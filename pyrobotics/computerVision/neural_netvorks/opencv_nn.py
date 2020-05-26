from typing import List

import cv2
import numpy as np

from pyrobotics.computerVision.neural_netvorks.core import NeuralNetwork, NeuralNetworkDetectResult


class OpencvDarkNetNN(NeuralNetwork):

    def __init__(self, model: str, config: str, classes: List[str], frame_size=(320, 320), min_confidence=None, threshold=0.3):
        """
        OpencvDarkNetNN constructor
        @:param frame_size - the size to which the image must be converted is equal to the input of the neural network
        supported values (320, 320), (416, 416), (608, 608)
        """

        super().__init__(classes, frame_size, min_confidence)
        self.__net = cv2.dnn.readNetFromDarknet(config, model)
        self.__output_layers = [self.__net.getLayerNames()[i[0] - 1] for i in self.__net.getUnconnectedOutLayers()]
        # self.__net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        # self.__net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL_FP16)

        self.__threshold = threshold

    def detect(self, frame: np.ndarray, swap_rb: bool = False) -> List[NeuralNetworkDetectResult]:
        results_list = []

        frame = self._resize_frame(frame)
        # frame = frame[:, :, [2, 1, 0]]  # BGR2RGB(swap R B channels manually)

        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, self._frame_size, swapRB=swap_rb, crop=False)
        self.__net.setInput(blob)
        outs = self.__net.forward(self.__output_layers)

        class_ids = []
        confidences = []
        boxes_px = []
        boxes_relation = []
        width, height = self._frame_size
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > self._min_confidence:
                    box_relation = [detection[0] - detection[2]/2, detection[1] - detection[3]/2, detection[0] + detection[2]/2, detection[1] + detection[3]/2]
                    box_px = (box_relation * np.array([width, height, width, height])).astype("int")
                    boxes_px.append(box_px)
                    boxes_relation.append(box_relation)
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes_px, confidences, self._min_confidence, self.__threshold)

        if len(indexes) > 0:
            for i in indexes.flatten():
                result_confidence = confidences[i]
                if result_confidence > self._min_confidence:
                    result_class_name = self._classes[class_ids[i] + 1]
                    result_box = boxes_relation[i]
                    results_list.append(NeuralNetworkDetectResult(result_class_name, result_confidence, result_box))

        return results_list


class OpencvTFNN(NeuralNetwork):

    def __init__(self, model: str, config: str, classes: List[str], frame_size=(300, 300), min_confidence=None):
        """
        OpencvTF constructor
        @:param frame_size - the size to which the image must be converted is equal to the input of the neural network
        """

        super().__init__(classes, frame_size, min_confidence)
        self.__net = cv2.dnn.readNetFromTensorflow(model, config)

    def detect(self, frame: np.ndarray, swap_rb: bool = False) -> List[NeuralNetworkDetectResult]:
        results_list = []

        blob = cv2.dnn.blobFromImage(frame, size=self._frame_size, swapRB=swap_rb, crop=False)
        self.__net.setInput(blob)
        networkOutput = self.__net.forward()

        for detection in networkOutput[0, 0, :, :]:
            confidence = float(detection[2])
            if confidence > self._min_confidence:
                box = detection[3:7]
                classId = int(detection[1])
                class_name = self._classes[classId]
                results_list.append(NeuralNetworkDetectResult(class_name, confidence, box))

        return results_list


class OpencvCaffeNN(NeuralNetwork):

    def __init__(self, model: str, prototxt: str, classes: List[str], frame_size=(300, 300), min_confidence=None):
        """
        OpencvCaffeNN constructor
        @:param frame_size - the size to which the image must be converted is equal to the input of the neural network
        """

        super().__init__(classes, frame_size, min_confidence)
        self.__net = cv2.dnn.readNetFromCaffe(prototxt, model)

    def detect(self, frame: np.ndarray, swap_rb: bool = False) -> List[NeuralNetworkDetectResult]:
        results_list = []

        blob = cv2.dnn.blobFromImage(frame, 0.007843, self._frame_size, 127.5, swapRB=swap_rb, crop=False)
        self.__net.setInput(blob)
        networkOutput = self.__net.forward()

        for detection in networkOutput[0, 0, :, :]:
            confidence = float(detection[2])
            if confidence > self._min_confidence:
                box = detection[3:7]
                classId = int(detection[1])
                class_name = self._classes[classId]
                results_list.append(NeuralNetworkDetectResult(class_name, confidence, box))

        return results_list
