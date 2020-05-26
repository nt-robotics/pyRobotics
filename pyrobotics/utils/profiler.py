
from pyrobotics.utils.time_utils import millis


# Class for calculate code time
class Profiler(object):

    def __init__(self, name):
        self.__name = name
        self.__start_time = None

    def __enter__(self):
        self.__start_time = millis()

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(self.__name, ": ", millis() - self.__start_time)