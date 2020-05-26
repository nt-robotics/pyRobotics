import cv2

from pyrobotics.video.cameras.camera_base import Camera


class OpenCVCamera(Camera):

    def __init__(self, camera_index: int = -1):

        self.__camera_index = camera_index
        self.__video_capture = None
        self.__is_started = False

        super().__init__()

    def open(self) -> None:
        self.__video_capture = cv2.VideoCapture(self.__camera_index)

        if self.__video_capture is None or not self.__video_capture.isOpened():
            error_message = "Camera with index (" + str(self.__camera_index) + ") not found"
            print("[ERROR]", self.__class__.__name__, error_message)
            self._error_event.fire(error_message)

    def _loop(self) -> None:
        self.__is_started = True
        while self.__is_started:
            read, real_frame = self.__video_capture.read()
            if read:
                self._frame_change_event.fire(real_frame)

        self._stopped_event.fire()

    def stop(self):
        self.__is_started = False


class PylonCamera(Camera):

    def __init__(self):
        super().__init__()
