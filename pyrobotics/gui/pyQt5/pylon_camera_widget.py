import os

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi

from pyrobotics.computerVision.camera.pylon_cameras import PylonMultipleCamera


class PylonCameraWidget(QWidget):

    __GUI_PATH = os.path.join(os.path.dirname(__file__), "ui", "pylon_camera_widget.ui")

    def __init__(self, camera: PylonMultipleCamera):
        super().__init__()
        loadUi(self.__GUI_PATH, self)

        self.__camera = camera

        self.camera_name_label.setText("ID: " + self.__camera.get_user_id() + " (S/N:" + str(self.__camera.get_serial_number()) + ")")

        # Grab strategy
        self.grab_strategy_combobox.addItems(self.__camera.GrabStrategy.get_names())
        garb_strategy_name = PylonMultipleCamera.GrabStrategy(self.__camera.get_grab_strategy()).name
        index = self.grab_strategy_combobox.findText(garb_strategy_name, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.grab_strategy_combobox.setCurrentIndex(index)
        self.grab_strategy_combobox.currentIndexChanged['QString'].connect(self.__on_grab_strategy_change)

        # fps
        self.fps_label.setText("0.00")

        # frame size
        self.frame_width_spinbox.setRange(self.__camera.MIN_FRAME_SIZE, self.__camera.get_max_width())
        self.frame_width_spinbox.setValue(self.__camera.get_width())
        self.frame_width_spinbox.valueChanged.connect(self.__frame_width_change)
        self.frame_height_spinbox.setRange(self.__camera.MIN_FRAME_SIZE, self.__camera.get_max_height())
        self.frame_height_spinbox.setValue(self.__camera.get_height())
        self.frame_height_spinbox.valueChanged.connect(self.__frame_height_change)

        # Offsets
        self.frame_offset_x_spinbox.setRange(0, self.__camera.get_max_width() - self.__camera.get_width())
        self.frame_offset_x_spinbox.setValue(self.__camera.get_offset_x())
        self.frame_offset_x_spinbox.valueChanged.connect(self.__frame_offset_x_change)
        self.frame_offset_y_spinbox.setRange(0, self.__camera.get_max_height() - self.__camera.get_height())
        self.frame_offset_y_spinbox.setValue(self.__camera.get_offset_y())
        self.frame_offset_y_spinbox.valueChanged.connect(self.__frame_offset_y_change)

        # Gain
        self.gain_auto_combobox.addItems(self.__camera.get_gain_auto_variants())
        gain_auto_value = self.__camera.get_gain_auto()
        index = self.gain_auto_combobox.findText(gain_auto_value, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.gain_auto_combobox.setCurrentIndex(index)
        self.gain_auto_combobox.currentIndexChanged['QString'].connect(self.__on_gain_auto_change)

        self.gain_upper_limit_spinbox.setRange(0, self.__camera.GAIN_MAX)
        self.gain_upper_limit_spinbox.setValue(self.__camera.get_gain_auto_upper_limit())
        self.gain_upper_limit_spinbox.valueChanged.connect(self.__on_gain_upper_limit_change)

        self.gain_lower_limit_spinbox.setRange(0, self.__camera.get_gain_auto_upper_limit())
        self.gain_lower_limit_spinbox.setValue(self.__camera.get_gain_auto_lower_limit())
        self.gain_lower_limit_spinbox.valueChanged.connect(self.__on_gain_lower_limit_change)

        self.gain_spinbox.setRange(0, self.__camera.GAIN_MAX)
        self.gain_spinbox.setValue(self.__camera.get_gain())
        self.gain_spinbox.valueChanged.connect(self.__on_gain_change)

        # Gamma
        self.gamma_spinbox.setRange(self.__camera.GAMMA_MIN, self.__camera.GAMMA_MAX)
        self.gamma_spinbox.setValue(self.__camera.get_gamma())
        self.gamma_spinbox.valueChanged.connect(self.__on_gamma_spinbox_change)

        # Exposure time
        self.exposure_auto_combobox.addItems(self.__camera.get_exposure_auto_variants())
        exposure_auto_value = self.__camera.get_exposure_auto()
        index = self.exposure_auto_combobox.findText(exposure_auto_value, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.exposure_auto_combobox.setCurrentIndex(index)
        self.exposure_auto_combobox.currentIndexChanged['QString'].connect(self.__on_exposure_auto_change)

        self.exposure_upper_limit_spinbox.setRange(self.__camera.EXPOSURE_MIN, self.__camera.EXPOSURE_MAX)
        self.exposure_upper_limit_spinbox.setValue(self.__camera.get_exposure_auto_upper_limit())
        self.exposure_upper_limit_spinbox.valueChanged.connect(self.__on_exposure_upper_limit_change)

        self.exposure_lower_limit_spinbox.setRange(self.__camera.EXPOSURE_MIN, self.__camera.get_exposure_auto_upper_limit())
        self.exposure_lower_limit_spinbox.setValue(self.__camera.get_exposure_auto_lower_limit())
        self.exposure_lower_limit_spinbox.valueChanged.connect(self.__on_exposure_lower_limit_change)

        self.exposure_time_spinbox.setRange(self.__camera.EXPOSURE_MIN, self.__camera.EXPOSURE_MAX)
        self.exposure_time_spinbox.setValue(self.__camera.get_exposure_time())
        self.exposure_time_spinbox.valueChanged.connect(self.__on_exposure_change)

        # Pixel format
        self.pixel_format_combobox.addItems(self.__camera.PixelFormat.get_names())
        pixel_format_value = self.__camera.get_pixel_format()
        index = self.pixel_format_combobox.findText(pixel_format_value, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.pixel_format_combobox.setCurrentIndex(index)
        self.pixel_format_combobox.currentIndexChanged['QString'].connect(self.__on_pixel_format_change)

        # Balance white
        self.balance_white_auto_combobox.addItems(self.__camera.get_balance_white_auto_variants())
        balance_white_value = self.__camera.get_balance_white_auto()
        index = self.balance_white_auto_combobox.findText(balance_white_value, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.balance_white_auto_combobox.setCurrentIndex(index)
        self.balance_white_auto_combobox.currentIndexChanged['QString'].connect(self.__on_balance_white_auto_change)

        # Camera events
        self.__camera.add_grab_started_handler(self.__on_camera_start_grabbing)
        self.__camera.add_grab_stopped_handler(self.__on_camera_stop_grabbing)
        self.__camera.add_frame_change_handler(self.__on_camera_frame_change)

    # ##########
    # GUI events
    # ##########

    # Grab strategy
    def __on_grab_strategy_change(self, value):
        self.__camera.set_grab_strategy(self.__camera.GrabStrategy.get_by_name(value))

    # Pixel format
    def __on_pixel_format_change(self, value):
        self.__camera.set_pixel_format(value)

    # Frame size
    def __frame_width_change(self):
        value = self.frame_width_spinbox.value()
        self.frame_offset_x_spinbox.setRange(0, self.__camera.get_max_width() - value)
        self.__camera.set_width(value)

    def __frame_height_change(self):
        value = self.frame_height_spinbox.value()
        self.frame_offset_y_spinbox.setRange(0, self.__camera.get_max_height() - value)
        self.__camera.set_height(value)

    def __frame_offset_x_change(self):
        self.__camera.set_offset_x(self.frame_offset_x_spinbox.value())

    def __frame_offset_y_change(self):
        self.__camera.set_offset_y(self.frame_offset_y_spinbox.value())

    # Gain
    def __on_gain_change(self):
        self.__camera.set_gain(self.gain_spinbox.value())

    def __on_gain_auto_change(self, value):
        self.__camera.set_gain_auto(value)

    def __on_gain_lower_limit_change(self):
        upper_limit_value = self.gain_upper_limit_spinbox.value()
        lower_limit_value = self.gain_lower_limit_spinbox.value()
        if lower_limit_value >= upper_limit_value:
            return
        self.__camera.set_gain_auto_lower_limit(lower_limit_value)

    def __on_gain_upper_limit_change(self):
        upper_limit_value = self.gain_upper_limit_spinbox.value()
        self.gain_lower_limit_spinbox.setRange(0, upper_limit_value)
        self.__camera.set_gain_auto_upper_limit(upper_limit_value)

    # Gamma
    def __on_gamma_spinbox_change(self):
        self.__camera.set_gamma(self.gamma_spinbox.value())

    # Exposure
    def __on_exposure_change(self):
        self.__camera.set_exposure_time(self.exposure_time_spinbox.value())

    def __on_exposure_auto_change(self, value):
        self.__camera.set_exposure_auto(value)

    def __on_exposure_lower_limit_change(self):
        upper_limit_value = self.exposure_upper_limit_spinbox.value()
        lower_limit_value = self.exposure_lower_limit_spinbox.value()
        if lower_limit_value >= upper_limit_value:
            return
        self.__camera.set_exposure_auto_lower_limit(lower_limit_value)

    def __on_exposure_upper_limit_change(self):
        upper_limit_value = self.exposure_upper_limit_spinbox.value()
        self.exposure_lower_limit_spinbox.setRange(self.__camera.EXPOSURE_MIN, upper_limit_value)
        self.__camera.set_exposure_auto_upper_limit(upper_limit_value)

    # Balance white
    def __on_balance_white_auto_change(self, value):
        self.__camera.set_balance_white_auto(value)
    #     balance_white_auto_combobox

    # #############
    # Camera events
    # #############

    def __on_camera_frame_change(self, _grab_result, _camera_serial, _frame_time):
        self.gain_spinbox.setValue(self.__camera.get_gain())
        self.exposure_time_spinbox.setValue(self.__camera.get_exposure_time())
        self.fps_label.setText("{:.2f}".format(self.__camera.get_fps()))

    def __on_camera_start_grabbing(self, _camera_serial):
        self.grab_strategy_combobox.setEnabled(False)
        self.frame_width_spinbox.setEnabled(False)
        self.frame_height_spinbox.setEnabled(False)
        self.pixel_format_combobox.setEnabled(False)

    def __on_camera_stop_grabbing(self, _camera_serial):
        self.grab_strategy_combobox.setEnabled(True)
        self.frame_width_spinbox.setEnabled(True)
        self.frame_height_spinbox.setEnabled(True)
        self.pixel_format_combobox.setEnabled(True)
        self.fps_label.setText("0.00")
