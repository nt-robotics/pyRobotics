from enum import Enum

import cv2

from pyrobotics.video.cameras.camera_base import Camera


class OpenCVCamera(Camera):

    class PixelFormat(Enum):
        RGB = "RGB"
        BGR = "BGR"

        @classmethod
        def get_names(cls):
            return [pix_format.name for pix_format in cls]

        @classmethod
        def get_by_name(cls, name):
            return cls[name]

    @classmethod
    def get_device_count(cls) -> int:
        max_tested = 100
        for i in range(max_tested):
            temp_camera = cv2.VideoCapture(i)
            if temp_camera is not None and temp_camera.isOpened():
                temp_camera.release()
                continue
            return i

    def __init__(self, camera_index: int = -1, pixel_format: PixelFormat = PixelFormat.BGR):

        self.__camera_index = camera_index
        self.__video_capture = None
        self.__is_grabbing = False

        self.__pixel_format = pixel_format

        super().__init__()

    # Control
    def open(self) -> None:
        self.__video_capture = cv2.VideoCapture(self.__camera_index)

        if self.__video_capture is None or not self.__video_capture.isOpened():
            error_message = "Camera with index (" + str(self.__camera_index) + ") not found"
            self._dispatch_error(error_message)
            self._error_event.fire(error_message)
            return

    def is_open(self) -> bool:
        return self.__video_capture.isOpened()

    def is_grabbing(self) -> bool:
        return self.__is_grabbing

    def _loop(self) -> None:
        self.__is_grabbing = True
        self._started_event.fire(self)
        while self.__is_grabbing:
            read, frame = self.__video_capture.read()
            if read:
                if self.__pixel_format == OpenCVCamera.PixelFormat.RGB:
                    frame = self.bgr2rgb(frame)
                self._frame_change_event.fire(frame)

        self._stopped_event.fire(self)
        self.__is_grabbing = False

    def stop(self):
        self.__is_grabbing = False

    def close(self) -> None:
        super().close()
        self.__video_capture.release()
        self.remove_all_handlers()

    # ###########################
    # Parameters
    # ###########################

    # _______________________________________________
    # Общие
    # _______________________________________________

    # ID
    def get_id(self) -> int:
        return self.__camera_index

    # FPS
    def get_fps(self):
        return self.__video_capture.get(cv2.CAP_PROP_FPS)

    # Name
    def get_name(self) -> str:
        return "OpenCV camera " + str(self.__camera_index)

    # _______________________________________________

    # Pixel format
    def set_pixel_format(self, pixel_format: PixelFormat) -> None:
        self.__pixel_format = pixel_format

    def get_pixel_format(self) -> PixelFormat:
        return self.__pixel_format
