import struct
from abc import ABC, abstractmethod
from threading import Thread

from roboticsnt.event import Event


class Command(object):

    TYPE_CONNECT_RESULT = 0x53
    TYPE_CONNECT = 0x70

    START_BYTE_1 = 0x78
    START_BYTE_2 = 0x78
    STOP_BYTE_1 = 0x0D
    STOP_BYTE_2 = 0x0A

    __DEFAULT_INTEGER_BYTES_COUNT = 4
    __DEFAULT_FLOAT_BYTES_COUNT = 8
    __DEFAULT_ENCODING = 'utf-8'

    def __init__(self, command_type, data):
        self.__type = command_type
        self.__data = data

        if type(data) == int:
            self.__data = data.to_bytes(self.__DEFAULT_INTEGER_BYTES_COUNT, byteorder='big')
        elif type(data) == str:
            self.__data = data.encode(self.__DEFAULT_ENCODING)
        elif type(data) == float:
            self.__data = bytearray(struct.pack("f", data))

        packet_len_bytes_count = _Parser.PACKET_LENGTH_BYTES_COUNT
        packet_len = len(self.__data) + 5 + packet_len_bytes_count

        packet_len_bytes = packet_len.to_bytes(packet_len_bytes_count, byteorder='big', signed=True)

        self.__bytes = bytearray(packet_len)
        self.__bytes[0] = self.START_BYTE_1
        self.__bytes[1] = self.START_BYTE_2
        self.__bytes[2:2+packet_len_bytes_count] = packet_len_bytes
        self.__bytes[2+packet_len_bytes_count] = command_type

        index = 2 + packet_len_bytes_count + 1

        for bt in self.__data:
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

    def get_string_data(self, encoding=__DEFAULT_ENCODING):
        return self.__data.decode(encoding)

    def get_integer_data(self, bytes_count=__DEFAULT_INTEGER_BYTES_COUNT, start_byte=0):
        return int.from_bytes(self.__data[start_byte:start_byte+bytes_count], byteorder='big')

    def get_float_data(self, bytes_count=__DEFAULT_FLOAT_BYTES_COUNT, start_byte=0):
        # return struct.unpack('!f', self.__data[start_byte:start_byte+bytes_count])[0]
        # '!f' do not working with Arduino
        return struct.unpack('<f', self.__data[start_byte:start_byte+bytes_count])[0]


class _Parser(object):

    PACKET_LENGTH_BYTES_COUNT = 1

    def __init__(self, buffer_size):

        self.__buffer_size = buffer_size

        self.__buffer = bytearray(buffer_size)
        self.__bytes_in_buffer = 0

        self.on_command_event = Event()

    def parse(self, byte_data) -> None:

        for byte in byte_data:
            # byte = ord(byte)

            if byte == Command.START_BYTE_2 and self.__bytes_in_buffer > 0 \
                    and self.__get_buffer_last_byte() == Command.START_BYTE_1:
                self.__clear_buffer()
                self.__add_to_buffer(Command.START_BYTE_1)
                self.__add_to_buffer(Command.START_BYTE_2)
            elif byte == Command.STOP_BYTE_2 and self.__bytes_in_buffer > 0 \
                    and self.__get_buffer_last_byte() == Command.STOP_BYTE_1:
                self.__add_to_buffer(byte)
                self.__detect_command()
            else:
                self.__add_to_buffer(byte)

    def __detect_command(self) -> None:
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

    def __add_to_buffer(self, bt) -> None:
        if self.__bytes_in_buffer + 1 > self.__buffer_size:
            self.__clear_buffer()
            raise Exception("Parser. Buffer overflow")

        self.__buffer[self.__bytes_in_buffer] = bt
        self.__bytes_in_buffer += 1

    def __clear_buffer(self) -> None:
        self.__buffer = bytearray(self.__buffer_size)
        self.__bytes_in_buffer = 0


