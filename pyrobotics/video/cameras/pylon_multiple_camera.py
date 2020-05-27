from datetime import datetime
from enum import Enum
from threading import Thread
from time import sleep
from typing import Tuple

from pypylon import pylon
from pypylon.pylon import AccessException

from pyrobotics.event import Event


class PylonMultipleCamera(object):

    MIN_FRAME_SIZE = 16
    GAIN_MAX = 18.027804
    GAMMA_MIN = 0.25
    GAMMA_MAX = 2.0

    EXPOSURE_MIN = 10
    EXPOSURE_MAX = 1_000_000

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

    @classmethod
    def get_device_count(cls) -> int:
        return len(pylon.TlFactory.GetInstance().EnumerateDevices())

    def __init__(self, cameras_count: int = 0, is_trigger: bool = False, trigger_interval: float = 0.0):
        super().__init__()

        self.__grab_thread = None
        self.__cameras_list = None
        self.__trigger = None
        self.__is_trigger_mode = False
        self.__trigger_interval = trigger_interval
        self.__cameras_count = 0
        self.__grab_strategy = pylon.GrabStrategy_LatestImageOnly

        self.__converter = pylon.ImageFormatConverter()
        self.__converter.OutputPixelFormat = pylon.PixelType_RGB8packed
        self.__converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        self.__frame_change_event = Event()
        self.__grab_started_event = Event()
        self.__grab_stopped_event = Event()
        # self.__camera_opened_event = Event()
        # self.__camera_closed_event = Event()

        self.open(cameras_count)
        self.set_trigger_mode(is_trigger)

    def open(self, cameras_count: int = 0):
        tl_factory = pylon.TlFactory.GetInstance()
        devices_list = tl_factory.EnumerateDevices()
        devices_count = len(devices_list)

        if devices_count == 0:
            print("[PYLON CAMERA] Error. No cameras connected")
            return
            # raise ConnectionError("No cameras connected")

        if cameras_count == 0:
            cameras_count = devices_count

        if devices_count < cameras_count:
            print("[PYLON CAMERA] Error. Too few cameras connected. Need " + str(cameras_count))
            return
            # raise ConnectionError("Too few cameras connected. Need " + str(cameras_count))

        self.__cameras_count = cameras_count

        self.__cameras_list = pylon.InstantCameraArray(cameras_count)

        grab_handler = _GrabEventHandler(frame_change_event=self.__frame_change_event)
        configuration_handler = _ConfigurationEventHandler(grab_started_event=self.__grab_started_event,
                                                           grab_stopped_event=self.__grab_stopped_event)

        for cam_index, camera in enumerate(self.__cameras_list):

            # Add grab and configuration handlers
            camera.RegisterImageEventHandler(grab_handler, pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
            camera.RegisterConfiguration(configuration_handler, pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_Delete)

            camera.Attach(tl_factory.CreateDevice(devices_list[cam_index]))
            camera.Open()

            # Get camera parameter vars example
            # print(camera.PixelFormat.Symbolics)
            # print(camera.GainAuto.Symbolics)

            # Image parameters
            # camera.Width.SetValue(camera.SensorWidth.GetValue())
            # camera.Height.SetValue(camera.SensorHeight.GetValue())
            # camera.OffsetX.SetValue(0)
            # camera.OffsetY.SetValue(0)

            # Max num buffer
            # camera.MaxNumBuffer.SetValue(16)

            # Acquisition frame rate
            # camera.AcquisitionFrameRate.SetValue(100000)

            # Grab result pixel format
            # camera.PixelFormat.SetValue(self.PixelFormat.RGB8.value)
            # camera.PixelFormat.SetValue(self.PixelFormat.YCbCr422_8.value)
            # camera.PixelFormat.SetValue(self.PixelFormat.BayerGR8.value)
            # camera.PixelFormat.SetValue(self.PixelFormat.BayerGR12.value)  # Not supported for dart cameras

            # Exposure
            # camera.ExposureAuto.SetValue('Off')
            # camera.ExposureAuto.SetValue('Once')
            # camera.ExposureAuto.SetValue('Continuous')
            # camera.AutoExposureTimeLowerLimit.SetValue(100)
            # camera.AutoExposureTimeUpperLimit.SetValue(10000)
            # camera.ExposureTime.SetValue(3000)
            # White balance
            # camera.BalanceWhiteAuto.SetValue('Off')
            # Gain
            # camera.GainAuto.SetValue('Off')
            # Immediate Trigger mode
            # camera.BslImmediateTriggerMode.SetValue('On')

            # Trigger mode
            camera.TriggerMode.SetValue('Off')

            print()
            print("[PYLON CAMERA] ***********************  Init cameras ************************")
            print("Camera:" + str(cam_index), "(User ID:", camera.DeviceUserID.GetValue(), "| Model: ", camera.GetDeviceInfo().GetModelName(), "| Serial: ", camera.DeviceSerialNumber.GetValue(), ")")
            print("USB speed:", camera.BslUSBSpeedMode.GetValue())
            print("-----------------------------------------------------------------------------")

    # Image converter
    def convert(self, grab_result, output_pixel_format=None):
        if output_pixel_format is not None:
            self.__converter.OutputPixelFormat = output_pixel_format
        return self.__converter.Convert(grab_result).GetArray()

    # Control
    def start(self):
        if not self.__cameras_list.IsGrabbing():
            print("[PYLON CAMERA] Start grabbing video from", self.__cameras_count, "camera(s)")
            # print("[PYLON CAMERA] Grab strategy: ", self.__grab_strategy)
            print("[PYLON CAMERA] Grab strategy: ", PylonMultipleCamera.GrabStrategy(self.__grab_strategy).name)
            self.__cameras_list.StartGrabbing(self.__grab_strategy)

            self.set_trigger_mode(self.__is_trigger_mode)

            self.__grab_thread = _CameraGrabThread(self.__cameras_list)
            self.__grab_thread.start()

    def stop(self) -> None:
        self._stop_trigger()
        if self.__cameras_list is not None:
            self.__cameras_list.StopGrabbing()

    def close(self) -> None:
        self._stop_trigger()
        if self.__cameras_list is not None:
            self.__cameras_list.Close()

    def is_grabbing(self) -> bool:
        return self.__cameras_list.IsGrabbing()

    # Events
    def add_frame_change_handler(self, handler) -> None:
        self.__frame_change_event.handle(handler)

    def add_grab_started_handler(self, handler) -> None:
        self.__grab_started_event.handle(handler)

    def add_grab_stopped_handler(self, handler) -> None:
        self.__grab_stopped_event.handle(handler)

    # Trigger
    def set_trigger_interval(self, value: float):
        self.__trigger_interval = value
        if self.__trigger is not None:
            self.__trigger.set_interval(value)

    def set_trigger_mode(self, value: bool) -> None:
        if value and self.__trigger is None:
            self.__trigger = _SoftwareTrigger(self.__cameras_list, self.__trigger_interval)
        if value and self.__cameras_list.IsGrabbing():
            self.__trigger.start()
        if not value:
            self._stop_trigger()
        self.__is_trigger_mode = value

    def is_trigger_mode(self) -> bool:
        return self.__is_trigger_mode

    # Grab strategy
    def set_grab_strategy(self, strategy: GrabStrategy):
        self.__grab_strategy = strategy.value

    def get_grab_strategy(self) -> int:
        return self.__grab_strategy

    # FPS
    def get_fps(self, camera_index: int = 0) -> float:
        return self.__cameras_list[camera_index].ResultingFrameRate.GetValue()

    # Exposure time
    def get_exposure_auto(self, camera_index: int = 0) -> str:
        return self.__cameras_list[camera_index].ExposureAuto.GetValue()

    def get_exposure_auto_variants(self, camera_index: int = 0) -> Tuple[str]:
        return self.__cameras_list[camera_index].ExposureAuto.Symbolics

    def get_exposure_time(self, camera_index: int = 0) -> float:
        return self.__cameras_list[camera_index].ExposureTime.GetValue()

    def get_exposure_auto_lower_limit(self, camera_index: int = 0) -> float:
        return self.__cameras_list[camera_index].AutoExposureTimeLowerLimit.GetValue()

    def get_exposure_auto_upper_limit(self, camera_index: int = 0) -> float:
        return self.__cameras_list[camera_index].AutoExposureTimeUpperLimit.GetValue()

    def set_exposure_auto(self, value: str, camera_indices: Tuple[int] = ()):
        [camera.ExposureAuto.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    def set_exposure_time(self, value: float, camera_indices: Tuple[int] = ()):
        [camera.ExposureTime.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    def set_exposure_auto_lower_limit(self, value: float, camera_indices: Tuple[int] = ()):
        [camera.AutoExposureTimeLowerLimit.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    def set_exposure_auto_upper_limit(self, value: float, camera_indices: Tuple[int] = ()):
        [camera.AutoExposureTimeUpperLimit.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    # Frame size
    def get_width(self, camera_index: int = 0) -> int:
        return self.__cameras_list[camera_index].Width.GetValue()

    def get_height(self, camera_index: int = 0) -> int:
        return self.__cameras_list[camera_index].Height.GetValue()

    def get_max_width(self, camera_index: int = 0) -> int:
        return self.__cameras_list[camera_index].WidthMax.GetValue()

    def get_max_height(self, camera_index: int = 0) -> int:
        return self.__cameras_list[camera_index].HeightMax.GetValue()

    def set_width(self, value: int, camera_indices: Tuple[int] = ()):
        [camera.Width.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    def set_height(self, value: int, camera_indices: Tuple[int] = ()):
        [camera.Height.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    # Frame offsets
    def get_offset_x(self, camera_index: int = 0) -> int:
        return self.__cameras_list[camera_index].OffsetX.GetValue()

    def get_offset_y(self, camera_index: int = 0) -> int:
        return self.__cameras_list[camera_index].OffsetY.GetValue()

    def set_offset_x(self, value: int, camera_indices: Tuple[int] = ()):
        [camera.OffsetX.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    def set_offset_y(self, value: int, camera_indices: Tuple[int] = ()):
        [camera.OffsetY.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    # Pixel format
    def get_pixel_format(self, camera_index: int = 0) -> str:
        return self.__cameras_list[camera_index].PixelFormat.GetValue()

    def set_pixel_format(self, pixel_format: PixelFormat, camera_indices: Tuple[int] = ()) -> None:
        [camera.PixelFormat.SetValue(pixel_format.value) for camera in self.__get_cameras_by_indices(camera_indices)]

    # Gamma
    def get_gamma(self, camera_index: int = 0) -> float:
        return self.__cameras_list[camera_index].Gamma.GetValue()

    def set_gamma(self, value: str, camera_indices: Tuple[int] = ()) -> None:
        [camera.Gamma.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    # Gain
    def get_gain(self, camera_index: int = 0) -> float:
        return self.__cameras_list[camera_index].Gain.GetValue()

    def get_gain_auto_variants(self, camera_index: int = 0) -> Tuple[str]:
        return self.__cameras_list[camera_index].GainAuto.Symbolics

    def get_gain_auto(self, camera_index: int = 0) -> str:
        return self.__cameras_list[camera_index].GainAuto.GetValue()

    def get_gain_auto_lower_limit(self, camera_index: int = 0) -> float:
        return self.__cameras_list[camera_index].AutoGainLowerLimit.GetValue()

    def get_gain_auto_upper_limit(self, camera_index: int = 0) -> float:
        return self.__cameras_list[camera_index].AutoGainUpperLimit.GetValue()

    def set_gain(self, value: float, camera_indices: Tuple[int] = ()) -> None:
        [camera.Gain.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    def set_gain_auto(self, value: str, camera_indices: Tuple[int] = ()) -> None:
        [camera.GainAuto.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    def set_gain_auto_lower_limit(self, value: float, camera_indices: Tuple[int] = ()) -> None:
        [camera.AutoGainLowerLimit.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    def set_gain_auto_upper_limit(self, value: float, camera_indices: Tuple[int] = ()) -> None:
        [camera.AutoGainUpperLimit.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    # User id
    def get_user_id(self, camera_index: int = 0) -> str:
        return self.__cameras_list[camera_index].DeviceUserID.GetValue()

    # Serial
    def get_serial_number(self, camera_index: int = 0) -> int:
        return self.__cameras_list[camera_index].DeviceSerialNumber.GetValue()

    # Balance white
    def get_balance_white_auto_variants(self, camera_index: int = 0) -> Tuple[str]:
        return self.__cameras_list[camera_index].BalanceWhiteAuto.Symbolics

    def get_balance_white_auto(self, camera_index: int = 0) -> str:
        return self.__cameras_list[camera_index].BalanceWhiteAuto.GetValue()

    def set_balance_white_auto(self, value: str, camera_indices: Tuple[int] = ()) -> None:
        [camera.BalanceWhiteAuto.SetValue(value) for camera in self.__get_cameras_by_indices(camera_indices)]

    # #########
    # Private
    # ########

    def __get_cameras_by_indices(self, indices: Tuple[int]):
        if len(indices) == 0:
            indices = range(self.__cameras_count)
        cameras = [self.__cameras_list[index] for index in indices]
        return cameras

    def _stop_trigger(self):
        if self.__trigger is not None:
            self.__trigger.stop_camera()
            self.__trigger = None


class _CameraGrabThread(Thread):

    def __init__(self, cameras_list):
        super().__init__()
        self.__cameras_list = cameras_list

    def run(self) -> None:
        while self.__cameras_list.IsGrabbing():
            try:
                self.__cameras_list.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            except SystemError as e:
                print("[PYLON CAMERA] Grab thread error.", e)


class _SoftwareTrigger(Thread):

    def __init__(self, cameras_list, trigger_interval=0.0):
        super().__init__()
        self.__cameras = cameras_list
        self.__trigger_interval = trigger_interval
        self.__is_started = False

    # param value in milliseconds
    def set_interval(self, value: int) -> None:
        self.__trigger_interval = value

    def stop(self) -> None:
        for camera in self.__cameras:
            # AccessException
            try:
                # if camera.IsOpened():
                #     camera.TriggerMode.SetValue('Off')
                camera.TriggerMode.SetValue('Off')
            except AccessException:
                print("[PYLON CAMERA] camera.TriggerMode AccessException")

        self.__is_started = False

    def run(self) -> None:
        self.__is_started = True

        for camera in self.__cameras:
            camera.TriggerMode.SetValue('On')
            camera.AcquisitionMode.SetValue('Continuous')
            camera.TriggerSelector.SetValue('FrameStart')
            camera.TriggerSource.SetValue('Software')
            camera.TriggerActivation.SetValue('RisingEdge')
            # camera.TriggerActivation.SetValue('FallingEdge')

        while self.__is_started:
            for camera in self.__cameras:
                try:
                    camera.TriggerSoftware.Execute()
                except Exception:
                    print("[PYLON CAMERA] _SoftwareTrigger error")
            if self.__trigger_interval > 0.0:
                sleep(self.__trigger_interval/1000)


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

    def __init__(self, grab_started_event: Event, grab_stopped_event: Event):
        super().__init__()
        self.__grab_started_event = grab_started_event
        self.__grab_stopped_event = grab_stopped_event

    def OnAttach(self, camera):
        pass
        # print("OnAttach event")

    def OnAttached(self, camera):
        pass
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "attached")
        # print("[PYLON CAMERA] Camera", camera.DeviceUserID.GetValue(), "attached")

    def OnOpen(self, camera):
        pass

    def OnOpened(self, camera):
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "(", camera.DeviceUserID.GetValue(), ")", "opened")

    def OnGrabStart(self, camera):
        pass

    def OnGrabStarted(self, camera):
        self.__grab_started_event.fire(camera.DeviceSerialNumber.GetValue())

    def OnGrabStop(self, camera):
        pass

    def OnGrabStopped(self, camera):
        self.__grab_stopped_event.fire(camera.DeviceSerialNumber.GetValue())

    def OnClose(self, camera):
        pass

    def OnClosed(self, camera):
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "(", camera.DeviceUserID.GetValue(), ")", "closed")

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
