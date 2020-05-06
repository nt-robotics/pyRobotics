import time

from serial import SerialException, Serial

from pyrobotics.commandProtocol.command_protocol import ProtocolConnection, Command
from pyrobotics.serial.serial_port import SerialPort


class ArduinoCommand:

    # To arduino
    TYPE_ADD_MOTOR = 0x30
    TYPE_START_MOTOR = 0x31
    TYPE_STOP_MOTOR = 0x32
    TYPE_SET_MOTOR_DIRECTION = 0x33
    TYPE_SET_MOTOR_SPEED = 0x34
    TYPE_MOTOR_ROTATE_TURNS = 0x35

    TYPE_ADD_ABSOLUTE_ENCODER_LISTENER = 0x40
    TYPE_ADD_MOTOR_STATE_LISTENER = 0x41

    TYPE_SET_ANALOG = 0x50
    TYPE_SET_DIGITAL = 0x51
    TYPE_SET_PIN_MODE = 0x52

    TYPE_SERVO_ATTACH = 0x54
    TYPE_SERVO_ROTATE = 0x55
    TYPE_SERVO_DETACH = 0x56
    TYPE_GET_DIGITAL = 0x57

    TYPE_ADD_DIGITAL_LISTENER = 0x58

    TYPE_WATCH_DOG = 0x80

    # From arduino

    TYPE_DIGITAL_PIN_VALUE = 0x71
    TYPE_ABSOLUTE_ENCODER_ANGLE = 0x72
    TYPE_MOTOR_STATE = 0x73

    # Errors
    TYPE_ERROR = 0x60


