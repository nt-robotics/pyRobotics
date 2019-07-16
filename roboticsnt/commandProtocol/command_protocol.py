import struct
from threading import Thread

from roboticsnt.event import Event


class ProtocolConnection(Thread):

    CONNECT_PASSWORD = "iddqdidkfa"
    # CONNECT_PASSWORD = "incorrect_password_for_tests"
    __DEFAULT_BUFFER_SIZE = 255

    def __init__(self, buffer_size=__DEFAULT_BUFFER_SIZE):
        super().__init__()
        self._parser = _Parser(buffer_size)

        self.__on_connect_event = Event()
        self.__on_disconnect_event = Event()
        self.__on_command_event = Event()
        self.__on_error_event = Event()

        self._parser.on_command_event.handle(self.__on_parser_detect_command)

    # Clear event handlers
    def clear_event_handlers(self):
        self.__on_connect_event.clear_handlers()
        self.__on_disconnect_event.clear_handlers()
        self.__on_command_event.clear_handlers()
        self.__on_error_event.clear_handlers()

    # Add Handlers

    def add_on_connect_event_handler(self, handler):
        self.__on_connect_event.handle(handler)

    def add_on_disconnect_event_handler(self, handler):
        self.__on_disconnect_event.handle(handler)

    def add_on_error_event_handler(self, handler):
        self.__on_error_event.handle(handler)

    def add_on_command_event_handler(self, handler):
        self.__on_command_event.handle(handler)

    # Dispatch events
    def _dispatch_on_connect(self):
        self.__on_connect_event.fire()

    def _dispatch_on_disconnect(self):
        self.__on_disconnect_event.fire()

    def _dispatch_on_command(self, command):
        self.__on_command_event.fire(command)

    def _dispatch_on_error(self, message):
        self.__on_error_event.fire(message)

    # Parser detect command listener
    def __on_parser_detect_command(self, command):
        self._dispatch_on_command(command)


class _Parser(object):

    PACKET_LENGTH_BYTES_COUNT = 1

    def __init__(self, buffer_size):

        self.__buffer_size = buffer_size

        self.__buffer = bytearray(buffer_size)
        self.__bytes_in_buffer = 0

        self.on_command_event = Event()

    def parse(self, byte_data):
        int_data = ord(byte_data)

        if int_data == Command.START_BYTE_2 and self.__bytes_in_buffer > 0 \
                and self.__get_buffer_last_byte() == Command.START_BYTE_1:
            self.__clear_buffer()
            self.__add_to_buffer(Command.START_BYTE_1)
            self.__add_to_buffer(Command.START_BYTE_2)
        elif int_data == Command.STOP_BYTE_2 and self.__bytes_in_buffer > 0 \
                and self.__get_buffer_last_byte() == Command.STOP_BYTE_1:
            self.__add_to_buffer(int_data)
            self.__detect_command()
        else:
            self.__add_to_buffer(int_data)

    def __detect_command(self):
        start1 = self.__buffer[0]
        start2 = self.__buffer[1]

        packet_length_bytes_count = _Parser.PACKET_LENGTH_BYTES_COUNT

        if packet_length_bytes_count == 1:
            packet_length = self.__buffer[2]
        else:
            packet_length = int.from_bytes(self.__buffer[2:2 + packet_length_bytes_count], byteorder='big')

        stop1 = self.__buffer[self.__bytes_in_buffer - 2]
        stop2 = self.__buffer[self.__bytes_in_buffer - 1]

        if start1 == Command.START_BYTE_1 and start2 == Command.START_BYTE_2 and stop1 == Command.STOP_BYTE_1 and \
                stop2 == Command.STOP_BYTE_2 and packet_length == self.__bytes_in_buffer:

            command_type = self.__buffer[2+packet_length_bytes_count]

            command_data = self.__buffer[3+packet_length_bytes_count:packet_length-2]

            command = Command(command_type, command_data)
            self.on_command_event.fire(command)
        else:
            print("Command protocol parser. Bad command!!!")
            self.__clear_buffer()

    def __get_buffer_last_byte(self):
        return self.__buffer[self.__bytes_in_buffer - 1]

    def __add_to_buffer(self, bt):
        if self.__bytes_in_buffer + 1 > self.__buffer_size:
            self.__clear_buffer()
            raise Exception("Parser. Buffer overflow")

        self.__buffer[self.__bytes_in_buffer] = bt
        self.__bytes_in_buffer += 1

    def __clear_buffer(self):
        self.__buffer = bytearray(self.__buffer_size)
        self.__bytes_in_buffer = 0


class Command(object):

    TYPE_CONNECT_RESULT = 0x53
    TYPE_CONNECT = 0x70

    START_BYTE_1 = 0x78
    START_BYTE_2 = 0x78
    STOP_BYTE_1 = 0x0D
    STOP_BYTE_2 = 0x0A

    def __init__(self, command_type, data):
        self.__type = command_type
        self.__data = data

        packet_len_bytes_count = _Parser.PACKET_LENGTH_BYTES_COUNT
        packet_len = len(data) + 5 + packet_len_bytes_count

        packet_len_bytes = packet_len.to_bytes(packet_len_bytes_count, byteorder='big', signed=True)

        self.__bytes = bytearray(packet_len)
        self.__bytes[0] = self.START_BYTE_1
        self.__bytes[1] = self.START_BYTE_2
        self.__bytes[2:2+packet_len_bytes_count] = packet_len_bytes
        self.__bytes[2+packet_len_bytes_count] = command_type

        index = 2 + packet_len_bytes_count + 1

        for bt in data:
            self.__bytes[index] = bt
            index += 1

        self.__bytes[index] = self.STOP_BYTE_1
        self.__bytes[index + 1] = self.STOP_BYTE_2

    def get_type(self):
        return self.__type

    def get_bytes(self):
        return self.__bytes

    def get_data(self):
        return self.__data

    def get_string_data(self, encoding="utf-8"):
        return self.__data.decode(encoding)

    def get_integer_data(self, bytes_count=4, start_byte=0):
        return int.from_bytes(self.__data[start_byte:start_byte+bytes_count], byteorder='big')

    def get_float_data(self, bytes_count=8, start_byte=0):
        # return struct.unpack('!f', self.__data[start_byte:start_byte+bytes_count])[0]
        # '!f' do not working with Arduino
        return struct.unpack('<f', self.__data[start_byte:start_byte+bytes_count])[0]
