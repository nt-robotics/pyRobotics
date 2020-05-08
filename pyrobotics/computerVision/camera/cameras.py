from enum import Enum
from threading import Thread
from typing import Any, List, Callable, Tuple

import cv2
from pypylon import pylon
from pypylon.genicam import OutOfRangeException
from pypylon.genicam import RuntimeException

from pyrobotics.event import Event


class BaslerMultipleCamera(Thread):

    MAX_FRAME_WIDTH: int = 1280
    MAX_FRAME_HEIGHT: int = 960

    # Типы идентификатора камеры который будет отправляться при мене кадра,
    # для идентификации камеры с которой этот кадр пришел
    IDENTIFIER_TYPE_USER_ID: int = 0
    IDENTIFIER_TYPE_SERIAL_NUMBER: int = 1
    IDENTIFIER_TYPE_CAMERA_CONTEXT: int = 2

    @staticmethod
    def get_device_count() -> int:
        return len(pylon.TlFactory.GetInstance().EnumerateDevices())

    def __init__(self, cameras_count: int = None, frame_width: int = MAX_FRAME_WIDTH, frame_height: int = MAX_FRAME_HEIGHT):
        super().__init__()

        self.__camera_thread = None

        self.__change_frame_event = Event()
        self.__camera_start_event = Event()
        self.__camera_error_event = Event()

        self.__cameras_count = None

        devices_count = BaslerMultipleCamera.get_device_count()

        if devices_count < 1:
            mes = "No Basler devices found"
            raise OutOfRangeException(mes)

        if cameras_count > devices_count:
            print("Внимание!!! Количество запрашиваемых камер превышает количество подключенных устройств Basler")
            print("Запрашивается:   ", cameras_count)
            print("Подключено:      ", devices_count)

        if cameras_count is not None and cameras_count > 0:
            self.__cameras_count = min(devices_count, cameras_count)
        else:
            self.__cameras_count = devices_count

        self.__camera_identifier_type_to_send_on_frame_change = self.IDENTIFIER_TYPE_SERIAL_NUMBER

        tl_factory = pylon.TlFactory.GetInstance()
        device_list = tl_factory.EnumerateDevices()
        self.__cameras_list = pylon.InstantCameraArray(self.__cameras_count)

        for i, camera in enumerate(self.__cameras_list):
            camera.Attach(tl_factory.CreateDevice(device_list[i]))
            camera.Open()
            camera.Width.SetValue(frame_width)
            camera.Height.SetValue(frame_height)

            # camera.DeviceLinkThroughputLimit.SetValue(200000000)
            # camera.DeviceUserID.SetValue("CAMERA_" + str(i))

        self.__converter = pylon.ImageFormatConverter()
        self.__converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.__converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def set_identifier_type(self, value: int):
        self.__camera_identifier_type_to_send_on_frame_change = value

    def add_frame_change_handler(self, handler: Callable, camera_id_type: int = None):
        if camera_id_type is not None:
            self.set_identifier_type(camera_id_type)
        self.__change_frame_event.handle(handler)

    def add_error_handler(self, handler: Callable):
        self.__camera_error_event.handle(handler)

    def add_start_handler(self, handler: Callable):
        self.__camera_start_event.handle(handler)

    def get_cameras_count(self) -> int:
        return self.__cameras_count

    def get_width(self, index: int) -> int:
        camera = self.__cameras_list[index]
        return camera.Width.GetValue()

    def get_height(self, index: int) -> int:
        camera = self.__cameras_list[index]
        return camera.Height.GetValue()

    def get_frame_size(self, index: int) -> Tuple[int, int]:
        return self.get_width(index), self.get_height(index)

    def get_fps(self, camera_index: int = None) -> float or List[float]:
        if camera_index is not None and 0 <= camera_index < self.__cameras_count:
            camera = self.__cameras_list[camera_index]
            fps = camera.ResultingFrameRate.GetValue()
        else:
            fps = []
            for camera in self.__cameras_list:
                fps.append(camera.ResultingFrameRate.GetValue())
        return fps

    # Идентификатор установленный пользователем
    def get_user_id(self, index):
        camera = self.__cameras_list[index]
        return camera.DeviceUserID.GetValue()

    def get_user_ids(self) -> List[str]:
        names = []
        for camera in self.__cameras_list:
            names.append(camera.DeviceUserID.GetValue())
        return names

    # Серийный номер камеры
    def get_serial_number(self, index):
        camera = self.__cameras_list[index]
        return camera.DeviceSerialNumber.GetValue()

    def get_serial_numbers(self):
        numbers = []
        for camera in self.__cameras_list:
            numbers.append(camera.DeviceSerialNumber.GetValue())
        return numbers

    def run(self) -> None:

        self.__cameras_list.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        while self.__cameras_list.IsGrabbing():
            try:
                grab_result = self.__cameras_list.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

                camera_index = grab_result.GetCameraContext()
                camera_identifier = None

                if self.__camera_identifier_type_to_send_on_frame_change == self.IDENTIFIER_TYPE_CAMERA_CONTEXT:
                    camera_identifier = camera_index
                elif self.__camera_identifier_type_to_send_on_frame_change == self.IDENTIFIER_TYPE_SERIAL_NUMBER:
                    camera_identifier = self.get_serial_number(camera_index)
                elif self.__camera_identifier_type_to_send_on_frame_change == self.IDENTIFIER_TYPE_USER_ID:
                    camera_identifier = self.get_user_id(camera_index)

                if grab_result.GrabSucceeded():
                    # Access the image data
                    image = self.__converter.Convert(grab_result)
                    opencv_frame = image.GetArray()

                    self.__change_frame_event.fire(opencv_frame, camera_identifier)

            except RuntimeException:
                break

    def stop(self):
        self.__cameras_list.StopGrabbing()


