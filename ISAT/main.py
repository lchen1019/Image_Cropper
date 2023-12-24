# -*- coding: utf-8 -*-
# @Author  : LG
# import os

from PyQt5 import QtWidgets
from ISAT.widgets.mainwindow import MainWindow
import sys
import torch
torch.cuda.is_available()

def main():
    app = QtWidgets.QApplication([''])
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

