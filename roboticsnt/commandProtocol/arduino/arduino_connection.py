import time

from serial import SerialException, Serial

from roboticsnt.commandProtocol.command_protocol import ProtocolConnection, Command
from roboticsnt.serial.serial_port import SerialPort


class ArduinoConnection(ProtocolConnection):

    PIN_MODE_INPUT = 0x0
    PIN_MODE_OUTPUT = 0x1
    PIN_MODE_INPUT_PULLUP = 0x2

    MOTOR_DIRECTION_CLOCKWISE = 0x1
    MOTOR_DIRECTION_COUNTERCLOCKWISE = 0x0
    # 2147483 - max turns count (Ограничение ардуино long 2147483 * 2000(steps count))
    _MAX_TURNS_COUNT = 2147483

    LOW = 0x0
    HIGH = 0x1

    __SLEEP_AFTER_CONNECTION = 2  # seconds
    __DEFAULT_FILTER_INTERVAL = 220  # milliseconds

    def __init__(self, port=None, speed=SerialPort.BAUDRATE_115200, auto_connect=False, use_change_pins_time_filter=True):
        super().__init__()

        self.__is_serial_port_connected = False
        self.__is_auth_on_arduino = False

        self.__port = port
        self.__speed = speed
        self.__serial_manager = None

        self.__connect_watchdog_last_time = 0
        self.__CONNECT_WATCHDOG_INTERVAL = 1000

        # Дребезг
        self.__listeners_list = dict()
        self.__filter_interval = self.__DEFAULT_FILTER_INTERVAL
        self.__is_used_change_pins_time_filter = use_change_pins_time_filter

        if auto_connect:
            self.connect()

    def connect(self, port=None):
        if self.__port is None and port is None:
            raise Exception("Protocol connection exception: connection port not received")
        if port is not None:
            self.__port = port
        try:
            self.__serial_manager = Serial(self.__port, self.__speed, dsrdtr=1, timeout=0)
        except SerialException as msg:
            print("SerialException: ", msg)
            super()._dispatch_on_error(msg)
        except ConnectionError as msg:
            print("ConnectionError: ", msg)
            super()._dispatch_on_error(msg)
        else:
            self.__is_serial_port_connected = True
            self.start()

    def run(self):
        super().run()
        while self.__is_serial_port_connected:

            data = self._read()
            if data is not None:
                print("DATA : ", data)
                self._parser.parse(data)

            now = time.time() * 1000

            if now - self.__connect_watchdog_last_time > self.__CONNECT_WATCHDOG_INTERVAL:
                if self.__is_auth_on_arduino:
                    pass
                    # print("send_watchdog_command")
                    # self.__send_watchdog_command()
                else:
                    # print("send_try_connect_command")
                    self.__send_try_connect_command()

                self.__connect_watchdog_last_time = now

    def send_command(self, command):
        if not self.__is_serial_port_connected:
            raise Exception("You must first connect to the port, and then send commands. Use connect method")
        try:
            self.__serial_manager.write(command.get_bytes())
        except ConnectionError as msg:
            super()._dispatch_on_error(msg)
        except SerialException as msg:
            super()._dispatch_on_error(msg)
            self.close()

    # Servos (Not tested)
    def attach_servo(self, pin):
        self.send_command(Command(ArduinoCommand.TYPE_SERVO_ATTACH, bytes([pin])))

    def rotate_servo(self, pin, angle):
        self.send_command(Command(ArduinoCommand.TYPE_SERVO_ROTATE, bytes([pin, angle])))

    def detach_servo(self, pin):
        self.send_command(Command(ArduinoCommand.TYPE_SERVO_ATTACH, bytes([pin])))

    # Time filter
    def set_use_change_pins_time_filter(self, is_used, filter_interval=None):
        self.__is_used_change_pins_time_filter = is_used
        if is_used & filter_interval is not None:
            self.__filter_interval = filter_interval

    def set_change_pins_time_filter_interval(self, value):
        self.__filter_interval = value

    # Pins
    def set_pin_mode(self, pin, mode):
        self.send_command(Command(ArduinoCommand.TYPE_SET_PIN_MODE, bytes([pin, mode])))

    def set_digital_pin(self, pin, value):
        self.send_command(Command(ArduinoCommand.TYPE_SET_DIGITAL, bytes([pin, value])))

    def get_digital_pin(self, pin):
        self.send_command(Command(ArduinoCommand.TYPE_GET_DIGITAL, bytes([pin])))

    def set_analog_pin(self, pin, value):
        self.send_command(Command(ArduinoCommand.TYPE_SET_ANALOG, bytes([pin, value])))

    # Listeners
    def add_digital_pin_listener(self, pin, pin_mode=None):
        if pin_mode is not None:
            self.set_pin_mode(pin, pin_mode)
        self.send_command(Command(ArduinoCommand.TYPE_ADD_DIGITAL_LISTENER, bytes([pin])))

    def add_absolute_encoder_listener(self, pins_list):
        self.send_command(Command(ArduinoCommand.TYPE_ADD_ABSOLUTE_ENCODER_LISTENER, bytes(pins_list)))

    # Motors
    def add_motor(self, steps_count, step_pin, dir_pin):
        self.send_command(Command(ArduinoCommand.TYPE_ADD_MOTOR, bytes([steps_count, step_pin, dir_pin])))

    def start_motor(self, index):
        self.send_command(Command(ArduinoCommand.TYPE_START_MOTOR, bytes([index])))

    def stop_motor(self, index):
        self.send_command(Command(ArduinoCommand.TYPE_STOP_MOTOR, bytes([index])))

    def motor_rotate_turns(self, index, turns_count):
        if turns_count > self._MAX_TURNS_COUNT:
            print("Error. Turns count value must be between 1 and ", self._MAX_TURNS_COUNT)
            return
        turns_count_bytes = turns_count.to_bytes(4, byteorder='big')
        data = bytes([index]) + turns_count_bytes
        self.send_command(Command(ArduinoCommand.TYPE_MOTOR_ROTATE_TURNS, data))

    def set_motor_direction(self, index, direction):
        self.send_command(Command(ArduinoCommand.TYPE_SET_MOTOR_DIRECTION, bytes([index, direction])))

    def set_motor_speed(self, index, speed):
        speed_bytes = speed.to_bytes(4, byteorder='big')
        data = bytes([index]) + speed_bytes
        self.send_command(Command(ArduinoCommand.TYPE_SET_MOTOR_SPEED, data))

    def close(self):
        try:
            self.__serial_manager.close()
        except SerialException as msg:
            super()._dispatch_on_error(msg)
        else:
            self.__is_serial_port_connected = False
            super().close()

    def is_connected(self):
        return self.__is_serial_port_connected

    def get_port(self):
        return self.__port

    # ##########
    # Private
    # ##########

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
        self.send_command(Command(Command.TYPE_CONNECT, ProtocolConnection.CONNECT_PASSWORD.encode('utf-8')))

    def __send_watchdog_command(self):
        self.send_command(Command(ArduinoCommand.TYPE_WATCH_DOG, bytes([0])))

    # Connection listeners
    def _dispatch_on_command(self, command):
        if command.get_type() == Command.TYPE_CONNECT_RESULT:
            if command.get_integer_data() == 1:
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


