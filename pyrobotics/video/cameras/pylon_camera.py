from datetime import datetime
from enum import Enum

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

    def __init__(self, auto_open: bool = True):

        self.__pylon_camera = pylon.InstantCamera()
        self.__grab_strategy = pylon.GrabStrategy_LatestImageOnly

        self.__converter = pylon.ImageFormatConverter()
        self.__converter.OutputPixelFormat = pylon.PixelType_RGB8packed
        self.__converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        super().__init__(auto_open=auto_open)

    # Control
    def open(self) -> None:

        grab_handler = _GrabEventHandler(frame_change_event=self._frame_change_event)
        configuration_handler = _ConfigurationEventHandler(camera=self, grab_started_event=self._started_event, grab_stopped_event=self._stopped_event)

        self.__pylon_camera.RegisterImageEventHandler(grab_handler, pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
        self.__pylon_camera.RegisterConfiguration(configuration_handler, pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_Delete)

        device = pylon.TlFactory.GetInstance().CreateFirstDevice()
        self.__pylon_camera.Attach(device)
        self.__pylon_camera.Open()

    #     !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.__pylon_camera.PixelFormat.SetValue("RGB8")
    #     !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    def start(self) -> None:
        self.__pylon_camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        super().start()

    def is_grabbing(self) -> bool:
        return self.__pylon_camera.IsGrabbing()

    def is_open(self) -> bool:
        return self.__pylon_camera.IsOpen()

    def _loop(self) -> None:
        while self.__pylon_camera.IsGrabbing():
            try:
                self.__pylon_camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            except SystemError:
                self._dispatch_error("Grab thread error")

    def stop(self) -> None:
        if self.is_grabbing():
            self.__pylon_camera.StopGrabbing()

    def close(self) -> None:
        super().close()
        self.__pylon_camera.Close()
        self.remove_all_handlers()

    # ###########################
    # Parameters
    # ###########################

    # _______________________________________________
    # Общие
    # _______________________________________________
    # ID
    def get_id(self) -> int:
        return self.get_serial_number()

    # Name
    def get_name(self) -> str:
        return "Model: " + self.get_model_name() + " Serial: " + str(self.get_serial_number()) + " User ID: " + self.get_user_id()

    # FPS
    def get_fps(self, camera_index: int = 0) -> float:
        return self.__pylon_camera[camera_index].ResultingFrameRate.GetValue()
    # _______________________________________________

    def get_user_id(self) -> str:
        return self.__pylon_camera.DeviceUserID.GetValue()

    def get_model_name(self) -> str:
        return self.__pylon_camera.GetDeviceInfo().GetModelName()

    def get_serial_number(self) -> int:
        return self.__pylon_camera.DeviceSerialNumber.GetValue()


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

    def __init__(self, camera: PylonCamera, grab_started_event: Event, grab_stopped_event: Event):
        super().__init__()
        self.__camera = camera
        self.__grab_started_event = grab_started_event
        self.__grab_stopped_event = grab_stopped_event

    def OnAttach(self, camera):
        pass
        # print("OnAttach event")

    def OnAttached(self, camera):
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "attached")

    def OnOpen(self, camera):
        pass

    def OnOpened(self, camera):
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "(", camera.DeviceUserID.GetValue(), ")", "opened")

    def OnGrabStart(self, camera):
        pass

    def OnGrabStarted(self, camera):
        self.__grab_started_event.fire(self.__camera)

    def OnGrabStop(self, camera):
        pass

    def OnGrabStopped(self, camera):
        # self.__grab_stopped_event.fire(camera.DeviceSerialNumber.GetValue())
        self.__grab_stopped_event.fire(self.__camera)

    def OnClose(self, camera):
        print("[PYLON CAMERA] Camera", camera.GetDeviceInfo().GetModelName(), "(", camera.DeviceUserID.GetValue(), ")", "close")

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
