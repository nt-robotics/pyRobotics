from threading import Thread
from typing import Tuple

import cv2

from pyrobotics.event import Event


class OpenCVCamera(object):

    def __init__(self, camera_index: int = -1):

        self.__frame_change_event = Event()
        self.__grab_started_event = Event()
        self.__grab_stopped_event = Event()
        self.__index = camera_index
        self.__grab_thread = None
        self.__is_connected = False

        self.__video_capture = cv2.VideoCapture(camera_index)

        if self.__video_capture is None or not self.__video_capture.isOpened():
            error_message = "Camera with index (" + str(camera_index) + ") not found"
            print("[ERROR]", self.__class__.__name__, error_message)
            return

        self.__is_connected = True

    def is_connected(self) -> bool:
        return self.__is_connected

    def get_fps(self):
        return self.__video_capture.get(cv2.CAP_PROP_FPS)

    def set_frame_size(self, size: Tuple[int]):
        self.__video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        self.__video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])

    def start(self) -> None:
        self.__grab_started_event.fire()
        self.__grab_thread = _GrabThread(self.__video_capture, self.__frame_change_event, self.__grab_stopped_event)
        self.__grab_thread.start()

    def stop(self) -> None:
        if self.__grab_thread is not None:
            self.__grab_thread.stop()
        self.__grab_thread = None

    def close(self):
        self.__video_capture.release()

    def is_grabbing(self) -> bool:
        return self.__grab_thread is not None

    # Events
    def add_frame_change_handler(self, handler) -> None:
        self.__frame_change_event.handle(handler)

    def add_grab_started_handler(self, handler) -> None:
        self.__grab_started_event.handle(handler)

    def add_grab_stopped_handler(self, handler) -> None:
        self.__grab_stopped_event.handle(handler)

    def remove_frame_change_handler(self, handler):
        self.__frame_change_event.unhandle(handler)

    def remove_grab_started_handler(self, handler) -> None:
        self.__grab_started_event.unhandle(handler)

    def remove_grab_stopped_handler(self, handler) -> None:
        self.__grab_stopped_event.unhandle(handler)


class _GrabThread(Thread):

    def __init__(self, video_capture: cv2.VideoCapture, change_event: Event, stop_event: Event):
        super().__init__()

        self.__is_started = False

        self.__video_capture = video_capture
        self.__frame_change_event = change_event
        self.__grab_stopped_event = stop_event

    def run(self) -> None:
        self.__is_started = True

        while self.__is_started:
            read, real_frame = self.__video_capture.read()
            if read:
                self.__frame_change_event.fire(real_frame)

        self.__grab_stopped_event.fire()

    def stop(self) -> None:
        self.__is_started = False
