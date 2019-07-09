import cv2 as cv
import tensorflow as tf


class ObjectDetector(object):

    __INPUT_IMAGE_SIZE = (300, 300)

    def __init__(self, model_path, max_score=0.4):
        self.sess = None
        # self.max_score = max_score

        # Reset the graph. If you do not do this when creating a new ObjectDetection instance with a different model,
        # tensorflow model does not change
        tf.reset_default_graph()

        f = tf.gfile.GFile(model_path, 'rb')
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())

        self.sess = tf.Session()
        self.sess.graph.as_default()
        tf.import_graph_def(graph_def, name='')

    def detect(self, image):
        inp = cv.resize(image, self.__INPUT_IMAGE_SIZE)
        inp = inp[:, :, [2, 1, 0]]  # BGR2RGB

        return self.sess.run([self.sess.graph.get_tensor_by_name('num_detections:0'),
                              self.sess.graph.get_tensor_by_name('detection_scores:0'),
                              self.sess.graph.get_tensor_by_name('detection_boxes:0'),
                              self.sess.graph.get_tensor_by_name('detection_classes:0')],
                             feed_dict={'image_tensor:0': inp.reshape(1, inp.shape[0], inp.shape[1], 3)})


class ColorDetector(object):

    def __init__(self, h_min=0, h_max=255, s_min=0, s_max=255, v_min=0, v_max=255, blur_size=3):
        self.h_min = h_min
        self.h_max = h_max
        self.s_min = s_min
        self.s_max = s_max
        self.v_min = v_min
        self.v_max = v_max
        self.blur_size = blur_size

    def detect(self, original_img):
        blur_image = cv.blur(original_img, (self.blur_size, self.blur_size))
        hsv_image = cv.cvtColor(blur_image, cv.COLOR_RGB2HSV_FULL)

        low_color = (self.h_min, self.s_min, self.v_min)
        high_color = (self.h_max, self.s_max, self.v_max)

        range_image = cv.inRange(hsv_image, low_color, high_color)

        # _, contours, hierarchy = cv.findContours(range_image, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

        return range_image