class ProtocolConnection(ABC, Thread):

    CONNECT_PASSWORD = "iddqdidkfa"
    # CONNECT_PASSWORD = "incorrect_password_for_tests"
    __DEFAULT_BUFFER_SIZE = 255

    CONNECT_SUCCESSFUL = 1
    CONNECT_ERROR = 0

    def __init__(self, buffer_size: int = __DEFAULT_BUFFER_SIZE):
        super().__init__()
        self._parser = _Parser(buffer_size)

        self._on_command_event = Event()
        self._on_error_event = Event()

        self._parser.on_command_event.handle(self.__on_parser_detect_command)

    # Clear event handlers
    @abstractmethod
    def _clear_event_handlers(self) -> None:
        self._on_command_event.clear_handlers()
        self._on_error_event.clear_handlers()

    @abstractmethod
    def close(self) -> None:
        self._clear_event_handlers()

    # Add Handlers

    def add_on_command_event_handler(self, handler: callable) -> None:
        self._on_command_event.handle(handler)

    def add_on_error_event_handler(self, handler: callable) -> None:
        self._on_error_event.handle(handler)

    def _dispatch_on_command(self, command) -> None:
        self._on_command_event.fire(command)

    def _dispatch_on_error(self, message) -> None:
        self._on_error_event.fire(message)

    # Parser detect command listener
    def __on_parser_detect_command(self, command) -> None:
        self._dispatch_on_command(command)


class ProtocolConnectionClient(ProtocolConnection):

    __next_client_id = 0

    def __init__(self):
        super().__init__()

        self._on_connect_event = Event()
        self._on_disconnect_event = Event()

        self.__id = ProtocolConnectionClient.__next_client_id
        ProtocolConnectionClient.__next_client_id += 1

        self._is_connected = False

    def get_id(self) -> int:
        return self.__id

    def is_connected(self) -> bool:
        return self._is_connected

    def add_on_connect_event_handler(self, handler: callable) -> None:
        self._on_connect_event.handle(handler)

    def add_on_disconnect_event_handler(self, handler: callable) -> None:
        self._on_disconnect_event.handle(handler)

    def _clear_event_handlers(self) -> None:
        super()._clear_event_handlers()
        self._on_connect_event.clear_handlers()
        self._on_disconnect_event.clear_handlers()

    @abstractmethod
    def send_command(self, command: Command) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        self._is_connected = False
        super().close()

    def _dispatch_on_connect(self) -> None:
        self._is_connected = True
        self._on_connect_event.fire()

    def _dispatch_on_disconnect(self) -> None:
        self._on_disconnect_event.fire()

    def _send_try_connect_command(self) -> None:
        self.send_command(Command(Command.TYPE_CONNECT, ProtocolConnection.CONNECT_PASSWORD.encode('utf-8')))


class ProtocolConnectionServer(ABC, Thread):

    def __init__(self):
        super().__init__()

        self.__on_client_connect_event = Event()
        self.__on_client_disconnect_event = Event()
        self.__on_client_command_event = Event()
        self.__on_client_error_event = Event()

        self.__on_server_stopped_event = Event()

    @abstractmethod
    def stop(self) -> None:
        self._dispatch_on_server_stopped()
        self._clear_event_handlers()

    def add_on_server_stopped_event(self, handler: callable):
        self.__on_server_stopped_event.handle(handler)

    def add_on_client_connect_event_handler(self, handler: callable):
        self.__on_client_connect_event.handle(handler)

    def add_on_client_disconnect_event_handler(self, handler: callable):
        self.__on_client_disconnect_event.handle(handler)

    def add_on_command_event_handler(self, handler: callable):
        self.__on_client_command_event.handle(handler)

    def add_on_error_event_handler(self, handler: callable):
        self.__on_client_error_event.handle(handler)

    def _clear_event_handlers(self) -> None:
        self.__on_client_connect_event.clear_handlers()
        self.__on_client_disconnect_event.clear_handlers()

    @abstractmethod
    def send_command(self, command: Command, client_id: int):
        pass

    def _dispatch_on_server_stopped(self):
        self.__on_server_stopped_event.fire()

    def _dispatch_on_client_connect(self, client_id):
        self.__on_client_connect_event.fire(client_id)

    def _dispatch_on_client_disconnect(self, client_id):
        self.__on_client_disconnect_event.fire(client_id)

    def _dispatch_on_command(self, client_id: int, command: Command):
        self.__on_client_command_event.fire(client_id, command)

    def _dispatch_on_error(self, client_id: int, message: str):
        self.__on_client_error_event.fire(client_id, message)
