
class ColorDetectorWindowController(object):

    def __init__(self, detector, window):
        self.__detector = detector
        self.__window = window

        self.__window.set_blur(self.__detector.blur_size)
        self.__window.set_h_min(self.__detector.h_min)
        self.__window.set_h_max(self.__detector.h_max)
        self.__window.set_s_min(self.__detector.s_min)
        self.__window.set_s_max(self.__detector.s_max)
        self.__window.set_v_min(self.__detector.v_min)
        self.__window.set_v_max(self.__detector.v_max)

        self.__window.add_change_sliders_value_listener(self.__on_slider_value_change)

    def __on_slider_value_change(self):
        self.__detector.blur_size = self.__window.get_blur()
        self.__detector.h_min = self.__window.get_h_min()
        self.__detector.h_max = self.__window.get_h_max()
        self.__detector.s_min = self.__window.get_s_min()
        self.__detector.s_max = self.__window.get_s_max()
        self.__detector.v_min = self.__window.get_v_min()
        self.__detector.v_max = self.__window.get_v_max()
