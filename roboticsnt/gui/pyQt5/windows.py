from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QSlider, QVBoxLayout, QLabel


class ColorDetectorWindow(QWidget):

    __BLUR_MIN_VALUE = 1
    __BLUR_MAX_VALUE = 9
    __SLIDER_MIN_VALUE = 0
    __SLIDER_MAX_VALUE = 255
    __SLIDER_STEP = 1

    def __init__(self, title='Color detector settings', fx=0, fy=0, width=200, height=200):
        super().__init__()

        self.setWindowTitle(title)
        self.setGeometry(fx, fy, width, height)

        self.__layout = QVBoxLayout()

        self.__blur_slider = QSlider(Qt.Horizontal, self)
        self.__blur_slider.setMinimum(self.__BLUR_MIN_VALUE)
        self.__blur_slider.setMaximum(self.__BLUR_MAX_VALUE)
        self.__h_min_slider = QSlider(Qt.Horizontal, self)
        self.__h_min_slider.setMinimum(self.__SLIDER_MIN_VALUE)
        self.__h_min_slider.setMaximum(self.__SLIDER_MAX_VALUE)
        self.__h_max_slider = QSlider(Qt.Horizontal, self)
        self.__h_max_slider.setMinimum(self.__SLIDER_MIN_VALUE)
        self.__h_max_slider.setMaximum(self.__SLIDER_MAX_VALUE)
        self.__s_min_slider = QSlider(Qt.Horizontal, self)
        self.__s_min_slider.setMinimum(self.__SLIDER_MIN_VALUE)
        self.__s_min_slider.setMaximum(self.__SLIDER_MAX_VALUE)
        self.__s_max_slider = QSlider(Qt.Horizontal, self)
        self.__s_max_slider.setMinimum(self.__SLIDER_MIN_VALUE)
        self.__s_max_slider.setMaximum(self.__SLIDER_MAX_VALUE)
        self.__v_min_slider = QSlider(Qt.Horizontal, self)
        self.__v_min_slider.setMinimum(self.__SLIDER_MIN_VALUE)
        self.__v_min_slider.setMaximum(self.__SLIDER_MAX_VALUE)
        self.__v_max_slider = QSlider(Qt.Horizontal, self)
        self.__v_max_slider.setMinimum(self.__SLIDER_MIN_VALUE)
        self.__v_max_slider.setMaximum(self.__SLIDER_MAX_VALUE)

        # Events to update slider labels
        self.__blur_slider.valueChanged.connect(self.__on_slider_value_changed)
        self.__h_min_slider.valueChanged.connect(self.__on_slider_value_changed)
        self.__h_max_slider.valueChanged.connect(self.__on_slider_value_changed)
        self.__s_min_slider.valueChanged.connect(self.__on_slider_value_changed)
        self.__s_max_slider.valueChanged.connect(self.__on_slider_value_changed)
        self.__v_min_slider.valueChanged.connect(self.__on_slider_value_changed)
        self.__v_max_slider.valueChanged.connect(self.__on_slider_value_changed)

        self.__layout.addStretch(1)
        self.__blur_label = QLabel("Blur:", self)
        self.__layout.addWidget(self.__blur_label)
        self.__layout.addWidget(self.__blur_slider)
        self.__layout.addStretch(1)
        self.__h_min_label = QLabel("H min:", self)
        self.__layout.addWidget(self.__h_min_label)
        self.__layout.addWidget(self.__h_min_slider)
        self.__layout.addStretch(1)
        self.__h_max_label = QLabel("H max:", self)
        self.__layout.addWidget(self.__h_max_label)
        self.__layout.addWidget(self.__h_max_slider)
        self.__layout.addStretch(1)
        self.__s_min_label = QLabel("S min:", self)
        self.__layout.addWidget(self.__s_min_label)
        self.__layout.addWidget(self.__s_min_slider)
        self.__layout.addStretch(1)
        self.__s_max_label = QLabel("S max:", self)
        self.__layout.addWidget(self.__s_max_label)
        self.__layout.addWidget(self.__s_max_slider)
        self.__layout.addStretch(1)
        self.__v_min_label = QLabel("V min:", self)
        self.__layout.addWidget(self.__v_min_label)
        self.__layout.addWidget(self.__v_min_slider)
        self.__layout.addStretch(1)
        self.__v_max_label = QLabel("V max:", self)
        self.__layout.addWidget(self.__v_max_label)
        self.__layout.addWidget(self.__v_max_slider)

        self.__layout.addStretch(1)

        self.setLayout(self.__layout)

        self.set_blur(self.__SLIDER_MIN_VALUE)
        self.set_h_min(self.__SLIDER_MIN_VALUE)
        self.set_h_max(self.__SLIDER_MAX_VALUE)
        self.set_s_min(self.__SLIDER_MIN_VALUE)
        self.set_s_max(self.__SLIDER_MAX_VALUE)
        self.set_v_min(self.__SLIDER_MIN_VALUE)
        self.set_v_max(self.__SLIDER_MAX_VALUE)

    def add_change_sliders_value_listener(self, listener):
        self.__blur_slider.valueChanged.connect(listener)
        self.__h_min_slider.valueChanged.connect(listener)
        self.__h_max_slider.valueChanged.connect(listener)
        self.__s_min_slider.valueChanged.connect(listener)
        self.__s_max_slider.valueChanged.connect(listener)
        self.__v_min_slider.valueChanged.connect(listener)
        self.__v_max_slider.valueChanged.connect(listener)

    def get_blur(self):
        return self.__blur_slider.value()

    def get_h_min(self):
        return self.__h_min_slider.value()

    def get_h_max(self):
        return self.__h_max_slider.value()

    def get_s_min(self):
        return self.__s_min_slider.value()

    def get_s_max(self):
        return self.__s_max_slider.value()

    def get_v_min(self):
        return self.__v_min_slider.value()

    def get_v_max(self):
        return self.__v_max_slider.value()

    def set_blur(self, value):
        self.__blur_slider.setValue(value)

    def set_h_min(self, value):
        self.__h_min_slider.setValue(value)

    def set_h_max(self, value):
        self.__h_max_slider.setValue(value)

    def set_s_min(self, value):
        self.__s_min_slider.setValue(value)

    def set_s_max(self, value):
        self.__s_max_slider.setValue(value)

    def set_v_min(self, value):
        self.__v_min_slider.setValue(value)

    def set_v_max(self, value):
        self.__v_max_slider.setValue(value)

    def __on_slider_value_changed(self):
        # Default listener to change labels text
        self.__blur_label.setText("Blur: (" + str(self.__blur_slider.value()) + ")")
        self.__h_min_label.setText("H min: (" + str(self.__h_min_slider.value()) + ")")
        self.__h_max_label.setText("H max: (" + str(self.__h_max_slider.value()) + ")")
        self.__s_min_label.setText("S min: (" + str(self.__s_min_slider.value()) + ")")
        self.__s_max_label.setText("S max: (" + str(self.__s_max_slider.value()) + ")")
        self.__v_min_label.setText("V min: (" + str(self.__v_min_slider.value()) + ")")
        self.__v_max_label.setText("V max: (" + str(self.__v_max_slider.value()) + ")")
        # print("Blur: ", self.__blur_slider.value())
        # print("H min: ", self.__h_min_slider.value())
        # print("H max: ", self.__h_max_slider.value())
        # print("S min: ", self.__s_min_slider.value())
        # print("S max: ", self.__s_max_slider.value())
        # print("V min: ", self.__v_min_slider.value())
        # print("V max: ", self.__v_max_slider.value())
        # print("===================================")
