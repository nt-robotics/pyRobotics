from roboticsnt.commandProtocol.command_protocol import Command
from roboticsnt.commandProtocol.socket.command_protocol_socket import CommandProtocolSocketClient

FLOAT_DATA_TYPE = 61
INTEGER_DATA_TYPE = 62
STRING_DATA_TYPE = 63


def on_connect():
    print("Connected to server")
    socket_connection.send_command(Command(STRING_DATA_TYPE, "Hello, server!!!"))


def on_disconnect():
    print("Disconnected")


def on_error(message):
    print("ERROR: ", message)


def on_command(command: Command):
    data = None

    if command.get_type() == STRING_DATA_TYPE:
        data = command.get_string_data()
    elif command.get_type() == FLOAT_DATA_TYPE:
        data = command.get_float_data()
    elif command.get_type() == INTEGER_DATA_TYPE:
        data = command.get_integer_data()

    print("New Command: TYPE:", command.get_type(), "    DATA:", data)


if __name__ == '__main__':
    print("=============================================================")
    print("=================== START APPLICATION =======================")
    print("=============================================================")

    socket_connection = CommandProtocolSocketClient('localhost', 8888)
    socket_connection.add_on_connect_event_handler(on_connect)
    socket_connection.add_on_disconnect_event_handler(on_disconnect)
    socket_connection.add_on_error_event_handler(on_error)
    socket_connection.add_on_command_event_handler(on_command)

    socket_connection.connect()