class ArduinoCommand:

    # To arduino
    TYPE_ADD_MOTOR = 0x30
    TYPE_START_MOTOR = 0x31
    TYPE_STOP_MOTOR = 0x32
    TYPE_SET_MOTOR_DIRECTION = 0x33
    TYPE_SET_MOTOR_SPEED = 0x34
    TYPE_MOTOR_ROTATE_TURNS = 0x35

    TYPE_ADD_ABSOLUTE_ENCODER_LISTENER = 0x40

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

    # Errors
    TYPE_ERROR = 0x60

# import time
#
# from roboticsnt.commandProtocol.command_protocol import Command, ProtocolConnection
# from roboticsnt.commandProtocol.serial_port_connection import SerialPortProtocolConnection
#
#
# class ArduinoConnection(SerialPortProtocolConnection):
#
#     PIN_MODE_INPUT = 0x0
#     PIN_MODE_OUTPUT = 0x1
#     PIN_MODE_INPUT_PULLUP = 0x2
#
#     MOTOR_DIRECTION_CLOCKWISE = 0x1
#     MOTOR_DIRECTION_COUNTERCLOCKWISE = 0x0
#
#     LOW = 0x0
#     HIGH = 0x1
#
#     __SLEEP_AFTER_CONNECTION = 2  # seconds
#     __DEFAULT_FILTER_INTERVAL = 220  # milliseconds
#
#     # 2147483 - max turns count (Ограничение ардуино long 2147483 * 2000(steps count))
#     _MAX_TURNS_COUNT = 2147483
#
#     def __init__(self, port=None, use_change_pins_time_filter=True):
#         super().__init__(port)
#
#         self.__is_confirm_password = False
#         self.__connect_watchdog_last_time = 0
#         self.__CONNECT_WATCHDOG_INTERVAL = 1000
#
#         # Дребезг
#         self.__listeners_list = dict()
#         self.__filter_interval = self.__DEFAULT_FILTER_INTERVAL
#         self.__is_used_change_pins_time_filter = use_change_pins_time_filter
#
#     # Connection
#     def __send_try_connect_command(self):
#         super().send_command(Command(Command.TYPE_CONNECT, ProtocolConnection.CONNECT_PASSWORD.encode('utf-8')))
#
#     def __send_watchdog_command(self):
#         super().send_command(Command(ArduinoCommand.TYPE_WATCH_DOG, bytes([0])))
#
#     def run(self):
#         while self._is_connected:
#             data = self._read()
#             if data is not None:
#                 print("DATA : ", data)
#                 self._parser.parse(data)
#
#             now = time.time() * 1000
#
#             if now - self.__connect_watchdog_last_time > self.__CONNECT_WATCHDOG_INTERVAL:
#                 print("TICK")
#                 if not self.__is_confirm_password:
#                     print("__send_try_connect_command")
#                     self.__send_try_connect_command()
#                 else:
#                     print("__send_watchdog_command")
#                     self.__send_watchdog_command()
#
#                 self.__connect_watchdog_last_time = now
#
#     # Servos (Not tested)
#     def attach_servo(self, pin):
#         super().send_command(Command(ArduinoCommand.TYPE_SERVO_ATTACH, bytes([pin])))
#
#     def rotate_servo(self, pin, angle):
#         super().send_command(Command(ArduinoCommand.TYPE_SERVO_ROTATE, bytes([pin, angle])))
#
#     def detach_servo(self, pin):
#         super().send_command(Command(ArduinoCommand.TYPE_SERVO_ATTACH, bytes([pin])))
#
#     # Time filter
#     def set_use_change_pins_time_filter(self, is_used, filter_interval=None):
#         self.__is_used_change_pins_time_filter = is_used
#         if is_used & filter_interval is not None:
#             self.__filter_interval = filter_interval
#
#     def set_change_pins_time_filter_interval(self, value):
#         self.__filter_interval = value
#
#     # Pins
#     def set_pin_mode(self, pin, mode):
#         super().send_command(Command(ArduinoCommand.TYPE_SET_PIN_MODE, bytes([pin, mode])))
#
#     def set_digital_pin(self, pin, value):
#         super().send_command(Command(ArduinoCommand.TYPE_SET_DIGITAL, bytes([pin, value])))
#
#     def get_digital_pin(self, pin):
#         super().send_command(Command(ArduinoCommand.TYPE_GET_DIGITAL, bytes([pin])))
#
#     def set_analog_pin(self, pin, value):
#         super().send_command(Command(ArduinoCommand.TYPE_SET_ANALOG, bytes([pin, value])))
#
#     # Listeners
#     def add_digital_pin_listener(self, pin, pin_mode=None):
#         if pin_mode is not None:
#             self.set_pin_mode(pin, pin_mode)
#         super().send_command(Command(ArduinoCommand.TYPE_ADD_DIGITAL_LISTENER, bytes([pin])))
#
#     def add_absolute_encoder_listener(self, pins_list):
#         super().send_command(Command(ArduinoCommand.TYPE_ADD_ABSOLUTE_ENCODER_LISTENER, bytes(pins_list)))
#
#     # Motors
#     def add_motor(self, steps_count, step_pin, dir_pin):
#         super().send_command(Command(ArduinoCommand.TYPE_ADD_MOTOR, bytes([steps_count, step_pin, dir_pin])))
#
#     def start_motor(self, index):
#         super().send_command(Command(ArduinoCommand.TYPE_START_MOTOR, bytes([index])))
#
#     def stop_motor(self, index):
#         super().send_command(Command(ArduinoCommand.TYPE_STOP_MOTOR, bytes([index])))
#
#     def motor_rotate_turns(self, index, turns_count):
#         if turns_count > self._MAX_TURNS_COUNT:
#             print("Error. Turns count value must be between 1 and ", self._MAX_TURNS_COUNT)
#             return
#         turns_count_bytes = turns_count.to_bytes(4, byteorder='big')
#         data = bytes([index]) + turns_count_bytes
#         super().send_command(Command(ArduinoCommand.TYPE_MOTOR_ROTATE_TURNS, data))
#
#     def set_motor_direction(self, index, direction):
#         super().send_command(Command(ArduinoCommand.TYPE_SET_MOTOR_DIRECTION, bytes([index, direction])))
#
#     def set_motor_speed(self, index, speed):
#         speed_bytes = speed.to_bytes(4, byteorder='big')
#         data = bytes([index]) + speed_bytes
#         super().send_command(Command(ArduinoCommand.TYPE_SET_MOTOR_SPEED, data))
#
#     # Connection listeners
#     def _dispatch_on_command(self, command):
#         if command.get_type() == Command.TYPE_CONNECT_RESULT:
#             if command.get_integer_data() == 1:
#                 self.__is_confirm_password = True
#                 self._on_connect_event.fire()
#             else:
#                 super()._dispatch_on_error("Authentication error. Password incorrect")
#                 self.close()
#
#         elif command.get_type() == ArduinoCommand.TYPE_DIGITAL_PIN_VALUE:
#             if self.__is_used_change_pins_time_filter:
#
#                 pin = command.get_data()[0]
#                 last_change_time = self.__listeners_list.get(pin)
#                 current_time = time.time() * 1000
#
#                 if last_change_time is not None:
#                     if (current_time - last_change_time) < self.__filter_interval:
#                         return
#
#                 self.__listeners_list[pin] = current_time
#
#                 super()._dispatch_on_command(command)
#
#             else:
#                 super()._dispatch_on_command(command)
#
#         elif command.get_type() == ArduinoCommand.TYPE_ERROR:
#             super()._dispatch_on_error(command.get_string_data())
#             super()._dispatch_on_command(command)
#
#         else:
#             super()._dispatch_on_command(command)
#
#     def _dispatch_on_connect(self):
#         pass
#
#
# class ArduinoCommand:
#
#     # To arduino
#     TYPE_ADD_MOTOR = 0x30
#     TYPE_START_MOTOR = 0x31
#     TYPE_STOP_MOTOR = 0x32
#     TYPE_SET_MOTOR_DIRECTION = 0x33
#     TYPE_SET_MOTOR_SPEED = 0x34
#     TYPE_MOTOR_ROTATE_TURNS = 0x35
#
#     TYPE_ADD_ABSOLUTE_ENCODER_LISTENER = 0x40
#
#     TYPE_SET_ANALOG = 0x50
#     TYPE_SET_DIGITAL = 0x51
#     TYPE_SET_PIN_MODE = 0x52
#
#     TYPE_SERVO_ATTACH = 0x54
#     TYPE_SERVO_ROTATE = 0x55
#     TYPE_SERVO_DETACH = 0x56
#     TYPE_GET_DIGITAL = 0x57
#
#     TYPE_ADD_DIGITAL_LISTENER = 0x58
#
#     TYPE_WATCH_DOG = 0x80
#
#     # From arduino
#
#     TYPE_DIGITAL_PIN_VALUE = 0x71
#     TYPE_ABSOLUTE_ENCODER_ANGLE = 0x72
#
#     # Errors
#     TYPE_ERROR = 0x60
#
#
# import serial
#
# from roboticsnt.commandProtocol.command_protocol import ProtocolConnection
# import serial.tools.list_ports as ports_list
# from serial import SerialException
#
#
# class SerialPortProtocolConnection(ProtocolConnection):
#
#     BAUDRATE_110 = 110
#     BAUDRATE_300 = 300
#     BAUDRATE_600 = 600
#     BAUDRATE_1200 = 1200
#     BAUDRATE_4800 = 4800
#     BAUDRATE_9600 = 9600
#     BAUDRATE_14400 = 14400
#     BAUDRATE_19200 = 19200
#     BAUDRATE_38400 = 38400
#     BAUDRATE_57600 = 57600
#     BAUDRATE_115200 = 115200
#     BAUDRATE_128000 = 128000
#     BAUDRATE_256000 = 256000
#
#     @staticmethod
#     def get_device_list():
#         device_list = []
#         for port in ports_list.comports():
#             # print(port.device)
#             # print(port.name)
#             # print(port.location)
#             # print(port.description)
#             # print(port.hwid)
#             device_list.append(port.device)
#         return device_list
#
#     def __init__(self, port=None, speed=BAUDRATE_115200, auto_connect=False):
#         super().__init__()
#
#         self._is_connected = False
#
#         self.__port = port
#         self.__speed = speed
#         self.__serial_manager = None
#
#         if auto_connect:
#             self.connect()
#
#     def send_command(self, command):
#         if not self._is_connected:
#             raise Exception("You must first connect to the port, and then send commands. Use connect method")
#         try:
#             self.__serial_manager.write(command.get_bytes())
#         except ConnectionError as msg:
#             self._dispatch_on_error(msg)
#         except SerialException as msg:
#             self._dispatch_on_error(msg)
#             self.close()
#
#     def close(self):
#         try:
#             self.__serial_manager.close()
#         except SerialException as msg:
#             super()._dispatch_on_error(msg)
#         else:
#             self._is_connected = False
#             super().close()
#
#     def connect(self, port=None):
#         if self.__port is None and port is None:
#             raise Exception("Protocol connection exception: connection port not received")
#         if port is not None:
#             self.__port = port
#         try:
#             self.__serial_manager = serial.Serial(self.__port, self.__speed, dsrdtr=1, timeout=0)
#         except SerialException as msg:
#             print("SerialException: ", msg)
#             self._dispatch_on_error(msg)
#         except ConnectionError as msg:
#             print("ConnectionError: ", msg)
#             self._dispatch_on_error(msg)
#         else:
#             self._is_connected = True
#             self.start()
#             self._dispatch_on_connect()
#
#     def run(self):
#         while self._is_connected:
#             data = self._read()
#             if data is not None:
#                 # print(type(data))
#                 # print(len(data))
#                 # print("DATA : ", data)
#                 self._parser.parse(data)
#
#     def is_connected(self):
#         return self._is_connected
#
#     def get_port(self):
#         return self.__port
#
#     def _read(self):
#         try:
#             bt = self.__serial_manager.read()
#         except serial.SerialException as msg:
#             self._dispatch_on_error(msg)
#             self.close()
#         else:
#             if bt != '' and len(bt) > 0:
#                 return bt
#             else:
#                 return None