class ArduinoConnection(ProtocolConnection):

    # The delay between the connection by serial port and the sending of a successful connection event
    __SLEEP_AFTER_CONNECTION = 0  # seconds

    __DEFAULT_FILTER_INTERVAL = 220  # milliseconds

    __CONNECT_AND_WATCHDOG_INTERVAL = 1000

    def __init__(self, port=None, speed=SerialPort.BAUDRATE_115200, auto_connect=False, use_change_pins_time_filter=True):
        super().__init__()

        self.__is_serial_port_connected = False
        self.__is_auth_on_arduino = False

        self.__port = port
        self.__speed = speed
        self.__serial_manager = None

        self.__connect_watchdog_last_time = 0

        # Дребезг
        self.__listeners_list = dict()
        self.__filter_interval = self.__DEFAULT_FILTER_INTERVAL
        self.__is_used_change_pins_time_filter = use_change_pins_time_filter

        if auto_connect:
            self.connect()

    def run(self):

        while self.__is_serial_port_connected:
            data = self._read()
            if data is not None:
                # print("DATA : ", data)
                self._parser.parse(data)

            now = time.time() * 1000

            if now - self.__connect_watchdog_last_time > self.__CONNECT_AND_WATCHDOG_INTERVAL:
                if self.__is_auth_on_arduino:
                    self.__send_watchdog_command()
                else:
                    self.__send_try_connect_command()

                self.__connect_watchdog_last_time = now
        try:
            self.__serial_manager.close()
        except SerialException as msg:
            super()._dispatch_on_error(msg)

        super()._dispatch_on_disconnect()
        super()._clear_event_handlers()

    def connect(self, port=None):
        if self.__port is None and port is None:
            error_mes = "Protocol connection exception: connection port not received"
            # super()._dispatch_on_error(error_mes)
            raise Exception(error_mes)
        if port is not None:
            self.__port = port
        try:
            self.__serial_manager = Serial(self.__port, self.__speed, dsrdtr=1, timeout=0)
        except SerialException as msg:
            super()._dispatch_on_error(msg)
        except ConnectionError as msg:
            super()._dispatch_on_error(msg)
        else:
            self.__is_serial_port_connected = True
            self.start()

    def close(self):
        self.__is_serial_port_connected = False

    def is_connected(self):
        return self.__is_serial_port_connected and self.__is_auth_on_arduino

    def get_port(self):
        return self.__port

    # Time filter
    def set_use_change_pins_time_filter(self, is_used, filter_interval=None):
        self.__is_used_change_pins_time_filter = is_used
        if is_used & filter_interval is not None:
            self.__filter_interval = filter_interval

    def set_change_pins_time_filter_interval(self, value):
        self.__filter_interval = value

    # #########
    # Private
    # #########

    def _send_command(self, command):

        if not self.__is_serial_port_connected:
            error_mes = "Connection is not established or is already disconnected. Use the \"connect\" method to " \
                        "establish a connection. "
            # super()._dispatch_on_error(error_mes)
            raise Exception(error_mes)

        if not self.__is_auth_on_arduino and command.get_type() != Command.TYPE_CONNECT:
            error_mes = "You are not authorized on the Arduino board. Wait for the \"on_connect\" event and then " \
                        "send the commands. "
            # super()._dispatch_on_error(error_mes)
            raise Exception(error_mes)

        try:
            self.__serial_manager.write(command.get_bytes())
        except ConnectionError as msg:
            super()._dispatch_on_error(msg)
            self.close()
        except SerialException as msg:
            super()._dispatch_on_error(msg)
            self.close()

    def _read(self):
        try:
            bt = self.__serial_manager.read()
        except SerialException as msg:
            self._dispatch_on_error(msg)
            self.close()
        else:
            if bt != '' and len(bt) > 0:
                return bt
            else:
                return None

    # Connection
    def __send_try_connect_command(self):
        self._send_command(Command(Command.TYPE_CONNECT, ProtocolConnection.CONNECT_PASSWORD.encode('utf-8')))

    def __send_watchdog_command(self):
        self._send_command(Command(ArduinoCommand.TYPE_WATCH_DOG, bytes([0])))

    # Connection listeners
    def _dispatch_on_command(self, command):
        if command.get_type() == Command.TYPE_CONNECT_RESULT:
            if command.get_integer_data() == 1:
                time.sleep(self.__SLEEP_AFTER_CONNECTION)
                self.__is_auth_on_arduino = True
                self._dispatch_on_connect()
            else:
                super()._dispatch_on_error("Authentication error. Password incorrect")
                self.close()

        elif command.get_type() == ArduinoCommand.TYPE_DIGITAL_PIN_VALUE:
            if self.__is_used_change_pins_time_filter:

                pin = command.get_data()[0]
                last_change_time = self.__listeners_list.get(pin)
                current_time = time.time() * 1000

                if last_change_time is not None:
                    if (current_time - last_change_time) < self.__filter_interval:
                        return

                self.__listeners_list[pin] = current_time

                super()._dispatch_on_command(command)

            else:
                super()._dispatch_on_command(command)

        elif command.get_type() == ArduinoCommand.TYPE_ERROR:
            super()._dispatch_on_error(command.get_string_data())
            super()._dispatch_on_command(command)

        else:
            super()._dispatch_on_command(command)


# !!!
# Контроллеры не надо наследовать от Connection, лучше экземпляр
# Connection передавать в конструктор контроллера при создании,
# тогда можно будет использовать несколько контроллеров на одно соединение


class ArduinoPinsController(ArduinoConnection):

    PIN_MODE_INPUT = 0x0
    PIN_MODE_OUTPUT = 0x1
    PIN_MODE_INPUT_PULLUP = 0x2

    LOW = 0x0
    HIGH = 0x1

    def __init__(self, port=None, speed=SerialPort.BAUDRATE_115200, auto_connect=False, use_change_pins_time_filter=True):
        super().__init__(port, speed, auto_connect, use_change_pins_time_filter)

    ##############
    # Commands
    ##############

    # Servos (Not tested)
    def attach_servo(self, pin):
        self._send_command(Command(ArduinoCommand.TYPE_SERVO_ATTACH, bytes([pin])))

    def rotate_servo(self, pin, angle):
        self._send_command(Command(ArduinoCommand.TYPE_SERVO_ROTATE, bytes([pin, angle])))

    def detach_servo(self, pin):
        self._send_command(Command(ArduinoCommand.TYPE_SERVO_ATTACH, bytes([pin])))

    # Pins
    def set_pin_mode(self, pin, mode):
        self._send_command(Command(ArduinoCommand.TYPE_SET_PIN_MODE, bytes([pin, mode])))

    def set_digital_pin(self, pin, value):
        self._send_command(Command(ArduinoCommand.TYPE_SET_DIGITAL, bytes([pin, value])))

    def get_digital_pin(self, pin):
        self._send_command(Command(ArduinoCommand.TYPE_GET_DIGITAL, bytes([pin])))

    def set_analog_pin(self, pin, value):
        self._send_command(Command(ArduinoCommand.TYPE_SET_ANALOG, bytes([pin, value])))

    # Listeners
    def add_digital_pin_listener(self, pin, pin_mode=None):
        if pin_mode is not None:
            self.set_pin_mode(pin, pin_mode)
        self._send_command(Command(ArduinoCommand.TYPE_ADD_DIGITAL_LISTENER, bytes([pin])))


