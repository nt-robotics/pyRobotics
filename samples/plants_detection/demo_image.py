
from roboticsnt.computerVision.detectors import ColorDetector, ObjectDetector

import numpy as np
import cv2

MAX_SCORE = 0.2
DRAW_COLOR = (220, 10, 10)
FONT = cv2.FONT_HERSHEY_SIMPLEX
LINE_THICKNESS = 6
FONT_SCALE = 4

MASK_COLOR = (10, 10, 230)
MASK_ALPHA = 0.8

IMAGE_PATH = "/home/user/Изображения/Для буклета/20180730_131610.jpg"
# IMAGE_PATH = "/home/user/Изображения/Для буклета/20180730_131045.jpg"
# IMAGE_PATH = "/home/user/Изображения/Для буклета/20180730_131618.jpg"

MODEL_PATH = "/home/user/ObjectDetection/trainSets/object_detection_api/cabbage_from_above/train/graph_45256/frozen_inference_graph.pb"

__H_MIN = 65
__H_MAX = 159
__S_MIN = 0
__S_MAX = 255
__V_MIN = 0
__V_MAX = 255


color_detector = ColorDetector(__H_MIN, __H_MAX, __S_MIN, __S_MAX, __V_MIN, __V_MAX)
cabbage_detector = ObjectDetector(MODEL_PATH)

frame = cv2.imread(IMAGE_PATH)

result = cabbage_detector.detect(frame)
mask = color_detector.detect(frame)

num_detections = int(result[0][0])

cols = frame.shape[1]
rows = frame.shape[0]


for i in range(num_detections):
    classId = int(result[3][0][i])
    score = float(result[1][0][i])
    bbox = [float(v) for v in result[2][0][i]]

    if score > MAX_SCORE:
        x = bbox[1] * cols
        y = bbox[0] * rows
        right = bbox[3] * cols
        bottom = bbox[2] * rows

        center = (int(x + (right - x) / 2), int(y + (bottom - y) / 2))
        size = (int((right - x) / 2), int((bottom - y) / 2))

        cv2.ellipse(frame, center, size, 0, 0, 360, DRAW_COLOR, LINE_THICKNESS, cv2.LINE_AA)

        cv2.ellipse(mask, center, size, 0, 0, 360, 0, -1, cv2.LINE_AA)

        cv2.putText(frame, str(int(score * 100)) + " %", (center[0] - 10, center[1] - 5), FONT, FONT_SCALE, DRAW_COLOR, LINE_THICKNESS, cv2.LINE_AA)

mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
mask[np.where((mask == [255, 255, 255]).all(axis=2))] = MASK_COLOR
frame = cv2.addWeighted(frame, 1, mask, MASK_ALPHA, 0)

cv2.imwrite("/home/user/Изображения/Для буклета/20180730_131610_2.jpg", frame)

frame = cv2.resize(frame, (800, 600))

cv2.imshow('image', frame)
# cv2.imshow('mask', mask)
cv2.waitKey(0)

