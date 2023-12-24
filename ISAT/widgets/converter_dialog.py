# -*- coding: utf-8 -*-
# @Author  : LG

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, QMessageBox
from ISAT.ui.Converter_dialog import Ui_Dialog
import os
import yaml
import json
import imgviz
from PIL import Image


class ConverterDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent, mainwindow):
        super(ConverterDialog, self).__init__(parent=parent)
        self.setWindowTitle('转换')
        self.layout = QVBoxLayout()
        self.mainwindow = mainwindow
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)

        self.path_layout = QHBoxLayout()
        self.button = QPushButton('保存至')
        self.button.clicked.connect(self.select_folder)
        self.path_layout.addWidget(self.button)
        self.path_text = QLineEdit()
        self.path_text.setReadOnly(True)
        self.path_layout.addWidget(self.path_text)
        self.layout.addLayout(self.path_layout)


        # 最底部居中按钮
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addStretch()
        self.bottom_button = QPushButton('转换')
        self.bottom_layout.addWidget(self.bottom_button)
        self.bottom_layout.addStretch()
        self.layout.addLayout(self.bottom_layout)
        self.bottom_button.clicked.connect(self.confirm_action)
        self.setLayout(self.layout)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '保存至')
        if folder:
            self.path_text.setText(folder)

    def confirm_action(self):
        path = self.path_text.text()
        if path == '':
            self.mainwindow.statusBar().showMessage('请先选择保存路径')
            QMessageBox.warning(self, '警告', '请先选择保存路径')
            return
        if not os.path.exists(path):
            os.makedirs(path)
        self.mainwindow.statusBar().showMessage('正在转换')
        labels_dir = self.mainwindow.label_root
        image_dir = self.mainwindow.image_root
        for inx, label in enumerate(os.listdir(labels_dir)):
            print(inx, label)
            label_path = os.path.join(labels_dir, label)
            image_path = os.path.join(image_dir, label[:-5] + '.jpg')
            if not os.path.exists(image_path):
                image_path = os.path.join(image_dir, label[:-5] + '.png')
            if not os.path.exists(image_path):
                image_path = os.path.join(image_dir, label[:-5] + '.jpeg')
            if not os.path.exists(image_path):
                continue
            image = Image.open(image_path)
            with open(label_path, 'r') as f:
                rects = json.load(f)
            
            for inx, rect in enumerate(rects):
                x1, y1, x2, y2 = rect['point1-x'], rect['point1-y'], rect['point2-x'], rect['point2-y']
                left = min(x1, x2)
                right = max(x1, x2)
                top = min(y1, y2)
                bottom = max(y1, y2)
                cropped_image = image.crop((left, top, right, bottom))
                save_path = os.path.join(path, label[:-5] + '_' + str(inx) + image_path[-4:])
                print(save_path)
                cropped_image.save(save_path)

        self.mainwindow.statusBar().showMessage('转换完成')
        QMessageBox.warning(self, '提示', '转换完成')
