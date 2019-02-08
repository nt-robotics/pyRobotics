import cv2
import sys
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QThread, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QHBoxLayout, QSlider, QVBoxLayout
import numpy as np
from time import time


from roboticsnt.computerVision.detectors import ColorDetector, ObjectDetector


class VideoBuffer:

    def __init__(self, fps, length):

        self.buffer = []
        self.max_len = int(fps * length)
        self.fps = fps
        self.index = 0

    def put(self, frame):
        self.buffer.insert(0, frame)
        if len(self.buffer) > self.max_len:
            self.buffer.pop()

    def set_delay(self, delay):
        self.index = int(delay * self.fps / 1000)

    def get(self):
        if len(self.buffer) >= self.index + 1:
            return self.buffer[self.index]
        else:
            return None


class ReadVideoThread(QThread):

    change_frame_signal = pyqtSignal(np.ndarray, np.ndarray, list)

    # CAMERA_PATH = 0
    # CAMERA_PATH = 1
    CAMERA_PATH = "/home/user/Изображения/DataSets/Тесты/Видео/Капуста/Сверху/Солнце/20180808_165440.mp4"
    CAMERA_FRAME_SIZE = (540, 300)
    DELAY_BETWEEN_FRAMES = 33

    def run(self):

        camera = cv2.VideoCapture(self.CAMERA_PATH)

        color_detector = ColorDetector()
        cabbage_detector = ObjectDetector("/home/user/ObjectDetection/trainSets/object_detection_api/cabbage_from_above/train/graph_45256/frozen_inference_graph.pb")

        while camera.isOpened():
            read, frame = camera.read()
            frame = cv2.resize(frame, self.CAMERA_FRAME_SIZE)
            detect_result = cabbage_detector.detect(frame)
            mask = color_detector.detect(frame)

            self.change_frame_signal.emit(frame, mask, detect_result)

            # QThread.msleep(self.DELAY_BETWEEN_FRAMES)

        camera.release()


class MainWindow(QWidget):

    DRAW_COLOR = (190, 90, 0)
    MAX_SCORE = 0.1
    FONT = cv2.FONT_HERSHEY_SIMPLEX

    def __init__(self):
        super().__init__()

        self.detect_camera_video = QLabel()
        self.injectors_camera_video = QLabel()

        self.speed_label = QLabel("0 km/h")
        self.speed_label.setFixedHeight(20)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setFixedWidth(200)
        self.speed_slider.setTickInterval(1)

        h_box = QHBoxLayout()
        h_box.addWidget(self.detect_camera_video)
        h_box.addWidget(self.injectors_camera_video)

        v_box = QVBoxLayout()
        v_box.addWidget(self.speed_label)
        v_box.addWidget(self.speed_slider)
        v_box.addLayout(h_box)

        self.setLayout(v_box)

        self.setWindowTitle("Plants treatment demo")
        self.setMinimumSize(800, 600)
        self.showMaximized()

    def closeEvent(self, close_event):
        print("Main window closed")

    def resizeEvent(self, resize_event):
        # print("Resize to:", self.width(), self.height())
        # pixmap_resized = qt_pixmap.scaled(900, 200, QtCore.Qt.KeepAspectRatio)
        pass

    def show_detection_image(self, image_rgb):
        qt_pixmap = QPixmap.fromImage(QImage(image_rgb.data, image_rgb.shape[1], image_rgb.shape[0], QImage.Format_RGB888))
        self.detect_camera_video.setPixmap(qt_pixmap)

    def show_injectors_image(self, image_rgb):
        qt_pixmap = QPixmap.fromImage(QImage(image_rgb.data, image_rgb.shape[1], image_rgb.shape[0], QImage.Format_RGB888))
        self.injectors_camera_video.setPixmap(qt_pixmap)

    def draw_detection_result(self, result, frame):
        num_detections = int(result[0][0])

        rows = frame.shape[1]
        cols = frame.shape[0]

        for i in range(num_detections):
            classId = int(result[3][0][i])
            score = float(result[1][0][i])
            bbox = [float(v) for v in result[2][0][i]]

            if score > self.MAX_SCORE:
                x = bbox[1] * cols
                y = bbox[0] * rows
                right = bbox[3] * cols
                bottom = bbox[2] * rows

                center = (int(x + (right - x) / 2), int(y + (bottom - y) / 2))
                size = (int((right - x) / 2), int((bottom - y) / 2))
                # cv2.ellipse(mask, center, size, 0, 0, 360, 0, -1, cv.LINE_AA)
                cv2.ellipse(frame, center, size, 0, 0, 360, self.DRAW_COLOR, 2, cv2.LINE_AA)
                # cv.rectangle(result, (x, y), (right, bottom), DRAW_COLOR, thickness=2)
                cv2.putText(frame, str(int(score * 100)) + " %", (center[0] - 10, center[1] - 5), self.FONT, 0.7, self.DRAW_COLOR, 2, cv2.LINE_AA)


