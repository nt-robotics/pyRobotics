import os
from typing import List, Tuple

import cv2
import numpy as np
from abc import ABCMeta, abstractmethod


class NeuralNetworkDetectResult(object):

    def __init__(self, class_name: str, confidence: float, box: List[float]):
        self.__class_name = class_name
        self.__confidence = confidence
        self.__box = box

    def get_class(self) -> str:
        return self.__class_name

    def get_confidence(self) -> float:
        return self.__confidence

    def get_box(self) -> List[float]:
        return self.__box


class NeuralNetwork(object):
    __metaclass__ = ABCMeta

    __PASCAL_VOC_CLASSES_FILE_PATH = os.path.join(os.path.dirname(__file__), "labels", "pascal_voc_classes.txt")
    __COCO_CLASSES_91_FILE_PATH = os.path.join(os.path.dirname(__file__), "labels", "coco_classes_91.txt")
    __COCO_CLASSES_80_FILE_PATH = os.path.join(os.path.dirname(__file__), "labels", "coco_classes_80.txt")

    __DEFAULT_MIN_CONFIDENCE = 0.1

    @staticmethod
    def __get_file_lines(file_path: str):
        with open(file_path) as file:
            data = file.read().strip().split("\n")
            return data

    @staticmethod
    def get_pascal_voc_classes() -> List[str]:
        return NeuralNetwork.__get_file_lines(NeuralNetwork.__PASCAL_VOC_CLASSES_FILE_PATH)

    @staticmethod
    def get_coco_91_classes() -> List[str]:
        return NeuralNetwork.__get_file_lines(NeuralNetwork.__COCO_CLASSES_91_FILE_PATH)

    @staticmethod
    def get_coco_80_classes() -> List[str]:
        return NeuralNetwork.__get_file_lines(NeuralNetwork.__COCO_CLASSES_80_FILE_PATH)

    def __init__(self, classes: List[str], frame_size: Tuple[int, int], min_confidence: float = None):
        self._classes = classes
        self._frame_size = frame_size
        self._min_confidence = self.__DEFAULT_MIN_CONFIDENCE if min_confidence is None else min_confidence

    @abstractmethod
    def detect(self, frame: np.ndarray, swap_rb: bool) -> List[NeuralNetworkDetectResult]:
        pass

    def set_min_confidence(self, value: float):
        self._min_confidence = value

    def get_min_confidence(self) -> float:
        return self._min_confidence

    def get_classes(self) -> List[str]:
        return self._classes

    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        if (frame.shape[1], frame.shape[0]) != self._frame_size:
            return cv2.resize(frame, self._frame_size)
        return frame
