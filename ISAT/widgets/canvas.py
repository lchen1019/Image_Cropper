# -*- coding: utf-8 -*-
# @Author  : LG

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem
from ISAT.widgets.polygon import Polygon, Vertex, PromptPoint
from ISAT.configs import STATUSMode, CLICKMode, DRAWMode, CONTOURMode
from PIL import Image
import numpy as np
import cv2
import time # 拖动鼠标描点

class AnnotationScene(QtWidgets.QGraphicsScene):
    def __init__(self, mainwindow):
        super(AnnotationScene, self).__init__()
        self.mainwindow = mainwindow
        self.image_item:QtWidgets.QGraphicsPixmapItem = None
        self.image_data = None
        self.current_graph:QGraphicsRectItem = None
        self.mode = STATUSMode.VIEW
        self.click = CLICKMode.POSITIVE
        self.click_points = []

        self.mask_alpha = 0.5
        self.top_layer = 1

        self.guide_line_x:QtWidgets.QGraphicsLineItem = None
        self.guide_line_y:QtWidgets.QGraphicsLineItem = None

        # 拖动鼠标描点     
        self.last_draw_time = time.time()
        self.draw_interval = 0.15
        self.pressd = False

    def load_image(self, image_path:str):
        self.clear()

        self.image_data = np.array(Image.open(image_path))
                
        self.image_item = QtWidgets.QGraphicsPixmapItem()
        self.image_item.setZValue(0)
        self.addItem(self.image_item)
        self.image_item.setPixmap(QtGui.QPixmap(image_path))
        self.setSceneRect(self.image_item.boundingRect())
    
    def start_draw_polygon(self):
        if self.mode != STATUSMode.VIEW:
            return
        self.change_mode_to_create()
        if self.mode == STATUSMode.CREATE:
            self.start_draw()
    
    def start_draw(self):
        print('start_draw')
        self.current_graph = QGraphicsRectItem()
        self.addItem(self.current_graph)
    
    def change_mode_to_view(self):
        self.mode = STATUSMode.VIEW
        self.image_item.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        self.mainwindow.actionPrev.setEnabled(True)
        self.mainwindow.actionNext.setEnabled(True)

        self.mainwindow.actionPolygon.setEnabled(self.mainwindow.can_be_annotated)
        self.mainwindow.actionBackspace.setEnabled(False)
        self.mainwindow.actionFinish.setEnabled(False)
        self.mainwindow.actionCancel.setEnabled(False)

        self.mainwindow.actionEdit.setEnabled(False)
        self.mainwindow.actionDelete.setEnabled(False)
        self.mainwindow.actionSave.setEnabled(self.mainwindow.can_be_annotated)

    def change_mode_to_create(self):
        if self.image_item is None:
            return
        self.mode = STATUSMode.CREATE
        self.image_item.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))
        self.mainwindow.actionPrev.setEnabled(False)
        self.mainwindow.actionNext.setEnabled(False)

        self.mainwindow.actionPolygon.setEnabled(False)
        self.mainwindow.actionBackspace.setEnabled(True)
        self.mainwindow.actionFinish.setEnabled(True)
        self.mainwindow.actionCancel.setEnabled(True)

        self.mainwindow.actionEdit.setEnabled(False)
        self.mainwindow.actionDelete.setEnabled(False)
        self.mainwindow.actionSave.setEnabled(False)

    def finish_draw(self):
        print('finish_draw')
        print(self.click_points)

        if self.current_graph is None:
            self.click_points.clear()
            return
        
        # 保存当前矩形
        print(self.click_points)
        print(self.mainwindow.rects)
        rect = {
            "point1-x": self.click_points[0][0],
            "point1-y": self.click_points[0][1],
            "point2-x": self.click_points[1][0],
            "point2-y": self.click_points[1][1],
        }
        print(rect)
        self.mainwindow.rects.append(rect)

        # 删除当前绘制对象
        self.click_points.clear()
        self.removeItem(self.current_graph)
        self.current_graph = None

        self.change_mode_to_view()


    def cancel_draw(self):
        if self.current_graph is None:
            return
        self.removeItem(self.current_graph)
        self.current_graph = None
        self.change_mode_to_view()
        self.click_points.clear()
       

    def mousePressEvent(self, event: 'QtWidgets.QGraphicsSceneMouseEvent'):
        if self.mode == STATUSMode.VIEW:
            return
        sceneX, sceneY = event.scenePos().x(), event.scenePos().y()
        sceneX = 0 if sceneX < 0 else sceneX
        sceneX = self.width()-1 if sceneX > self.width()-1 else sceneX
        sceneY = 0 if sceneY < 0 else sceneY
        sceneY = self.height()-1 if sceneY > self.height()-1 else sceneY
        print(sceneX, sceneY)

        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            print('left click')
            self.pressd = True

            if len(self.click_points) <= 2:
                self.click_points.append([sceneX, sceneY])

            if len(self.click_points) == 2:
                pen = QPen(Qt.red)
                pen.setWidth(5)
                brush = QBrush(QColor(255, 255, 255, 128))

                p1 = self.click_points[0]
                p2 = self.click_points[1]
                self.current_graph.setPen(pen)
                self.current_graph.setBrush(brush)
                self.current_graph.setRect(p1[0], p1[1], p2[0]-p1[0], p2[1]-p1[1])
        super(AnnotationScene, self).mousePressEvent(event)

    # 拖动鼠标描点 
    def mouseReleaseEvent(self, event: 'QtWidgets.QGraphicsSceneMouseEvent'):       
        self.pressd = False
        super(AnnotationScene, self).mouseReleaseEvent(event)
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.GraphicsSceneMouseMove and event.buttons() == Qt.LeftButton:
            self.mouseMoveEvent(event)
            return True
        return super(RectangleScene, self).eventFilter(obj, event)

    def mouseMoveEvent(self, event: 'QtWidgets.QGraphicsSceneMouseEvent'):
        # 拖动鼠标描点
        pos = event.scenePos()
        if pos.x() < 0: pos.setX(0)
        if pos.x() > self.width()-1: pos.setX(self.width()-1)
        if pos.y() < 0: pos.setY(0)
        if pos.y() > self.height()-1: pos.setY(self.height()-1)

        if len(self.click_points) == 1:
            pen = QPen(Qt.red)
            pen.setWidth(5)
            brush = QBrush(QColor(255, 255, 255, 128))

            p1 = self.click_points[0]
            p2 = [pos.x(), pos.y()]
            self.current_graph.setPen(pen)
            self.current_graph.setBrush(brush)
            self.current_graph.setRect(p1[0], p1[1], p2[0]-p1[0], p2[1]-p1[1])
        else:
            return

        # 状态栏,显示当前坐标
        if self.image_data is not None:
            x, y = round(pos.x()), round(pos.y())
            self.mainwindow.labelCoord.setText('xy: ({:>4d},{:>4d})'.format(x, y))

            data = self.image_data[y][x]
            if self.image_data.ndim == 2:
                self.mainwindow.labelData.setText('pix: [{:^3d}]'.format(data))
            elif self.image_data.ndim == 3:
                if len(data) == 3:
                    self.mainwindow.labelData.setText('rgb: [{:>3d},{:>3d},{:>3d}]'.format(data[0], data[1], data[2]))
                else:
                    self.mainwindow.labelData.setText('pix: [{}]'.format(data))

        super(AnnotationScene, self).mouseMoveEvent(event)
    
    def show_all(self):
        print('show_all')

        pen = QPen(Qt.red)
        pen.setWidth(5)
        brush = QBrush(QColor(255, 255, 255, 128))

        for rect in self.mainwindow.rects:
            self.current_graph = QGraphicsRectItem()
            self.addItem(self.current_graph)
            p1 = [rect["point1-x"], rect["point1-y"]]
            p2 = [rect["point2-x"], rect["point2-y"]]
            self.current_graph.setPen(pen)
            self.current_graph.setBrush(brush)
            self.current_graph.setRect(p1[0], p1[1], p2[0]-p1[0], p2[1]-p1[1])

    def hide_all(self):
        print('hide_all')
        items_to_remove = [item for item in self.items() if isinstance(item, QGraphicsRectItem)]
        for item in items_to_remove:
            self.removeItem(item)

class AnnotationView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(AnnotationView, self).__init__(parent)
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.factor = 1.2

    def wheelEvent(self, event: QtGui.QWheelEvent):
        angel = event.angleDelta()
        angelX, angelY = angel.x(), angel.y()
        point = event.pos() # 当前鼠标位置
        if angelY > 0:
            self.zoom(self.factor, point)
        else:
            self.zoom(1 / self.factor, point)

    def zoom_in(self):
        self.zoom(self.factor)

    def zoom_out(self):
        self.zoom(1/self.factor)

    def zoomfit(self):
        self.fitInView(0, 0, self.scene().width(), self.scene().height(),  QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def zoom(self, factor, point=None):
        mouse_old = self.mapToScene(point) if point is not None else None
        # 缩放比例

        pix_widget = self.transform().scale(factor, factor).mapRect(QtCore.QRectF(0, 0, 1, 1)).width()
        if pix_widget > 30 and factor > 1: return
        if pix_widget < 0.01 and factor < 1: return

        self.scale(factor, factor)
        if point is not None:
            mouse_now = self.mapToScene(point)
            center_now = self.mapToScene(self.viewport().width() // 2, self.viewport().height() // 2)
            center_new = mouse_old - mouse_now + center_now
            self.centerOn(center_new)
