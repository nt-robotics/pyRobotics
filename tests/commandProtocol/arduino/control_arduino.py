import time
from threading import Thread

from roboticsnt.commandProtocol.arduino.arduino_connection import ArduinoConnection, ArduinoCommand
from roboticsnt.serial.serial_port import SerialPort


class ControlArduinoThread(Thread):

    def __init__(self):
        super().__init__()

        port = SerialPort.get_device_list()[0]
        print(port)

        self.connection = ArduinoConnection()

        self.connection.add_on_connect_event_handler(self.connect_handler)
        self.connection.add_on_disconnect_event_handler(self.disconnect_handler)
        self.connection.add_on_command_event_handler(self.command_handler)
        self.connection.add_on_error_event_handler(self.error_handler)

        self.connection.connect(port)
        # self.connection.set_motor_speed(0, 600)

    def run(self):
        while self.connection.is_connected():

            # self.test_stepper_motor()
            self.test_digital_pins()

            self.connection.close()

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

    def error_handler(self, message):
        print("Error. Message: ", message)

    def disconnect_handler(self):
        print("Disconnected")

    def test_stepper_motor(self):
        time.sleep(1)

        motor_index = 0

        self.connection.add_motor(200, 10, 11)

        self.connection.set_motor_speed(motor_index, 200)

        self.connection.motor_rotate_turns(motor_index, 50)
        time.sleep(20)
        self.connection.set_motor_direction(motor_index, ArduinoConnection.MOTOR_DIRECTION_CLOCKWISE)
        self.connection.motor_rotate_turns(motor_index, 6)
        # connection.stop_motor(motor_index)
        time.sleep(5)

    def test_digital_pins(self):
        pin = 13
        self.connection.set_pin_mode(pin, ArduinoConnection.PIN_MODE_OUTPUT)

        time.sleep(1)
        self.connection.set_digital_pin(pin, ArduinoConnection.LOW)
        time.sleep(1)
        self.connection.set_digital_pin(pin, ArduinoConnection.HIGH)
        time.sleep(1)
        self.connection.set_digital_pin(pin, ArduinoConnection.LOW)
        time.sleep(1)
        self.connection.set_digital_pin(pin, ArduinoConnection.HIGH)

    def test_analog_pins(self):
        pin = 11
        self.connection.set_analog_pin(pin, 10)
        time.sleep(1)
        self.connection.set_analog_pin(pin, 50)
        time.sleep(1)
        self.connection.set_analog_pin(pin, 100)
        time.sleep(1)
        self.connection.set_analog_pin(pin, 150)
        time.sleep(1)
        self.connection.set_analog_pin(pin, 200)
        time.sleep(1)

    def test_digital_listeners(self):
        self.connection.add_digital_pin_listener(13, ArduinoConnection.PIN_MODE_INPUT_PULLUP)
        self.connection.add_digital_pin_listener(32, ArduinoConnection.PIN_MODE_INPUT_PULLUP)
        self.connection.add_digital_pin_listener(30, ArduinoConnection.PIN_MODE_INPUT_PULLUP)
        self.connection.add_digital_pin_listener(28, ArduinoConnection.PIN_MODE_INPUT_PULLUP)

    def test_absolute_encoder(self):
        pins_list = [28, 30, 32, 34, 36, 38, 40, 42, 44, 46]
        self.connection.add_absolute_encoder_listener(pins_list)


ControlArduinoThread()

