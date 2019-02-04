import time

import serial.tools.list_ports

from roboticsnt.commandProtocol.arduino.arduino_connection import ArduinoConnection, ArduinoCommand
from roboticsnt.serial.serial_port import SerialPort


def connect_handler():

    print("Device connected to serial port")

    #  ================= DIGITAL PINS ================

    # pin = 13
    #
    # connection.set_pin_mode(pin, ArduinoConnection.PIN_MODE_OUTPUT)
    #
    # time.sleep(1)
    # connection.set_digital_pin(pin, ArduinoConnection.LOW)
    # time.sleep(1)
    # connection.set_digital_pin(pin, ArduinoConnection.HIGH)
    # time.sleep(1)
    # connection.set_digital_pin(pin, ArduinoConnection.LOW)
    # time.sleep(1)
    # connection.set_digital_pin(pin, ArduinoConnection.HIGH)
    # time.sleep(1)
    # connection.set_digital_pin(pin, ArduinoConnection.LOW)
    # time.sleep(1)
    # connection.set_digital_pin(pin, ArduinoConnection.HIGH)
    # time.sleep(1)
    # connection.set_digital_pin(pin, ArduinoConnection.LOW)
    # time.sleep(1)
    # connection.set_digital_pin(pin, ArduinoConnection.HIGH)
    # time.sleep(1)

    # pins_list = [33, 27, 23, 25, 31, 35, 37, 29, 45, 49, 41, 43, 39, 47, 53, 51, 24, 26, 22, 28]
    # for i in pins_list:
    #     connection.set_pin_mode(i, ArduinoConnection.PIN_MODE_OUTPUT)
    #     connection.set_digital_pin(i, ArduinoConnection.HIGH)

    # while connection.is_connected():
    #     for i in pins_list:
    #         connection.set_digital_pin(i, ArduinoConnection.LOW)
    #         time.sleep(0.5)
    #
    #     for i in pins_list:
    #         connection.set_digital_pin(i, ArduinoConnection.HIGH)
    #         time.sleep(0.5)

    # connection.add_digital_pin_listener(13, ArduinoConnection.PIN_MODE_INPUT_PULLUP)
    # connection.add_digital_pin_listener(32, ArduinoConnection.PIN_MODE_INPUT_PULLUP)
    # connection.add_digital_pin_listener(30, ArduinoConnection.PIN_MODE_INPUT_PULLUP)
    # connection.add_digital_pin_listener(28, ArduinoConnection.PIN_MODE_INPUT_PULLUP)

    # connection.get_digital_pin(pin)

    #  ================= ABSOLUTE ENCODER ================

    # pins_list = [28, 30, 32, 34, 36, 38, 40, 42, 44, 46]
    # connection.add_absolute_encoder_listener(pins_list)

    #  ================= GECKODRIVE STEPPER MOTOR ================

    time.sleep(1)

    motor_index = 0

    connection.add_motor(200, 10, 11)

    connection.set_motor_speed(motor_index, 200)

    connection.motor_rotate_turns(motor_index, 20)
    time.sleep(10)
    # connection.motor_rotate_turns(motor_index, 20)
    # connection.stop_motor(motor_index)
    connection.set_motor_direction(motor_index, ArduinoConnection.MOTOR_DIRECTION_CLOCKWISE)
    print("2")
    connection.motor_rotate_turns(motor_index, 6)
    time.sleep(8)

    # connection.set_motor_direction(motor_index, ArduinoConnection.MOTOR_DIRECTION_BACKWARD)
    # time.sleep(6)
    # connection.set_motor_direction(motor_index, ArduinoConnection.MOTOR_DIRECTION_FORWARD)
    # time.sleep(6)
    # connection.set_motor_direction(motor_index, ArduinoConnection.MOTOR_DIRECTION_BACKWARD)
    # time.sleep(6)

    connection.stop_motor(motor_index)

    # connection.start_motor(motor_index)
    # print("Speed:", 1000)
    # connection.set_motor_speed(motor_index, 1000)
    # time.sleep(4)
    # print("Speed:", 2000)
    # connection.set_motor_speed(motor_index, 2000)
    # time.sleep(4)
    # print("Speed:", 3000)
    # connection.set_motor_speed(motor_index, 3000)
    # time.sleep(4)
    # print("Speed:", 4000)
    # connection.set_motor_speed(motor_index, 4000)
    # time.sleep(4)
    # print("Speed:", 5000)
    # connection.set_motor_speed(motor_index, 5000)
    # time.sleep(4)
    # print("Speed:", 6000)
    # connection.set_motor_speed(motor_index, 6000)
    # time.sleep(4)
    # print("Speed:", 7000)
    # connection.set_motor_speed(motor_index, 7000)
    # time.sleep(4)
    # print("Speed:", 8000)
    # connection.set_motor_speed(motor_index, 8000)
    # time.sleep(2)
    # print("Speed:", 9000)
    # connection.set_motor_speed(motor_index, 9000)
    # time.sleep(2)
    # print("Speed:", 9500)
    # connection.set_motor_speed(motor_index, 9500)

    # connection.start_motor(motor_index)
    # time.sleep(3)
    # connection.set_motor_direction(motor_index, ArduinoConnection.MOTOR_DIRECTION_BACKWARD)
    # time.sleep(3)
    # connection.set_motor_direction(motor_index, ArduinoConnection.MOTOR_DIRECTION_FORWARD)
    # time.sleep(3)
    # connection.stop_motor(motor_index)
    # time.sleep(3)

    # ============= SET ANALOG ===================

    # time.sleep(1)
    # connection.set_analog_pin(pin, 10)
    # time.sleep(1)
    # connection.set_analog_pin(pin, 50)
    # time.sleep(1)
    # connection.set_analog_pin(pin, 100)
    # time.sleep(1)
    # connection.set_analog_pin(pin, 150)
    # time.sleep(1)
    # connection.set_analog_pin(pin, 200)

    connection.close()


def disconnect_handler():
    print("Serial port connection closed")


def command_handler(command):
    # print("NEW COMMAND!!!")
    # print(command.get_data()[0])
    # print(command.get_data()[1])
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


def error_handler(message):
    print("Error. Message: ", message)


port = SerialPort.get_device_list()[0]
print(port)

connection = ArduinoConnection()

connection.add_on_connect_event_handler(connect_handler)
connection.add_on_disconnect_event_handler(disconnect_handler)
connection.add_on_command_event_handler(command_handler)
connection.add_on_error_event_handler(error_handler)

connection.connect(port)
