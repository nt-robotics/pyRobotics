from datetime import datetime
from enum import Enum
from typing import Tuple

from pypylon import pylon

from pyrobotics.event import Event
from pyrobotics.video.cameras.camera_base import Camera


class PylonCamera(Camera):

    MIN_FRAME_SIZE = 16
    GAIN_MAX = 18.027804
    GAMMA_MIN = 0.25
    GAMMA_MAX = 2.0

    EXPOSURE_MIN = 10
    EXPOSURE_MAX = 1_000_000

    __tl_factory = pylon.TlFactory.GetInstance()
    # Список доступных камер, обновляется методом '__update_list'
    __cameras_list = []

    # Image converter
    __converter = pylon.ImageFormatConverter()
    __converter.OutputPixelFormat = pylon.PixelType_RGB8packed
    __converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    class GrabStrategy(Enum):
        ONE_BY_ONE = pylon.GrabStrategy_OneByOne
        LATEST_IMAGE_ONLY = pylon.GrabStrategy_LatestImageOnly
        LATEST_IMAGES = pylon.GrabStrategy_LatestImages
        # UPCOMING_IMAGE = pylon.GrabStrategy_UpcomingImage # for GigE only

        @classmethod
        def get_names(cls):
            return [strategy.name for strategy in cls]

        @classmethod
        def get_by_name(cls, name):
            return cls[name]

    class PixelFormat(Enum):
        RGB8 = "RGB8"
        YCbCr422_8 = "YCbCr422_8"
        BayerGR8 = "BayerGR8"
        BayerGR12 = "BayerGR12"

        @classmethod
        def get_names(cls):
            return [pix_format.name for pix_format in cls]

        @classmethod
        def get_by_name(cls, name):
            return cls[name]

    # Convert image format
    @classmethod
    def convert(cls, grab_result, output_pixel_format=None):
        if output_pixel_format is not None:
            cls.__converter.OutputPixelFormat = output_pixel_format
        return cls.__converter.Convert(grab_result).GetArray()

    @classmethod
    def get_list(cls) -> []:
        cls.__update_list()
        return cls.__cameras_list

    @classmethod
    def get_device_count(cls) -> int:
        return len(cls.__tl_factory.EnumerateDevices())

    @classmethod
    def get_accessible_device_count(cls) -> int:
        accessible_device_count = 0
        devices_list = cls.__tl_factory.EnumerateDevices()
        for device in devices_list:
            if cls.__tl_factory.IsDeviceAccessible(device):
                accessible_device_count += 1
        return accessible_device_count

    @classmethod
    def get_first_accessible_camera(cls):
        if cls.get_accessible_device_count() == 0:
            raise ConnectionError("No cameras available. Connected: " + str(cls.get_device_count()) + " Accessible: 0")
        devices_info_list = cls.__tl_factory.EnumerateDevices()
        for device_info in devices_info_list:
            if cls.__tl_factory.IsDeviceAccessible(device_info):
                return PylonCamera(device_info.GetSerialNumber())
        return None

    @classmethod
    def __update_list(cls):
        if len(cls.__cameras_list) == cls.get_device_count():
            return
        devices_list = cls.__tl_factory.EnumerateDevices()
        for device_info in devices_list:
            device_serial = device_info.GetSerialNumber()
            if not cls.__is_camera_exist(device_serial):
                PylonCamera(device_serial)

    @classmethod
    def __get_device_info_by_serial_number(cls, serial: str):
        devices_info_list = cls.__tl_factory.EnumerateDevices()
        for device_info in devices_info_list:
            if device_info.GetSerialNumber() == serial:
                return device_info
        return None

    @classmethod
    def __is_camera_exist(cls, serial) -> bool:
        for camera in cls.__cameras_list:
            camera_serial = camera.get_serial_number()
            if camera_serial == serial:
                return True
        return False

    def __new__(cls, serial_number: str = None):
        if serial_number is None:
            return PylonCamera.get_first_accessible_camera()

        for camera in PylonCamera.__cameras_list:
            camera_serial = camera.get_serial_number()
            if camera_serial == serial_number:
                return camera
        return super(PylonCamera, cls).__new__(cls)

    def __init__(self, serial_number: str = None):
        if serial_number is None or PylonCamera.__is_camera_exist(serial_number):
            return
        self.__camera_device_info = self.__get_device_info_by_serial_number(serial_number)
        if self.__camera_device_info is None:
            raise ConnectionError("Camera with serial number (" + serial_number + ") not connect")

        super().__init__(Camera.Type.PYLON)

        PylonCamera.__cameras_list.append(self)

        # Флаг показывающий что камера была открыта именно в этой программе, а не в другом клиенте
        self.__is_opened_here = False
        self.__pylon_camera = pylon.InstantCamera()

        self.__grab_strategy = None
        self.set_grab_strategy(PylonCamera.GrabStrategy.LATEST_IMAGE_ONLY)

        grab_handler = _GrabEventHandler(frame_change_event=self._frame_change_event)
        configuration_handler = _ConfigurationEventHandler(camera=self, grab_started_event=self._started_event, grab_stopped_event=self._stopped_event, camera_opened_event=self._opened_event)

        self.__pylon_camera.RegisterImageEventHandler(grab_handler, pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
        self.__pylon_camera.RegisterConfiguration(configuration_handler, pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_Delete)

        if not self.is_device_accessible():
            # raise ConnectionError("Camera with serial number (" + serial_number + ") used in another application")
            print("[WARNING] Camera (S/N:", serial_number, ") used in another application")
            return

        camera_device = PylonCamera.__tl_factory.CreateDevice(self.__camera_device_info)
        self.__pylon_camera.Attach(camera_device)

    # Control
    def open(self) -> None:
        self.__is_opened_here = True
        self.__pylon_camera.Open()

    def start(self) -> None:
        if not self.is_open():
            self.open()
        print("[PYLON CAMERA] Start grabbing. Grab strategy: ", PylonCamera.GrabStrategy(self.__grab_strategy).name)
        self.__pylon_camera.StartGrabbing(self.__grab_strategy)
        super().start()

    def is_grabbing(self) -> bool:
        return self.__pylon_camera.IsGrabbing()

    def is_open(self) -> bool:
        return self.__pylon_camera.IsOpen()

    def is_attach(self) -> bool:
        return self.__pylon_camera.IsPylonDeviceAttached()

    # Не работает, всегда False
    # def is_device_removed(self) -> bool:
    #     return self.__pylon_camera.IsCameraDeviceRemoved()

    def is_open_in_another_application(self):
        return not self.is_device_accessible() and not self.__is_opened_here

    def _loop(self) -> None:
        while self.__pylon_camera.IsGrabbing():
            try:
                self.__pylon_camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            except SystemError:
                print("Grab thread error")

    def stop(self) -> None:
        if self.is_grabbing():
            print("[PYLON CAMERA] Stop grabbing")
            self.__pylon_camera.StopGrabbing()

    def close(self) -> None:
        super().close()
        self.__pylon_camera.Close()
        self.remove_all_handlers()
        PylonCamera.__cameras_list.remove(self)

    # ###########################
    # Parameters
    # ###########################

    # _______________________________________________
    # Общие для всех типов камер(Pylon, OpenCV)
    # _______________________________________________

    # ID
    def get_id(self) -> str:
        return self.get_serial_number()

    # Name
    def get_name(self) -> str:
        return "<Pylon camera>. Model: " + self.get_model_name() + ", Serial: " + str(self.get_serial_number()) + ", User ID: " + self.get_user_id()

    # FPS
    def get_fps(self) -> float:
        return self.__pylon_camera.ResultingFrameRate.GetValue()
    # _______________________________________________

    # _______________________________________________
    # Параметры устройства
    # _______________________________________________

    # print("GetSerialNumber: ", device.GetSerialNumber())
    # print("GetUserDefinedName: ", device.GetUserDefinedName())
    # print("GetModelName: ", device.GetModelName())
    # print("GetInterfaceID: ", device.GetInterfaceID())
    # print("GetFriendlyName: ", device.GetFriendlyName())
    # print("GetFullName: ", device.GetFullName())
    # print("GetVendorName: ", device.GetVendorName())
    # print("GetDeviceClass: ", device.GetDeviceClass())
    # print("GetManufacturerInfo: ", device.GetManufacturerInfo())
    # print("GetProductId: ", device.GetProductId())
    # print("GetXMLSource: ", device.GetXMLSource())
    # print("GetAddress: ", device.GetAddress())
    # print("GetInterface: ", device.GetInterface())
    # print("GetInitialBaudRate: ", device.GetInitialBaudRate())
    # print("GetDeviceVersion: ", device.GetDeviceVersion())

    # device_info["serial_number"] = device.GetSerialNumber()
    # device_info["user_defined_name"] = device.GetUserDefinedName()
    # device_info["model_name"] = device.GetModelName()
    # device_info["friendly_name"] = device.GetFriendlyName()
    # device_info["full_name"] = device.GetFullName()
    # device_info["vendor_name"] = device.GetVendorName()
    # device_info["device_class"] = device.GetDeviceClass()
    # device_info["is_accessible"] = tl_factory.IsDeviceAccessible(device)

    # Is device accessible
    def is_device_accessible(self) -> bool:
        return PylonCamera.__tl_factory.IsDeviceAccessible(self.__camera_device_info)

    # User ID
    def get_user_id(self) -> str:
        return self.__camera_device_info.GetUserDefinedName()

    def set_user_id(self, user_id: str) -> None:
        self.__camera_device_info.SetUserDefinedName(user_id)

    # Model name
    def get_model_name(self) -> str:
        return self.__camera_device_info.GetModelName()

    # Serial number
    def get_serial_number(self) -> str:
        return self.__camera_device_info.GetSerialNumber()

    # Friendly name
    def get_friendly_name(self) -> str:
        return self.__camera_device_info.GetFriendlyName()

    # _______________________________________________

    # Pixel format
    def get_pixel_format(self) -> str:
        return self.__pylon_camera.PixelFormat.GetValue()

    def set_pixel_format(self, pixel_format: PixelFormat) -> None:
        self.__pylon_camera.PixelFormat.SetValue(pixel_format.value)

    # Grab strategy
    def set_grab_strategy(self, strategy: GrabStrategy) -> None:
        self.__grab_strategy = strategy.value

    def get_grab_strategy(self) -> int:
        return self.__grab_strategy

    # Frame size
    def get_width(self) -> int:
        return self.__pylon_camera.Width.GetValue()

    def get_height(self) -> int:
        return self.__pylon_camera.Height.GetValue()

    def get_max_width(self) -> int:
        return self.__pylon_camera.WidthMax.GetValue()

    def get_max_height(self) -> int:
        return self.__pylon_camera.HeightMax.GetValue()

    def set_width(self, value: int) -> None:
        self.__pylon_camera.Width.SetValue(value)

    def set_height(self, value: int) -> None:
        self.__pylon_camera.Height.SetValue(value)

    # Frame offsets
    def get_offset_x(self) -> int:
        return self.__pylon_camera.OffsetX.GetValue()

    def get_offset_y(self) -> int:
        return self.__pylon_camera.OffsetY.GetValue()

    def set_offset_x(self, value: int) -> None:
        self.__pylon_camera.OffsetX.SetValue(value)

    def set_offset_y(self, value: int) -> None:
        self.__pylon_camera.OffsetY.SetValue(value)

    # Exposure time
    def get_exposure_auto(self) -> str:
        return self.__pylon_camera.ExposureAuto.GetValue()

    def get_exposure_auto_variants(self) -> Tuple[str]:
        return self.__pylon_camera.ExposureAuto.Symbolics

    def get_exposure_time(self) -> float:
        return self.__pylon_camera.ExposureTime.GetValue()

    def get_exposure_auto_lower_limit(self) -> float:
        return self.__pylon_camera.AutoExposureTimeLowerLimit.GetValue()

    def get_exposure_auto_upper_limit(self) -> float:
        return self.__pylon_camera.AutoExposureTimeUpperLimit.GetValue()

    def set_exposure_auto(self, value: str) -> None:
        self.__pylon_camera.ExposureAuto.SetValue(value)

    def set_exposure_time(self, value: float) -> None:
        self.__pylon_camera.ExposureTime.SetValue(value)

    def set_exposure_auto_lower_limit(self, value: float) -> None:
        self.__pylon_camera.AutoExposureTimeLowerLimit.SetValue(value)

    def set_exposure_auto_upper_limit(self, value: float) -> None:
        self.__pylon_camera.AutoExposureTimeUpperLimit.SetValue(value)

    # Gamma
    def get_gamma(self) -> float:
        return self.__pylon_camera.Gamma.GetValue()

    def set_gamma(self, value: str) -> None:
        self.__pylon_camera.Gamma.SetValue(value)

    # Gain
    def get_gain(self) -> float:
        return self.__pylon_camera.Gain.GetValue()

    def get_gain_auto_variants(self) -> Tuple[str]:
        return self.__pylon_camera.GainAuto.Symbolics

    def get_gain_auto(self) -> str:
        return self.__pylon_camera.GainAuto.GetValue()

    def get_gain_auto_lower_limit(self) -> float:
        return self.__pylon_camera.AutoGainLowerLimit.GetValue()

    def get_gain_auto_upper_limit(self) -> float:
        return self.__pylon_camera.AutoGainUpperLimit.GetValue()

    def set_gain(self, value: float) -> None:
        self.__pylon_camera.Gain.SetValue(value)

    def set_gain_auto(self, value: str) -> None:
        self.__pylon_camera.GainAuto.SetValue(value)

    def set_gain_auto_lower_limit(self, value: float) -> None:
        self.__pylon_camera.AutoGainLowerLimit.SetValue(value)

    def set_gain_auto_upper_limit(self, value: float) -> None:
        self.__pylon_camera.AutoGainUpperLimit.SetValue(value)

    # Balance white
    def get_balance_white_auto_variants(self) -> Tuple[str]:
        return self.__pylon_camera.BalanceWhiteAuto.Symbolics

    def get_balance_white_auto(self) -> str:
        return self.__pylon_camera.BalanceWhiteAuto.GetValue()

    def set_balance_white_auto(self, value: str) -> None:
        self.__pylon_camera.BalanceWhiteAuto.SetValue(value)


class _GrabEventHandler(pylon.ImageEventHandler):

    def __init__(self, frame_change_event: Event):
        super().__init__()

        self.__frame_change_event = frame_change_event

    def OnImagesSkipped(self, camera, count_of_skipped_images):
        pass
        # print("Camera ID: ", camera.DeviceUserID.GetValue(), count_of_skipped_images, "images have been skipped.")

    def OnImageGrabbed(self, camera, grab_result):
        # print("Camera #", grab_result.GetCameraContext(), camera.DeviceUserID.GetValue(), "(", camera.GetDeviceInfo().GetModelName(), ")")
        # print("Serial number: ", camera.DeviceSerialNumber.GetValue())
        # print("FPS: ", camera.ResultingFrameRate.GetValue())
        # print("---------------------------------------------------------------")
        # print(grab_result.GetArray().shape)
        # print(grab_result.GetArray()[0][0])
        # serial = camera.DeviceSerialNumber.GetValue()

        if grab_result.GrabSucceeded():
            time = datetime.now()
            self.__frame_change_event.fire(grab_result, camera.DeviceSerialNumber.GetValue(), time)
        else:
            print("[PYLON CAMERA] Grab Error: ", grab_result.ErrorCode, grab_result.ErrorDescription)


class _ConfigurationEventHandler(pylon.ConfigurationEventHandler):

    def __init__(self, camera: PylonCamera, grab_started_event: Event, grab_stopped_event: Event, camera_opened_event: Event):
        super().__init__()
        self.__camera = camera
        self.__camera_opened_event = camera_opened_event
        self.__grab_started_event = grab_started_event
        self.__grab_stopped_event = grab_stopped_event

    def OnAttach(self, camera):
        pass

    def OnAttached(self, camera):
        print("[PYLON CAMERA] Camera attached", self.__camera)

    def OnOpen(self, camera):
        pass

    def OnOpened(self, camera):
        print("[PYLON CAMERA] Camera opened", self.__camera)
        self.__camera_opened_event.fire(self.__camera)

    def OnGrabStart(self, camera):
        pass

    def OnGrabStarted(self, camera):
        self.__grab_started_event.fire(self.__camera)

    def OnGrabStop(self, camera):
        pass

    def OnGrabStopped(self, camera):
        self.__grab_stopped_event.fire(self.__camera)

    def OnClose(self, camera):
        print("[PYLON CAMERA] Camera close", self.__camera)

    def OnClosed(self, camera):
        print("[PYLON CAMERA] Camera closed")

    def OnDestroy(self, camera):
        pass

    def OnDestroyed(self, camera):
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "(", camera.DeviceUserID.GetValue(), ")", "destroyed")

    def OnDetach(self, camera):
        pass

    def OnDetached(self, camera):
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "(", camera.DeviceUserID.GetValue(), ")", "detached")

    def OnGrabError(self, camera, error_message):
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "(", camera.DeviceUserID.GetValue(), ")", "grab error")
        print("Error message: ", error_message)

    def OnCameraDeviceRemoved(self, camera):
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "(", camera.DeviceUserID.GetValue(), ")", "device removed")
