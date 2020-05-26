from typing import List

import cv2
import numpy as np

import tensorflow as tf
# import tensorflow.compat.v1 as tf

from pyrobotics.computerVision.neural_netvorks.core import NeuralNetwork, NeuralNetworkDetectResult


class TensorflowNN(NeuralNetwork):

    def __init__(self, model: str, classes: List[str], frame_size=(300, 300), min_confidence=None):
        super().__init__(classes, frame_size, min_confidence)

        tf.reset_default_graph()

        f = tf.gfile.GFile(model, 'rb')
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())

        self.sess = tf.Session()
        self.sess.graph.as_default()
        tf.import_graph_def(graph_def, name='')

    def detect(self, frame: np.ndarray, swap_rb: bool = False) -> List[NeuralNetworkDetectResult]:
        results_list = []

        frame = self._resize_frame(frame)

        if swap_rb:
            frame = frame[:, :, [2, 1, 0]]  # BGR2RGB(swap R B channels manually)

        results = self.sess.run([
                                 self.sess.graph.get_tensor_by_name('num_detections:0'),
                                 self.sess.graph.get_tensor_by_name('detection_scores:0'),
                                 self.sess.graph.get_tensor_by_name('detection_boxes:0'),
                                 self.sess.graph.get_tensor_by_name('detection_classes:0')
                                 ],
                                feed_dict={'image_tensor:0': frame.reshape(1, frame.shape[0], frame.shape[1], 3)})

        for i in range(int(results[0][0])):
            confidence = results[1][0][i]
            if confidence > self._min_confidence:
                box = results[2][0][i]
                box = [box[1], box[0], box[3], box[2]]
                class_id = int(results[3][0][i])
                class_name = self._classes[class_id]
                results_list.append(NeuralNetworkDetectResult(class_name, confidence, box))

        return results_list
