import time
from threading import Thread

from roboticsnt.utils import millis
from roboticsnt.commandProtocol.arduino.arduino_controllers import ArduinoEncoderController
from roboticsnt.event import Event


class EncoderSpeedometer(object):

    __DEFAULT_ONE_TURN_DISTANCE = 0.8    # meters

    def __init__(self, pins_list, port=None, one_turn_distance=__DEFAULT_ONE_TURN_DISTANCE):
        super().__init__()

        self.__speed_change_event = Event()

        self.__pins_list = pins_list
        self.__port = port

        self.__encoder_connection = None
        self.__check_angle_thread = None

        self.__one_turn_distance = one_turn_distance

    #  Distance in meters
    def get_distance(self):
        distance = 0
        if self.__check_angle_thread is not None:
            distance = self.__check_angle_thread.get_distance()
        return distance

    # Speed in turns per minute
    def get_speed(self):
        speed = 0
        if self.__check_angle_thread is not None:
            speed = self.__check_angle_thread.get_speed()
        return speed

    def set_one_turn_distance(self, value):
        self.__one_turn_distance = value

    def create_connection(self):
        self.__encoder_connection = ArduinoEncoderController()
        self.__encoder_connection.add_on_connect_event_handler(self._on_connect)

    def connect(self, port=None):
        if port is not None:
            self.__port = port
        self.__encoder_connection.connect(self.__port)

    def is_connected(self):
        return self.__encoder_connection is not None and self.__encoder_connection.is_connected()

    def get_port(self):
        return self.__encoder_connection.get_port()

    def add_speed_change_handler(self, handler):
        self.__speed_change_event.handle(handler)

    def add_on_connect_event_handler(self, handler):
        self.__encoder_connection.add_on_connect_event_handler(handler)

    def add_on_disconnect_event_handler(self, handler):
        self.__encoder_connection.add_on_disconnect_event_handler(handler)

    def add_on_error_event_handler(self, handler):
        self.__encoder_connection.add_on_error_event_handler(handler)

    def stop(self):
        if self.__check_angle_thread is not None:
            self.__check_angle_thread.stop()
        if self.is_connected():
            self.__encoder_connection.close()
        self.__check_angle_thread = None

    def _on_connect(self):
        self.__encoder_connection.add_absolute_encoder_listener(self.__pins_list)
        self.__check_angle_thread = CheckEncoderAngleThread(self.__encoder_connection, self.__speed_change_event, self.__one_turn_distance)
        self.__check_angle_thread.start()


class CheckEncoderAngleThread(Thread):

    def __init__(self, encoder_connection, speed_change_event, one_turn_distance):
        super().__init__()

        self.__prev_angle = None

        self.__check_angle_last_time = None
        self.__CHECK_ANGLE_INTERVAL = 0.023  # seconds

        self.__is_started = False

        self.__encoder_connection = encoder_connection
        self.__speed = 0

        self.__total_distance = 0
        self.__one_turn_distance = one_turn_distance

        self.__speed_change_event = speed_change_event

    def get_speed(self):
        return self.__speed

    def get_distance(self):
        return self.__total_distance

    def stop(self):
        self.__is_started = False

    def run(self):

        self.__is_started = True

        self.__check_angle_last_time = millis()

        while self.__is_started:

            time_delta = millis() - self.__check_angle_last_time

            # Calculate distance
            if self.__speed > 0:
                # distance_delta = self.__one_turn_distance * time_delta / (self.__speed * 60 * 1000)
                distance_delta = self.__one_turn_distance * (self.__speed / 1000 / 60) * time_delta
                self.__total_distance += distance_delta

            # Calculate speed
            angle = self.__encoder_connection.get_angle()

            if angle is not None:

                if self.__prev_angle is not None:

                    angle_delta = 0

                    if self.__prev_angle < angle:
                        angle_delta = self.__prev_angle + 360 - angle
                        if angle_delta > 180:
                            angle_delta = self.__prev_angle - angle
                    elif self.__prev_angle > angle:
                        angle_delta = self.__prev_angle - angle
                        if angle_delta > 180:
                            angle_delta = self.__prev_angle - 360 - angle

                    speed = (angle_delta / 360) / (time_delta / 1000 / 60)

                    if speed != self.__speed:
                        self.__speed = speed
                        # print("angle_delta: ", angle_delta)
                        # print("time_delta: ", time_delta)
                        # print("SPEED tur/min: ", self.__speed)
                        # print("SPEED km/h: ", turns_per_minute_to_kilometers_per_hour(self.__speed, 0.04))
                        # print("angle: ", angle)
                        # print("prev_angle: ", self.__prev_angle)
                        # print("======================================")
                        self.__speed_change_event.fire(self.__speed)

                self.__prev_angle = angle

            self.__check_angle_last_time += time_delta

            time.sleep(self.__CHECK_ANGLE_INTERVAL)