class CameraType(Enum):
    BASLER = 100
    USB = 200
    CAMERA_DEFAULT = -1
    CAMERA_0 = 0
    CAMERA_1 = 1


class Camera(object):

    __DEFAULT_CAMERA_TYPE = CameraType.CAMERA_DEFAULT

    BASLER_CAMERA_FRAME_MIN_SIZE = (16, 8)
    BASLER_CAMERA_FRAME_MAX_SIZE = (1280, 960)

    def __init__(self, cam_type: CameraType = __DEFAULT_CAMERA_TYPE, index: int = None):

        self.__DEFAULT_BASLER_CAMERA_FRAME_SIZE = (600, 300)
        self.__DEFAULT_USB_CAMERA_FRAME_SIZE = (640, 480)

        self.__DEFAULT_OFFSET_X = (self.BASLER_CAMERA_FRAME_MAX_SIZE[0] - self.__DEFAULT_BASLER_CAMERA_FRAME_SIZE[0]) // 2
        self.__DEFAULT_OFFSET_Y = (self.BASLER_CAMERA_FRAME_MAX_SIZE[1] - self.__DEFAULT_BASLER_CAMERA_FRAME_SIZE[1]) // 2

        self.__camera_type = cam_type
        self.__index = index

        self.__frame_size = None
        self.__frame_offset_x = self.__DEFAULT_OFFSET_X
        self.__frame_offset_y = self.__DEFAULT_OFFSET_Y

        if self.__camera_type is CameraType.BASLER:
            self.__frame_size = list(self.__DEFAULT_BASLER_CAMERA_FRAME_SIZE)
        else:
            self.__frame_size = list(self.__DEFAULT_USB_CAMERA_FRAME_SIZE)

        # Thread and events
        self.__camera_thread = None
        self.__change_frame_event = Event()
        self.__camera_start_event = Event()
        self.__camera_error_event = Event()

    @staticmethod
    def get_basler_cameras_count() -> int:
        return len(pylon.TlFactory.GetInstance().EnumerateDevices())

    def start(self) -> None:
        self.__camera_thread = _CameraThread(self.__camera_type, self.__index, self.__frame_size, self.__change_frame_event, self.__camera_start_event, self.__camera_error_event)
        self.__camera_thread.set_frame_offset_x(self.__frame_offset_x)
        self.__camera_thread.set_frame_offset_y(self.__frame_offset_y)
        self.__camera_thread.start()

    def stop(self) -> None:
        if self.is_started():
            self.__camera_thread.stop_camera()
        self.__camera_thread = None

    def is_started(self) -> bool:
        return self.__camera_thread is not None and self.__camera_thread.is_started()

    # Camera type
    def set_camera_type(self, camera_type: CameraType) -> None:
        self.__camera_type = camera_type
        if self.__camera_type is CameraType.BASLER:
            self.__frame_size = list(self.__DEFAULT_BASLER_CAMERA_FRAME_SIZE)
        else:
            self.__frame_size = list(self.__DEFAULT_USB_CAMERA_FRAME_SIZE)

    def get_camera_type(self) -> CameraType:
        return self.__camera_type

    # Handlers
    def add_change_frame_handler(self, handler: Callable) -> None:
        self.__change_frame_event.handle(handler)

    def add_start_handler(self, handler: Callable) -> None:
        self.__camera_start_event.handle(handler)

    def add_error_handler(self, handler: Callable) -> None:
        self.__camera_error_event.handle(handler)

    # Frame settings
    def set_frame_width(self, value: int) -> None:
        self.__frame_size[0] = value

    def set_frame_height(self, value: int) -> None:
        self.__frame_size[1] = value

    def set_frame_offset_x(self, value: int) -> None:
        self.__frame_offset_x = value
        if self.is_started():
            self.__camera_thread.set_frame_offset_x(value)

    def set_frame_offset_y(self, value: int) -> None:
        self.__frame_offset_y = value
        if self.is_started():
            self.__camera_thread.set_frame_offset_y(value)

    def get_frame_width(self) -> int:
        return self.__frame_size[0]

    def get_frame_height(self) -> int:
        return self.__frame_size[1]

    def get_frame_offset_x(self) -> int:
        return self.__frame_offset_x

    def get_frame_offset_y(self) -> int:
        return self.__frame_offset_y