class PlantsTreatmentDemo:

    OBJECT_DETECTOR_MODEL_PATH = "/home/user/ObjectDetection/trainSets/object_detection_api/cabbage_from_above/train/graph_45256/frozen_inference_graph.pb"
    MIN_SPEED = 1   # km/h
    MAX_SPEED = 15   # km/h
    START_SPEED = 5   # km/h
    DISTANCE_TO_INJECTORS = 3   # meters
    INJECTORS_COUNT = 24
    MAX_SCORE = 0.1

    def __init__(self):

        # self.color_detector = ColorDetector()
        # self.cabbage_detector = ObjectDetector(self.OBJECT_DETECTOR_MODEL_PATH)

        app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.main_window.speed_slider.setMinimum(self.MIN_SPEED)
        self.main_window.speed_slider.setMaximum(self.MAX_SPEED)
        self.main_window.speed_slider.setValue(self.START_SPEED)
        self.main_window.speed_slider.valueChanged.connect(self.on_speed_change)

        thread = ReadVideoThread(self.main_window)
        thread.change_frame_signal.connect(self.on_frame_change)
        thread.start()

        fps = 30
        buffer_length = 20
        self.video_buffer = VideoBuffer(fps, buffer_length)
        self.on_speed_change()

        self.main_window.show()
        sys.exit(app.exec_())

    def on_speed_change(self):
        speed_km_h = self.main_window.speed_slider.value()
        speed_m_s = speed_km_h * 0.27
        video_delay = int((self.DISTANCE_TO_INJECTORS / speed_m_s) * 1000)  # milliseconds
        self.video_buffer.set_delay(video_delay)

        self.main_window.speed_label.setText("{0} km/h".format(speed_km_h))

    def on_frame_change(self, frame, mask, detection_result):
        # result = frame.copy()

        # self.main_window.show_detection_image(cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB))
        self.main_window.draw_detection_result(detection_result, frame)
        self.main_window.show_injectors_image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # mask = self.color_detector.detect(frame)
        # mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        # mask[np.where((mask == [255, 255, 255]).all(axis=2))] = [0, 33, 200]

        # original_frame_width = frame.shape[1]
        # original_frame_height = frame.shape[0]
        # rows = frame.shape[1]
        # cols = frame.shape[0]

        # detect_result = self.object_detector.detect(frame)
        # out = self.cabbage_detector.detect(frame)
        # print(out)
        # num_detections = int(out[0][0])

        # for i in range(num_detections):
        #     classId = int(out[3][0][i])
        #     score = float(out[1][0][i])
        #     bbox = [float(v) for v in out[2][0][i]]
        #
        #     if score > self.MAX_SCORE:
        #         x = bbox[1] * cols
        #         y = bbox[0] * rows
        #         right = bbox[3] * cols
        #         bottom = bbox[2] * rows
        #
        #         center = (int(x + (right - x) / 2), int(y + (bottom - y) / 2))
        #         size = (int((right - x) / 2), int((bottom - y) / 2))
        #         # cv2.ellipse(mask, center, size, 0, 0, 360, 0, -1, cv.LINE_AA)
        #         cv2.ellipse(frame, center, size, 0, 0, 360, self.DRAW_COLOR, 2, cv2.LINE_AA)
        #         # cv.rectangle(result, (x, y), (right, bottom), DRAW_COLOR, thickness=2)
        #         cv2.putText(frame, str(int(score * 100)) + " %", (center[0] - 10, center[1] - 5), self.FONT, 0.7, self.DRAW_COLOR, 2, cv2.LINE_AA)

        # self.video_buffer.put(frame)
        # frame2 = self.video_buffer.get()
        #
        # if frame2 is not None:
        #     image_rgb2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
        #     self.main_window.show_injectors_image(image_rgb2)
        #
        # mask = self.color_detector.detect(frame)
        # mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        # mask[np.where((mask == [255, 255, 255]).all(axis=2))] = [0, 33, 200]
        # result = cv2.addWeighted(frame, 1, mask, 0.9, 0)

        # image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # self.main_window.show_injectors_image(image_rgb)


if __name__ == "__main__":
    PlantsTreatmentDemo()
