import os

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi

from pyrobotics.event import Event
from pyrobotics.utils.time_utils import millis
from pyrobotics.video.cameras.pylon_camera import PylonCamera


'''

ERROR !!!

При скролле этого виджета приложение вылетает когда на экран появляется один из спинбоксов gain_spinbox, exposure_time_spinbox
если в __on_frame_change добавить:

# self.gain_spinbox.setValue(self.__camera.get_gain())
# self.exposure_time_spinbox.setValue(self.__camera.get_exposure_time())

, то же самое если в другом потоке

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Не вылетает в HarvesterVision в Windows
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

'''


class PylonCameraWidget(QWidget):

    """PylonCameraWidget pyQt виджет для управления камерами Basler"""

    __GUI_PATH = os.path.join(os.path.dirname(__file__), "ui", "pylon_camera_widget.ui")
    __UPDATE_ICON_PATH = os.path.join(os.path.dirname(__file__), "ui", "updateIcon.png")

    __UPDATE_DELAY = 500  # milliseconds

    def __init__(self):
        super().__init__()
        loadUi(self.__GUI_PATH, self)

        self.update_devices_bt.setIcon(QtGui.QIcon(self.__UPDATE_ICON_PATH))
        self.update_devices_bt.setIconSize(QtCore.QSize(16, 16))
        self.update_devices_auto_checkbox.setEnabled(False)

        self.settings_panel.hide()

        self.__camera = None
        self.__cameras_count = 0

        self.__cameras_count_change_event = Event()
        self.__camera_change_event = Event()

        self.__create_gui_event_handlers()
        self.__update_devices_list()

        # Update
        self.__last_update_time = millis()

    # #######################
    # Widget events
    # #######################

    def add_camera_change_handler(self, handler):
        self.__camera_change_event.handle(handler)

    def remove_camera_change_handler(self, handler):
        self.__camera_change_event.unhandle(handler)

    def add_cameras_count_change_handler(self, handler):
        self.__cameras_count_change_event.handle(handler)

    def remove_cameras_count_change_handler(self, handler):
        self.__cameras_count_change_event.unhandle(handler)

    # #######################
    # Control camera devices
    # #######################

    # def set_select_camera_enabled(self, value: bool):
    #     self.device_list_combobox.setEnabled(value)

    def get_cameras_count(self) -> int:
        return self.__cameras_count

    def get_camera(self) -> PylonCamera:
        return self.__camera

    def __set_camera(self, camera: PylonCamera) -> None:
        if self.__camera is not None and self.__camera.get_serial_number() == camera.get_serial_number():
            return
        self.__unset_camera()
        self.__camera = camera
        self.__camera.add_grab_started_handler(self.__on_camera_start_grabbing)
        self.__camera.add_grab_stopped_handler(self.__on_camera_stop_grabbing)
        self.__camera.add_frame_change_handler(self.__on_camera_frame_change)
        self.__camera.add_opened_handler(self.__on_camera_opened)
        self.__camera.add_closed_handler(self.__on_camera_closed)
        self.__camera.add_error_handler(self.__on_camera_error)
        if self.__camera.is_open():
            self.__show_settings()
        else:
            self.__hide_settings()

        self.__camera_change_event.fire(self.__camera)

    def __update_devices_list(self) -> None:

        cameras_count = self.__cameras_count

        model = QtGui.QStandardItemModel(0, 1)
        for index, camera in enumerate(PylonCamera.get_list()):
            camera: PylonCamera = camera
            device_name = camera.get_friendly_name()
            serial_number = camera.get_serial_number()
            item = QtGui.QStandardItem(device_name)
            item.setData(serial_number, QtCore.Qt.UserRole)

            # print(camera.get_friendly_name())
            # print("is_open_in_another_application:", camera.is_open_in_another_application())
            # print("is_open:", camera.is_open())
            # print("is_device_accessible:", camera.is_device_accessible())
            # print("is_device_removed:", camera.is_device_removed())
            # print("---------------------------")

            # Если камера открыта в другом приложении,
            # то не добавляем ее в список
            if not camera.is_open_in_another_application():
                model.appendRow(item)
                # item.setEnabled(False)

        self.device_list_combobox.blockSignals(True)
        self.device_list_combobox.setModel(model)

        self.__cameras_count = self.device_list_combobox.count()

        if self.__camera is not None:
            index = self.device_list_combobox.findData(self.__camera.get_serial_number())
            if index > -1:
                self.device_list_combobox.setCurrentIndex(index)
            else:
                self.__update_camera()
        else:
            self.__update_camera()
        self.device_list_combobox.blockSignals(False)

        # Если изменилось количество камер кидаем событие
        if self.__cameras_count != cameras_count:
            self.__cameras_count_change_event.fire(self.__cameras_count)

    def __update_camera(self) -> None:
        # Если подключена хотябя одна камера
        if self.device_list_combobox.count() > 0:
            selected_serial = self.device_list_combobox.currentData()
            self.open_device_bt.setEnabled(True)
            self.device_list_combobox.setEnabled(True)
            self.__set_camera(PylonCamera.get_camera_by_serial(selected_serial))
        else:
            self.device_list_combobox.addItem("No cameras available")
            self.open_device_bt.setText("Open")
            self.open_device_bt.setEnabled(False)
            self.device_list_combobox.setEnabled(False)
            self.settings_panel.hide()
            self.__unset_camera()

    def __unset_camera(self) -> None:
        if self.__camera is not None:
            self.__camera.remove_grab_started_handler(self.__on_camera_start_grabbing)
            self.__camera.remove_grab_stopped_handler(self.__on_camera_stop_grabbing)
            self.__camera.remove_frame_change_handler(self.__on_camera_frame_change)
            self.__camera.remove_opened_handler(self.__on_camera_opened)
            self.__camera.remove_closed_handler(self.__on_camera_closed)
            self.__camera.remove_error_handler(self.__on_camera_error)
            self.__camera = None

    def __show_settings(self) -> None:
        self.__set_camera_settings()
        self.settings_panel.show()
        self.open_device_bt.setText("Close")

    def __hide_settings(self) -> None:
        self.settings_panel.hide()
        self.open_device_bt.setText("Open")

    def __set_camera_settings(self) -> None:
        # Block widget signals
        self.grab_strategy_combobox.blockSignals(True)
        self.frame_width_spinbox.blockSignals(True)
        self.frame_height_spinbox.blockSignals(True)
        self.frame_offset_x_spinbox.blockSignals(True)
        self.frame_offset_y_spinbox.blockSignals(True)
        self.gain_auto_combobox.blockSignals(True)
        self.gain_upper_limit_spinbox.blockSignals(True)
        self.gain_lower_limit_spinbox.blockSignals(True)
        self.gain_spinbox.blockSignals(True)
        self.gamma_spinbox.blockSignals(True)
        self.exposure_auto_combobox.blockSignals(True)
        self.exposure_upper_limit_spinbox.blockSignals(True)
        self.exposure_lower_limit_spinbox.blockSignals(True)
        self.exposure_time_spinbox.blockSignals(True)
        self.pixel_format_combobox.blockSignals(True)
        self.balance_white_auto_combobox.blockSignals(True)

        # Grab strategy
        self.grab_strategy_combobox.clear()
        self.grab_strategy_combobox.addItems(self.__camera.GrabStrategy.get_names())
        garb_strategy_name = PylonCamera.GrabStrategy(self.__camera.get_grab_strategy()).name
        index = self.grab_strategy_combobox.findText(garb_strategy_name, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.grab_strategy_combobox.setCurrentIndex(index)

        # fps
        self.fps_label.setText("0.00")

        # Frame size
        self.frame_width_spinbox.setRange(self.__camera.MIN_FRAME_SIZE, self.__camera.get_max_width())
        self.frame_width_spinbox.setValue(self.__camera.get_width())
        self.frame_height_spinbox.setRange(self.__camera.MIN_FRAME_SIZE, self.__camera.get_max_height())
        self.frame_height_spinbox.setValue(self.__camera.get_height())

        # Offsets
        self.frame_offset_x_spinbox.setRange(0, self.__camera.get_max_width() - self.__camera.get_width())
        self.frame_offset_x_spinbox.setValue(self.__camera.get_offset_x())
        self.frame_offset_y_spinbox.setRange(0, self.__camera.get_max_height() - self.__camera.get_height())
        self.frame_offset_y_spinbox.setValue(self.__camera.get_offset_y())

        # Gain
        self.gain_auto_combobox.clear()
        self.gain_auto_combobox.addItems(self.__camera.get_gain_auto_variants())
        gain_auto_value = self.__camera.get_gain_auto()
        index = self.gain_auto_combobox.findText(gain_auto_value, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.gain_auto_combobox.setCurrentIndex(index)

        self.gain_upper_limit_spinbox.setRange(0, self.__camera.GAIN_MAX)
        self.gain_upper_limit_spinbox.setValue(self.__camera.get_gain_auto_upper_limit())

        self.gain_lower_limit_spinbox.setRange(0, self.__camera.get_gain_auto_upper_limit())
        self.gain_lower_limit_spinbox.setValue(self.__camera.get_gain_auto_lower_limit())

        self.gain_spinbox.setRange(0, self.__camera.GAIN_MAX)
        self.gain_spinbox.setValue(self.__camera.get_gain())

        # Gamma
        self.gamma_spinbox.setRange(self.__camera.GAMMA_MIN, self.__camera.GAMMA_MAX)
        self.gamma_spinbox.setValue(self.__camera.get_gamma())

        # Exposure time
        self.exposure_auto_combobox.clear()
        self.exposure_auto_combobox.addItems(self.__camera.get_exposure_auto_variants())
        exposure_auto_value = self.__camera.get_exposure_auto()
        index = self.exposure_auto_combobox.findText(exposure_auto_value, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.exposure_auto_combobox.setCurrentIndex(index)

        self.exposure_upper_limit_spinbox.setRange(self.__camera.EXPOSURE_MIN, self.__camera.EXPOSURE_MAX)
        self.exposure_upper_limit_spinbox.setValue(self.__camera.get_exposure_auto_upper_limit())

        self.exposure_lower_limit_spinbox.setRange(self.__camera.EXPOSURE_MIN,
                                                   self.__camera.get_exposure_auto_upper_limit())
        self.exposure_lower_limit_spinbox.setValue(self.__camera.get_exposure_auto_lower_limit())

        self.exposure_time_spinbox.setRange(self.__camera.EXPOSURE_MIN, self.__camera.EXPOSURE_MAX)
        self.exposure_time_spinbox.setValue(self.__camera.get_exposure_time())

        # Pixel format
        self.pixel_format_combobox.clear()
        self.pixel_format_combobox.addItems(self.__camera.PixelFormat.get_names())
        pixel_format_value = self.__camera.get_pixel_format()
        index = self.pixel_format_combobox.findText(pixel_format_value, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.pixel_format_combobox.setCurrentIndex(index)

        # Balance white
        self.balance_white_auto_combobox.clear()
        self.balance_white_auto_combobox.addItems(self.__camera.get_balance_white_auto_variants())
        balance_white_value = self.__camera.get_balance_white_auto()
        index = self.balance_white_auto_combobox.findText(balance_white_value, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.balance_white_auto_combobox.setCurrentIndex(index)

        # UnBlock signals
        self.grab_strategy_combobox.blockSignals(False)
        self.frame_width_spinbox.blockSignals(False)
        self.frame_height_spinbox.blockSignals(False)
        self.frame_offset_x_spinbox.blockSignals(False)
        self.frame_offset_y_spinbox.blockSignals(False)
        self.gain_auto_combobox.blockSignals(False)
        self.gain_upper_limit_spinbox.blockSignals(False)
        self.gain_lower_limit_spinbox.blockSignals(False)
        self.gain_spinbox.blockSignals(False)
        self.gamma_spinbox.blockSignals(False)
        self.exposure_auto_combobox.blockSignals(False)
        self.exposure_upper_limit_spinbox.blockSignals(False)
        self.exposure_lower_limit_spinbox.blockSignals(False)
        self.exposure_time_spinbox.blockSignals(False)
        self.pixel_format_combobox.blockSignals(False)
        self.balance_white_auto_combobox.blockSignals(False)

    # Вызывается один раз при создании
    def __create_gui_event_handlers(self) -> None:
        # Devices
        self.update_devices_bt.clicked.connect(self.__on_update_devices_list_but_click)
        self.open_device_bt.clicked.connect(self.__on_open_device_bt_click)
        self.device_list_combobox.currentIndexChanged[int].connect(self.__on_selected_device_change)
        # Grab strategy
        self.grab_strategy_combobox.currentIndexChanged['QString'].connect(self.__on_grab_strategy_change)
        # Frame size
        self.frame_width_spinbox.valueChanged.connect(self.__frame_width_change)
        self.frame_height_spinbox.valueChanged.connect(self.__frame_height_change)
        # Offsets
        self.frame_offset_x_spinbox.valueChanged.connect(self.__frame_offset_x_change)
        self.frame_offset_y_spinbox.valueChanged.connect(self.__frame_offset_y_change)
        # Gain
        self.gain_auto_combobox.currentIndexChanged['QString'].connect(self.__on_gain_auto_change)
        self.gain_upper_limit_spinbox.valueChanged.connect(self.__on_gain_upper_limit_change)
        self.gain_lower_limit_spinbox.valueChanged.connect(self.__on_gain_lower_limit_change)
        self.gain_spinbox.valueChanged.connect(self.__on_gain_change)
        # Gamma
        self.gamma_spinbox.valueChanged.connect(self.__on_gamma_spinbox_change)
        # Exposure time
        self.exposure_auto_combobox.currentIndexChanged['QString'].connect(self.__on_exposure_auto_change)
        self.exposure_upper_limit_spinbox.valueChanged.connect(self.__on_exposure_upper_limit_change)
        self.exposure_lower_limit_spinbox.valueChanged.connect(self.__on_exposure_lower_limit_change)
        self.exposure_time_spinbox.valueChanged.connect(self.__on_exposure_change)
        # Pixel format
        self.pixel_format_combobox.currentIndexChanged['QString'].connect(self.__on_pixel_format_change)
        # Balance white
        self.balance_white_auto_combobox.currentIndexChanged['QString'].connect(self.__on_balance_white_auto_change)

    # ##########
    # GUI events
    # ##########

    # Devices control
    def __on_selected_device_change(self, _index):
        self.__update_camera()

    def __on_open_device_bt_click(self):
        if self.__camera.is_open():
            self.__camera.close()
        else:
            self.__camera.open()

    def __on_update_devices_list_but_click(self):
        self.__update_devices_list()

    # Grab strategy
    def __on_grab_strategy_change(self, value):
        self.__camera.set_grab_strategy(self.__camera.GrabStrategy.get_by_name(value))

    # Pixel format
    def __on_pixel_format_change(self, value):
        pixel_format = self.__camera.PixelFormat.get_by_name(value)
        self.__camera.set_pixel_format(pixel_format)

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

    # #############
    # Camera events
    # #############

    def __on_camera_opened(self, _camera: PylonCamera):
        self.__show_settings()

    def __on_camera_closed(self, _camera: PylonCamera):
        self.__hide_settings()

    def __on_camera_frame_change(self, _grab_result, _camera_serial, _frame_time):
        now = millis()
        if now - self.__last_update_time >= self.__UPDATE_DELAY:
            # Если раскомментировать следующие две строчки вылетает приложение при скроле этого виджета
            # (Не вылетает в HarvesterVision в Windows)
            # ===================================================================
            self.gain_spinbox.setValue(self.__camera.get_gain())
            self.exposure_time_spinbox.setValue(self.__camera.get_exposure_time())
            # ===================================================================
            self.fps_label.setText("{:.2f}".format(self.__camera.get_fps()))
            self.__last_update_time = now

    def __on_camera_start_grabbing(self, _camera):
        self.grab_strategy_combobox.setEnabled(False)
        self.frame_width_spinbox.setEnabled(False)
        self.frame_height_spinbox.setEnabled(False)
        self.pixel_format_combobox.setEnabled(False)

    def __on_camera_stop_grabbing(self, _camera):
        self.grab_strategy_combobox.setEnabled(True)
        self.frame_width_spinbox.setEnabled(True)
        self.frame_height_spinbox.setEnabled(True)
        self.pixel_format_combobox.setEnabled(True)
        self.fps_label.setText("0.00")

    @staticmethod
    def __on_camera_error(message):
        print("CAMERA ERROR")
        print(message)
        # self.__unset_camera()
        # self.__update_devices_list()
