import os
import sys
from threading import Thread
from typing import Callable

import cv2
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.uic import loadUi
from pypylon import pylon
from pypylon.genicam import OutOfRangeException


class Test:

    def __init__(self):

        app = QApplication(sys.argv)

        self.main_window = _MainWindow(self.close_window_handler)

        self.cameras = _BaslerMultipleCamera()
        self.cameras.add_frame_change_handler(self._change_frame_handler)
        self.cameras.start()

        self.main_window.show()

        sys.exit(app.exec_())

    def _change_frame_handler(self, frame, index):
        self.main_window.show_image(frame, index)
        # win_title = "Camera#" + str(index)
        # cv2.namedWindow(win_title, cv2.WINDOW_NORMAL)
        # cv2.imshow(win_title, frame)
        # k = cv2.waitKey(1)
        # if k == 27:
        #     self.cameras.stop()

    def _error_handler(self, mes):
        print(mes)

    def close_window_handler(self):
        self.cameras.stop()


class _BaslerMultipleCamera(Thread):

    @staticmethod
    def get_device_count() -> int:
        return len(pylon.TlFactory.GetInstance().EnumerateDevices())

    def __init__(self, cameras_count: int = None):
        super().__init__()

        self.__camera_thread = None

        self.__change_frame_event = _Event()
        self.__camera_start_event = _Event()
        self.__camera_error_event = _Event()

        self.__cameras_count = None

        devices_count = _BaslerMultipleCamera.get_device_count()

        if devices_count < 1:
            mes = "No Basler devices found"
            raise OutOfRangeException(mes)

        if cameras_count is not None and cameras_count > 0:
            self.__cameras_count = min(devices_count, cameras_count)
        else:
            self.__cameras_count = devices_count

        tl_factory = pylon.TlFactory.GetInstance()
        device_list = tl_factory.EnumerateDevices()
        self.__cameras_list = pylon.InstantCameraArray(self.__cameras_count)

        for i, camera in enumerate(self.__cameras_list):
            camera.Attach(tl_factory.CreateDevice(device_list[i]))
            camera.Open()

            camera.Width.SetValue(600)
            camera.Height.SetValue(300)

            camera.DeviceLinkThroughputLimit.SetValue(21000000)
            camera.DeviceUserID.SetValue("CAMERA_" + str(i))

        self.__converter = pylon.ImageFormatConverter()
        self.__converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.__converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def add_frame_change_handler(self, handler: Callable):
        self.__change_frame_event.handle(handler)

    def add_error_handler(self, handler: Callable):
        self.__camera_error_event.handle(handler)

    def add_start_handler(self, handler: Callable):
        self.__camera_start_event.handle(handler)

    def run(self) -> None:

        self.__cameras_list.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        while self.__cameras_list.IsGrabbing():

            grab_result = self.__cameras_list.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grab_result.GrabSucceeded():

                camera_context = grab_result.GetCameraContext()

                # Access the image data
                image = self.__converter.Convert(grab_result)
                opencv_frame = image.GetArray()
                self.__change_frame_event.fire(opencv_frame, camera_context)

    def stop(self):
        self.__cameras_list.StopGrabbing()


class _MainWindow(QWidget):

    # __GUI_PATH = "/home/user/Projects/pyCharm/pyRobotics/tests/pypylon/basler_camera_with_qt/gui/test_basler_with_qt_gui.ui"
    __GUI_PATH = os.getcwd() + "/gui/test_basler_with_qt_gui.ui"

    def __init__(self, close_window_handler):
        super().__init__()

        print(os.getcwd())

        loadUi(self.__GUI_PATH, self)
        # self.setWindowIcon(QIcon(self.__ICON_PATH))

        self.__close_window_handler = close_window_handler

    def show_image(self, image, index):
        qt_pixmap = QPixmap.fromImage(QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888))

        # screen_w = self.frameGeometry().width() - self.settings_panel.geometry().width() - 80
        # screen_h = self.frameGeometry().height() - 80
        #
        # qt_pixmap = qt_pixmap.scaled(screen_w, screen_h, QtCore.Qt.KeepAspectRatio)

        if index == 0:
            self.label.setPixmap(qt_pixmap)
        elif index == 1:
            self.label_2.setPixmap(qt_pixmap)

    def closeEvent(self, event):
        self.__close_window_handler()


class _Event(object):
    def __init__(self):
        self.__handlers = set()

    def handle(self, handler):
        self.__handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.__handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        for handler in self.__handlers:
            handler(*args, **kargs)

    def get_handlers_count(self):
        return len(self.__handlers)

    def clear_handlers(self):
        self.__handlers = []

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__ = get_handlers_count


if __name__ == '__main__':
    ttr = Test()
