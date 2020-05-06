import serial.tools.list_ports as ports_list


class SerialPort(object):

    BAUDRATE_110 = 110
    BAUDRATE_300 = 300
    BAUDRATE_600 = 600
    BAUDRATE_1200 = 1200
    BAUDRATE_4800 = 4800
    BAUDRATE_9600 = 9600
    BAUDRATE_14400 = 14400
    BAUDRATE_19200 = 19200
    BAUDRATE_38400 = 38400
    BAUDRATE_57600 = 57600
    BAUDRATE_115200 = 115200
    BAUDRATE_128000 = 128000
    BAUDRATE_256000 = 256000

    @staticmethod
    def get_device_list():
        device_list = []
        for port in ports_list.comports():
            # print(port.device)
            # print(port.name)
            # print(port.location)
            # print(port.description)
            # print(port.hwid)
            device_list.append(port.device)
        return device_list
