# -*- coding: utf-8 -*-
# @Author  : LG

from PyQt5 import QtWidgets, QtCore, QtGui
from ISAT.ui.MainWindow import Ui_MainWindow
from ISAT.widgets.files_dock_widget import FilesDockWidget
from ISAT.widgets.canvas import AnnotationScene, AnnotationView
from ISAT.configs import STATUSMode, MAPMode, load_config, save_config, CONFIG_FILE, DEFAULT_CONFIG_FILE, CHECKPOINT_PATH, ISAT_ROOT
from ISAT.annotation import Object, Annotation
from ISAT.widgets.polygon import Polygon, PromptPoint
from ISAT.widgets.converter_dialog import ConverterDialog
import os
import json
from PIL import Image
import functools
import imgviz
import ISAT.icons_rc
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import torch
import cv2  # 调整图像饱和度

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.image_root: str = None
        self.label_root:str = None

        self.files_list: list = []
        self.current_index = None
        self.current_file_index: int = None

        self.current_group = 1

        self.config_file = CONFIG_FILE if os.path.exists(CONFIG_FILE) else DEFAULT_CONFIG_FILE
        self.saved = True
        self.can_be_annotated = True
        self.load_finished = False

        self.png_palette = None # 图像拥有调色盘，说明是单通道的标注png文件
        self.instance_cmap = imgviz.label_colormap()
    
        # 标注目标
        self.current_label:Annotation = None

        # 新增 手动/自动 group选择
        self.group_select_mode = 'auto'

        # 所有labels
        self.rects = []

        self.is_show_bitmap = False
        
        self.init_ui()

        self.init_connect()
        self.reset_action()

    def init_ui(self):
        #q
        self.files_dock_widget = FilesDockWidget(mainwindow=self)
        self.files_dock.setWidget(self.files_dock_widget)

        # 新增 group 选择 快捷键
        self.next_group_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Tab"), self)
        self.prev_group_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("`"), self)
        self.next_group_shortcut.setContext(QtCore.Qt.ApplicationShortcut)
        self.prev_group_shortcut.setContext(QtCore.Qt.ApplicationShortcut)
       
        self.scene = AnnotationScene(mainwindow=self)

        self.view = AnnotationView(parent=self)
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)

        self.labelCoord = QtWidgets.QLabel('')
        self.labelCoord.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.labelCoord.setFixedWidth(150)
        self.statusbar.addPermanentWidget(self.labelCoord)

        self.labelData = QtWidgets.QLabel('')
        self.labelData.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.labelData.setFixedWidth(150)
        self.statusbar.addPermanentWidget(self.labelData)

        self.trans = QtCore.QTranslator()

        self.Converter_dialog = ConverterDialog(self, mainwindow=self)

    def set_saved_state(self, is_saved:bool):
        self.saved = is_saved
        if self.files_list is not None and self.current_index is not None:

            if is_saved:
                self.setWindowTitle(self.current_label.label_path)
            else:
                self.setWindowTitle('*{}'.format(self.current_label.label_path))

    def open_dir(self):
        dir = QtWidgets.QFileDialog.getExistingDirectory(self)
        if not dir:
            return

        self.files_list.clear()
        self.files_dock_widget.listWidget.clear()

        files = []
        suffixs = tuple(['{}'.format(fmt.data().decode('ascii').lower()) for fmt in QtGui.QImageReader.supportedImageFormats()])
        for f in os.listdir(dir):
            if f.lower().endswith(suffixs):
                # f = os.path.join(dir, f)
                files.append(f)
        files = sorted(files)
        self.files_list = files

        self.files_dock_widget.update_widget()

        self.current_index = 0

        self.image_root = dir
        self.actionOpen_dir.setStatusTip("Image root: {}".format(self.image_root))

        if self.label_root is None:
            self.label_root = dir
            self.actionSave_dir.setStatusTip("Label root: {}".format(self.label_root))

            # load setting yaml
            if os.path.exists(os.path.join(dir, 'isat.yaml')):
                self.config_file = os.path.join(dir, 'isat.yaml')

        self.show_image(self.current_index)

    def save_dir(self):
        dir = QtWidgets.QFileDialog.getExistingDirectory(self)
        if not dir:
            return

        self.label_root = dir
        self.actionSave_dir.setStatusTip("Label root: {}".format(self.label_root))
        # load setting yaml
        if os.path.exists(os.path.join(dir, 'isat.yaml')):
            self.config_file = os.path.join(dir, 'isat.yaml')
            self.reload_cfg()
        # 刷新图片
        if self.current_index is not None:
            self.show_image(self.current_index)

    def save(self):
        print('save')
        print(self.rects)

        save_name = self.files_list[self.current_index].split('.')[0] + '.json'
        save_path = os.path.join(self.label_root, save_name)
        # 保存json文件 self.rects
        print(save_path)
        with open(save_path, 'w') as file:
            json.dump(self.rects, file)

        # 保存所有的矩形
        if self.scene.mode != STATUSMode.VIEW:
            return
        if self.current_label is None:
            return
        print(self.rects)
        

    def show_image(self, index:int):
        self.reset_action()

        self.current_label = None
        self.load_finished = False
        self.saved = True
    
        try:
            # 加载image
            file_path = os.path.join(self.image_root, self.files_list[index])
            image_data = Image.open(file_path)
            self.png_palette = image_data.getpalette()
            self.scene.load_image(file_path)
            self.view.zoomfit()

            # 加载label
            file_path = os.path.join(self.label_root, self.files_list[index].split('.')[0] + '.json')
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    self.rects = json.load(file)
                    print(self.rects)
            else:
                self.rects = []
            self.is_show_bitmap = True
            self.scene.show_all()

            if self.current_label is not None:
                self.setWindowTitle('{}'.format(self.current_label.label_path))
            else:
                self.setWindowTitle('{}'.format(file_path))

            self.load_finished = True

        except Exception as e:
            print(e)
        finally:
            if self.current_index > 0:
                self.actionPrev.setEnabled(True)
            else:
                self.actionPrev.setEnabled(False)

            if self.current_index < len(self.files_list) - 1:
                self.actionNext.setEnabled(True)
            else:
                self.actionNext.setEnabled(False)
        
        self.actionPolygon.setEnabled(True)
        self.actionBit_map.setEnabled(True)
        self.actionDelete.setEnabled(True)

    def prev_image(self):
        if self.scene.mode != STATUSMode.VIEW:
            return
        if self.current_index is None:
            return
        if not self.saved:
            result = QtWidgets.QMessageBox.question(self, 'Warning', 'Proceed without saved?', QtWidgets.QMessageBox.StandardButton.Yes|QtWidgets.QMessageBox.StandardButton.No, QtWidgets.QMessageBox.StandardButton.No)
            if result == QtWidgets.QMessageBox.StandardButton.No:
                return
        self.current_index = self.current_index - 1
        if self.current_index < 0:
            self.current_index = 0
            QtWidgets.QMessageBox.warning(self, 'Warning', 'This is the first picture.')
        else:
            self.show_image(self.current_index)

    def next_image(self):
        if self.scene.mode != STATUSMode.VIEW:
            return
        if self.current_index is None:
            return
        if not self.saved:
            result = QtWidgets.QMessageBox.question(self, 'Warning', 'Proceed without saved?', QtWidgets.QMessageBox.StandardButton.Yes|QtWidgets.QMessageBox.StandardButton.No, QtWidgets.QMessageBox.StandardButton.No)
            if result == QtWidgets.QMessageBox.StandardButton.No:
                return
        self.current_index = self.current_index + 1
        if self.current_index > len(self.files_list)-1:
            self.current_index = len(self.files_list)-1
            QtWidgets.QMessageBox.warning(self, 'Warning', 'This is the last picture.')
        else:
            self.show_image(self.current_index)
        

    def jump_to(self):
        index = self.files_dock_widget.lineEdit_jump.text()
        if index:
            if not index.isdigit():
                if index in self.files_list:
                    index = self.files_list.index(index)+1
                else:
                    QtWidgets.QMessageBox.warning(self, 'Warning', 'Don`t exist image named: {}'.format(index))
                    self.files_dock_widget.lineEdit_jump.clear()
                    return
            index = int(index)-1
            if 0 <= index < len(self.files_list):
                self.show_image(index)
                self.files_dock_widget.lineEdit_jump.clear()
            else:
                QtWidgets.QMessageBox.warning(self, 'Warning', 'Index must be in [1, {}].'.format(len(self.files_list)))
                self.files_dock_widget.lineEdit_jump.clear()
                self.files_dock_widget.lineEdit_jump.clearFocus()
                return

    def cancel_draw(self):
        self.scene.cancel_draw()

    def setting(self):
        self.setting_dialog.load_cfg()
        self.setting_dialog.show()

    def model_manage(self):
        self.model_manager_dialog.show()

    def exit(self):
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.exit()

    def converter(self):
        self.Converter_dialog.show()
    
    def init_connect(self):
        self.actionOpen_dir.triggered.connect(self.open_dir)
        self.actionSave_dir.triggered.connect(self.save_dir)

        self.actionPrev.triggered.connect(self.prev_image)
        self.actionNext.triggered.connect(self.next_image)
        self.actionExit.triggered.connect(self.exit)

        self.actionPolygon.triggered.connect(self.scene.start_draw_polygon) # 绘制四边形
        self.actionFinish.triggered.connect(self.scene.finish_draw)
        self.actionDelete.triggered.connect(self.clear_all_rects)
        self.actionSave.triggered.connect(self.save)

        self.actionZoom_in.triggered.connect(self.view.zoom_in)
        self.actionZoom_out.triggered.connect(self.view.zoom_out)
        self.actionFit_wiondow.triggered.connect(self.view.zoomfit)

        # 转换格式
        self.actionConverter.triggered.connect(self.converter)

        # 预览结果
        self.actionBit_map.triggered.connect(self.change_bit_map)

    
    def clear_all_rects(self):
        self.rects = []
        self.scene.hide_all()

        file_path = os.path.join(self.label_root, self.files_list[self.current_index].split('.')[0] + '.json')
        if os.path.exists(file_path):
            os.remove(file_path)

    
    def change_bit_map(self):
        print('view bit map')
        if self.scene.mode == STATUSMode.CREATE:
            self.scene.cancel_draw()
        self.is_show_bitmap = not self.is_show_bitmap

        if self.is_show_bitmap:
            self.scene.show_all()
        else:
            self.scene.hide_all()

    def reset_action(self):
        self.actionPrev.setEnabled(False)
        self.actionNext.setEnabled(False)
        self.actionPolygon.setEnabled(False)
        self.actionEdit.setEnabled(False)
        self.actionDelete.setEnabled(False)
        self.actionSave.setEnabled(False)
        self.actionTo_top.setEnabled(False)
        self.actionTo_bottom.setEnabled(False)
        self.actionBit_map.setChecked(False)
        self.actionBit_map.setEnabled(False)