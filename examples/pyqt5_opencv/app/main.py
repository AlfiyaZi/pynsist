import os
import sys
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi

from camera import CameraDevice

UI_PATH = os.path.dirname(os.path.abspath(__file__))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = loadUi(os.path.join(UI_PATH, 'mainwindow.ui'), self)

        self.thread = QThread()

        self.camera = CameraDevice()
        self.camera.frame_ready.connect(self.update_video_label)

        self.ui.video.setMinimumSize(*self.camera.size)

        self.camera.moveToThread(self.thread)

    @pyqtSlot(QImage)
    def update_video_label(self, image):
        pixmap = QPixmap.fromImage(image)
        self.ui.video.setPixmap(pixmap)
        self.ui.video.update()


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
