from roboticsnt.commandProtocol.arduino.arduino_devices import EncoderSpeedometer
from roboticsnt.serial.serial_port import SerialPort


def _on_connect():
    print("Speedometer connected")


def _on_speed_change(value):
    print("Speed100: ", value)
    # pass


def _on_disconnect():
    print("Speedometer disconnected")


def _on_error(message):
    print("Error | ", message)


port = SerialPort.get_device_list()[0]
pins_list = [12, 11, 10, 9, 8, 7, 6, 5, 4, 3]


# # 1
# speedometer = EncoderSpeedometer(pins_list)
# speedometer.create_connection()
# speedometer.set_speed_change_handler(_on_speed_change)
# speedometer.add_on_connect_event_handler(_on_connect)
# speedometer.add_on_disconnect_event_handler(_on_disconnect)
# speedometer.add_on_error_event_handler(_on_error)
# speedometer.connect(port)
# 2
speedometer = EncoderSpeedometer(pins_list, port)
speedometer.create_connection()
speedometer.set_speed_change_handler(_on_speed_change)
speedometer.add_on_connect_event_handler(_on_connect)
speedometer.add_on_disconnect_event_handler(_on_disconnect)
speedometer.add_on_error_event_handler(_on_error)
speedometer.connect()


