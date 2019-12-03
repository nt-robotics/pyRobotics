import socket
from roboticsnt.commandProtocol.command_protocol import Command, ProtocolConnectionClient, \
    ProtocolConnectionServer, ProtocolConnection


# Socket clients base class

class CommandProtocolSocketClientBase(ProtocolConnectionClient):

    __RECEIVE_BYTES = 1024

    def __init__(self, socket_connection, ip: str, port: int):
        super().__init__()

        self._socket_connection = socket_connection
        self._ip = ip
        self._port = port

        self.__is_started = False

    def get_ip_address(self) -> str:
        return self._ip

    def get_port(self) -> int:
        return self._port

    def run(self) -> None:
        self.__is_started = True
        with self._socket_connection:
            while self.__is_started:
                data = self._socket_connection.recv(self.__RECEIVE_BYTES)
                if not data:
                    self.close()
                    break
                self._parser.parse(data)

    def send_command(self, command: Command) -> None:
        self._socket_connection.sendall(command.get_bytes())

    def close(self) -> None:
        self._socket_connection.close()
        self.__is_started = False
        self._dispatch_on_disconnect()
        super().close()


# CLIENT

class CommandProtocolSocketClient(CommandProtocolSocketClientBase):

    def __init__(self, ip: str = None, port: int = None, auto_connect: bool = False):
        socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        super().__init__(socket_connection, ip, port)

        if auto_connect:
            self.connect()

    def connect(self, ip=None, port=None):
        if ip is not None:
            self._ip = ip
        if port is not None:
            self._port = port
        if self._port is None or self._ip is None:
            error_mes = "Protocol connection exception: ip address or connection port not received"
            # super()._dispatch_on_error(error_mes)
            raise Exception(error_mes)

        self._socket_connection.connect((self._ip, self._port))
        self.start()
        self._send_try_connect_command()

    def _dispatch_on_command(self, command):
        if command.get_type() == Command.TYPE_CONNECT_RESULT:
            if command.get_integer_data() == ProtocolConnection.CONNECT_SUCCESSFUL:
                self._dispatch_on_connect()
            else:
                super()._dispatch_on_error("Authentication error. Password incorrect")
                self.close()
        else:
            super()._dispatch_on_command(command)


# SERVER

# Socket server socket_connection class

class _Client(CommandProtocolSocketClientBase):

    def __init__(self, connection, address):
        super().__init__(connection, address[0], address[1])

    def _send_connect_result_command(self, connect_result: int):
        self.send_command(Command(Command.TYPE_CONNECT_RESULT, connect_result))

    def _dispatch_on_connect(self) -> None:
        self._is_connected = True
        self._on_connect_event.fire(self)

    def _dispatch_on_disconnect(self) -> None:
        self._is_connected = False
        self._on_disconnect_event.fire(self)

    def _dispatch_on_command(self, command: Command) -> None:
        if command.get_type() == Command.TYPE_CONNECT:
            if command.get_string_data() == ProtocolConnection.CONNECT_PASSWORD:
                self._send_connect_result_command(ProtocolConnection.CONNECT_SUCCESSFUL)
                self._dispatch_on_connect()
            else:
                self._send_connect_result_command(ProtocolConnection.CONNECT_ERROR)
                self._dispatch_on_error("Authentication error. Password incorrect")
                self.close()
        else:
            self._on_command_event.fire(self, command)

    def _dispatch_on_error(self, message) -> None:
        self._on_error_event.fire(self, message)


class CommandProtocolSocketServer(ProtocolConnectionServer):

    def __init__(self, port):
        super().__init__()
        server_address = ('', port)

        self.__is_thread_started = False
        self.__clients_list: [_Client] = []

        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.bind(server_address)
        self.__server_socket.listen(socket.SOMAXCONN)

    def get_clients_list(self) -> [_Client]:
        return self.__clients_list

    def get_client_by_id(self, client_id: int) -> _Client or None:
        for client in self.__clients_list:
            if client.get_id() == client_id:
                return client
        return None

    def close_client(self, client_id):
        client: _Client = self.get_client_by_id(client_id)
        client.close()

    def run(self) -> None:
        self.__is_thread_started = True

        with self.__server_socket:
            while self.__is_thread_started:
                connection, address = self.__server_socket.accept()
                client = _Client(connection, address)
                self.__clients_list.append(client)
                client.add_on_connect_event_handler(self._on_client_connect)
                client.add_on_disconnect_event_handler(self._on_client_disconnect)
                client.add_on_command_event_handler(self._on_client_command)
                client.add_on_error_event_handler(self._on_client_error)
                client.start()

    def send_command(self, command: Command, client_id: int):
        client: _Client = self.get_client_by_id(client_id)
        client.send_command(command)

    def send_command_to_all(self, command: Command):
        for client in self.__clients_list:
            client.send(command)

    def stop(self):
        self.__is_thread_started = False
        for client in self.__clients_list:
            print(client.get_id())
            client.close()
        # if platform.system() == 'Linux':
        #     print("SHUTDOWN")
        #     self.__server_socket.shutdown(socket.SHUT_RDWR)
        self.__server_socket.close()

        super().stop()

    def _on_client_connect(self, client: _Client):
        self._dispatch_on_client_connect(client.get_id())

    def _on_client_disconnect(self, client: _Client):
        self._dispatch_on_client_disconnect(client.get_id())

    def _on_client_command(self, client: _Client, command: Command):
        self._dispatch_on_command(client.get_id(), command)

    def _on_client_error(self, client: _Client, message: str):
        self._dispatch_on_error(client.get_id(), message)