class ArduinoGeckoDriveG540Controller(ArduinoConnection):

    MOTOR_DIRECTION_CLOCKWISE = 0x1
    MOTOR_DIRECTION_COUNTERCLOCKWISE = 0x0
    # 2147483 - max turns count (Ограничение ардуино long 2147483 * 2000(steps count))
    _MOTOR_MAX_TURNS_COUNT = 2147483

    MOTOR_STATE_STOPPED = 0x00
    MOTOR_STATE_RUNNABLE = 0x01

    def __init__(self, port=None, speed=SerialPort.BAUDRATE_115200, auto_connect=False, use_change_pins_time_filter=True):
        super().__init__(port, speed, auto_connect, use_change_pins_time_filter)

    def add_motor_state_listener(self, motor_index):
        self._send_command(Command(ArduinoCommand.TYPE_ADD_MOTOR_STATE_LISTENER, bytes([motor_index])))

    # Motors
    def add_motor(self, steps_count, step_pin, dir_pin):
        self._send_command(Command(ArduinoCommand.TYPE_ADD_MOTOR, bytes([steps_count, step_pin, dir_pin])))

    def start_motor(self, index):
        self._send_command(Command(ArduinoCommand.TYPE_START_MOTOR, bytes([index])))

    def stop_motor(self, index):
        self._send_command(Command(ArduinoCommand.TYPE_STOP_MOTOR, bytes([index])))

    def motor_rotate_turns(self, index, turns_count):
        if turns_count > self._MOTOR_MAX_TURNS_COUNT:
            error_mes = "Error. Turns count value must be between 1 and " + str(self._MOTOR_MAX_TURNS_COUNT)
            # super()._dispatch_on_error(error_mes)
            raise Exception(error_mes)
        turns_count_bytes = turns_count.to_bytes(4, byteorder='big')
        data = bytes([index]) + turns_count_bytes
        self._send_command(Command(ArduinoCommand.TYPE_MOTOR_ROTATE_TURNS, data))

    def set_motor_direction(self, index, direction):
        self._send_command(Command(ArduinoCommand.TYPE_SET_MOTOR_DIRECTION, bytes([index, direction])))

    def set_motor_speed(self, index, speed):
        speed_bytes = speed.to_bytes(4, byteorder='big')
        data = bytes([index]) + speed_bytes
        self._send_command(Command(ArduinoCommand.TYPE_SET_MOTOR_SPEED, data))


class ArduinoEncoderController(ArduinoConnection):

    def __init__(self, port=None, speed=SerialPort.BAUDRATE_115200, auto_connect=False, use_change_pins_time_filter=True):
        super().__init__(port, speed, auto_connect, use_change_pins_time_filter)

        self._angle = None
        self.add_on_command_event_handler(self._on_command_handler)

        # self.__last_command_time = millis()

    ############
    # Public
    ############

    def add_absolute_encoder_listener(self, pins_list):
        self._send_command(Command(ArduinoCommand.TYPE_ADD_ABSOLUTE_ENCODER_LISTENER, bytes(pins_list)))

    def get_angle(self):
        return self._angle

    ############
    # Private
    ############

    def _on_command_handler(self, command):
        if command.get_type() == ArduinoCommand.TYPE_ABSOLUTE_ENCODER_ANGLE:
            self._angle = command.get_float_data(4, 0)

            # now = millis()
            # print("COMMAND DELTA: ", now - self.__last_command_time)
            # self.__last_command_time = now
