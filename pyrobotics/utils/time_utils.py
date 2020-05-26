import time


class TimeCounter(object):

    def __init__(self):
        self.__last_check_time = None
        self.__is_started = False
        self.__total_millis = 0

        self.__total_seconds = 0
        self.__total_minutes = 0

        # self.__days = 0
        self.__hours = 0
        self.__minutes = 0
        self.__seconds = 0
        self.__milliseconds = 0

    def get_time_string(self) -> str:
        return str(self)

    def get_hours(self) -> int:
        self.__update()
        return self.__hours

    def get_minutes(self) -> int:
        self.__update()
        return self.__minutes

    def get_seconds(self) -> int:
        self.__update()
        return self.__seconds

    def get_milliseconds(self) -> int:
        self.__update()
        return self.__milliseconds

    def get_total_millis(self):
        self.__update()
        return self.__total_millis

    def get_total_seconds(self):
        self.__update()
        return self.__total_seconds

    def get_total_minutes(self):
        self.__update()
        return self.__total_minutes

    def start(self):
        self.__is_started = True
        self.__last_check_time = millis()

    def __str__(self):
        self.__update()
        return '{:02}:{:02}:{:02}.{:03}'.format(self.__hours, self.__minutes, self.__seconds, self.__milliseconds)

    def set_pause(self, value: bool):
        if self.__is_started and not value:
            return
        self.__is_started = not value
        if not value:
            self.__last_check_time = millis()

    def reset(self):
        self.__total_millis = 0

    def stop(self):
        self.reset()
        self.__is_started = False

    def __update(self) -> None:
        if self.__is_started:
            now = millis()
            self.__total_millis += now - self.__last_check_time
            self.__last_check_time = now

            self.__total_seconds = self.__total_millis // 1000
            self.__total_minutes = self.__total_millis // 1000 // 60

            self.__hours = self.__total_millis // 1000 // 60 // 60
            self.__minutes = self.__total_millis // 1000 // 60 % 60
            self.__seconds = self.__total_millis // 1000 % 60
            self.__milliseconds = self.__total_millis % 1000


def millis():
    return int(time.monotonic() * 1000)
    # return int(time.time() * 1000)