class _CameraThread(Thread):

    def __init__(self, camera_type: CameraType, camera_index: int, frame_size: List[int], change_frame_event: Event = None, camera_start_event: Event = None, camera_error_event: Event = None):
        super().__init__()

        self.__camera_type = camera_type
        self.__camera_index = camera_index
        self.__frame_size = frame_size
        self.__frame_offset_x = None
        self.__frame_offset_y = None

        self.__is_started = False
        self.__camera = None

        self.__change_frame_event = change_frame_event
        self.__camera_start_event = camera_start_event
        self.__camera_error_event = camera_error_event

    def is_started(self) -> bool:
        return self.__is_started

    def set_frame_offset_x(self, value: int) -> None:
        self.__frame_offset_x = value
        if self.__camera_type is CameraType.BASLER and self.__camera is not None:
            self.__camera.OffsetX = value

    def set_frame_offset_y(self, value: int) -> None:
        self.__frame_offset_y = value
        if self.__camera_type is CameraType.BASLER and self.__camera is not None:
            self.__camera.OffsetY = value

    def stop(self) -> None:
        self.__is_started = False

    def run(self) -> None:
        self.__is_started = True

        if self.__camera_type is CameraType.BASLER:
            self.__grab__basler(self.__camera_index)
        elif self.__camera_type is CameraType.USB:
            self.__grab_opencv(self.__camera_index)
        elif self.__camera_type is CameraType.CAMERA_0:
            self.__grab_opencv(0)
        elif self.__camera_type is CameraType.CAMERA_1:
            self.__grab_opencv(1)
        elif self.__camera_type is CameraType.CAMERA_DEFAULT:
            self.__grab_opencv(-1)

        self.__is_started = False

    def __dispatch_change_frame_event(self, frame: Any) -> None:
        if self.__change_frame_event is not None:
            self.__change_frame_event.fire(frame)

    def __dispatch_start_event(self) -> None:
        if self.__camera_start_event is not None:
            self.__camera_start_event.fire()

    def __dispatch_error_event(self, error_mes: str) -> None:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("CAMERA ERROR")
        print(error_mes)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        if self.__camera_error_event is not None:
            self.__camera_error_event.fire(error_mes)

    def __grab__basler(self, camera_index: int) -> None:
        # ====================
        # 1. Grab  with pylon
        # ====================
        try:
            if camera_index is not None:
                if camera_index < 0 or camera_index > Camera.get_basler_cameras_count() - 1:
                    error_mes = "Basler camera with index (" + str(camera_index) + ") not found"
                    self.__dispatch_error_event(error_mes)
                    return

                cameras_count = Camera.get_basler_cameras_count()

                tl_factory = pylon.TlFactory.GetInstance()
                devices = tl_factory.EnumerateDevices()
                cameras = pylon.InstantCameraArray(cameras_count)
                self.__camera = cameras[camera_index]
                self.__camera.Attach(tl_factory.CreateDevice(devices[camera_index]))
            else:
                device = pylon.TlFactory.GetInstance().CreateFirstDevice()
                self.__camera = pylon.InstantCamera(device)

            self.__camera.Open()
            self.__camera.Width = self.__frame_size[0]
            self.__camera.Height = self.__frame_size[1]
            self.__camera.OffsetX = self.__frame_offset_x
            self.__camera.OffsetY = self.__frame_offset_y

            # Grabbing Continusely (video) with minimal delay
            self.__camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            converter = pylon.ImageFormatConverter()

            self.__camera.ExposureTime = self.__camera.ExposureTime.Min

            # converting to opencv bgr format
            converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        except RuntimeException:
            error_mes = "Error. Basler camera not connected"
            self.__dispatch_error_event(error_mes)
            return

        except OutOfRangeException:
            error_mes = "Error. You have set the image size too large. " + str(self.__frame_size)
            self.__dispatch_error_event(error_mes)
            return

        self.__dispatch_start_event()

        while self.__is_started:

            grab_result = self.__camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grab_result.GrabSucceeded():

                # Access the image data
                image = converter.Convert(grab_result)
                real_frame = image.GetArray()
                self.__dispatch_change_frame_event(real_frame)

            grab_result.Release()

        self.__camera.StopGrabbing()
        self.__camera.Close()

    def __grab_opencv(self, camera_index: int) -> None:
        # ====================
        # 2. Grab with OpenCV
        # ====================
        if camera_index is None:
            camera_index = -1

        self.__camera = cv2.VideoCapture(camera_index)

        if self.__camera is None or not self.__camera.isOpened():
            self.__camera.release()
            error_message = "Camera with index (" + str(camera_index) + ") not found"
            self.__dispatch_error_event(error_message)
            return
        else:
            self.__dispatch_start_event()

        self.__camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.__frame_size[0])
        self.__camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.__frame_size[1])

        self.__is_started = True

        while self.__is_started:
            read, real_frame = self.__camera.read()
            if read:
                self.__dispatch_change_frame_event(real_frame)
        self.__camera.release()
