import time
from threading import Thread

from roboticsnt.commandProtocol.arduino.arduino_controllers import ArduinoCommand, ArduinoGeckoDriveG540Controller
from roboticsnt.serial.serial_port import SerialPort


class ControlMotorThread(Thread):

    def __init__(self):
        super().__init__()

        port = SerialPort.get_device_list()[0]
        print(port)

        self.connection = ArduinoGeckoDriveG540Controller(port)

        self.connection.add_on_connect_event_handler(self.connect_handler)
        self.connection.add_on_disconnect_event_handler(self.disconnect_handler)
        self.connection.add_on_command_event_handler(self.command_handler)
        self.connection.add_on_error_event_handler(self.error_handler)

        self.connection.connect()

    def run(self):
        self.connection.add_motor(200, 6, 7)
        self.connection.set_motor_speed(0, 800)
        self.connection.motor_rotate_turns(0, 200)

        # time.sleep(5)
        # print(100)
        # self.connection.set_motor_speed(0, 100)
        # time.sleep(5)
        # print(200)
        # self.connection.set_motor_speed(0, 200)
        # time.sleep(5)
        # print(300)
        # self.connection.set_motor_speed(0, 300)
        # time.sleep(5)
        # print(400)
        # self.connection.set_motor_speed(0, 350)

        time.sleep(30)
        self.connection.close()

        # connection.set_motor_speed(0, 4000)
        # connection.motor_rotate_turns(0, 10)

    def connect_handler(self):
        print("Device connected to serial port")

        self.start()

    def command_handler(self, command):
        print("New command, type: ", command.get_type())

        if command.get_type() == ArduinoCommand.TYPE_ABSOLUTE_ENCODER_ANGLE:
            # print("Integer data ", command.get_integer_data(1))
            # print("Integer data ", command.get_data()[0])
            # print("Float data ", command.get_float_data(4, 1))
            # print("Angle change : ")
            # print(command.get_integer_data(1, 4))
            print(command.get_float_data(4, 0))

        elif command.get_type() == ArduinoCommand.TYPE_DIGITAL_PIN_VALUE:
            print("DIGITAL PIN VALUE CHANGE")
            print(command.get_integer_data(1, 0))
            print(command.get_integer_data(1, 1))
        # elif command.get_type() == ArduinoCommand.TYPE_MOTOR_STATE:
        #     print("Motor state command")
        #     print("Motor index - ", command.get_integer_data(1, 0))
        #     print("Motor state - ", command.get_integer_data(1, 1))
        #
        #     state = command.get_integer_data(1, 1)
        #
        #     if state == ArduinoConnection.MOTOR_STATE_STOPPED:
        #
        #         if self._motor_direction == ArduinoConnection.MOTOR_DIRECTION_COUNTERCLOCKWISE:
        #             self._motor_direction = ArduinoConnection.MOTOR_DIRECTION_CLOCKWISE
        #             self.connection.set_motor_direction(0, ArduinoConnection.MOTOR_DIRECTION_CLOCKWISE)
        #         else:
        #             self._motor_direction = ArduinoConnection.MOTOR_DIRECTION_COUNTERCLOCKWISE
        #             self.connection.set_motor_direction(0, ArduinoConnection.MOTOR_DIRECTION_COUNTERCLOCKWISE)
        #
        #         self.connection.motor_rotate_turns(0, 12)

    def error_handler(self, message):
        print("Error. Message: ", message)

    def disconnect_handler(self):
        print("Disconnected")






ControlMotorThread()
