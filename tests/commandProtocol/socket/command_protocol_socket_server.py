from roboticsnt.commandProtocol.command_protocol import Command
from roboticsnt.commandProtocol.socket.command_protocol_socket import CommandProtocolSocketServer

FLOAT_DATA_TYPE = 61
INTEGER_DATA_TYPE = 62
STRING_DATA_TYPE = 63


def on_client_connect(client_id):
    print("New socket_connection connect", "ID: ", client_id)

    command = Command(STRING_DATA_TYPE, "Hello client!!!")
    server.send_command(command, client_id)

    command = Command(FLOAT_DATA_TYPE, 12.67)
    server.send_command(command, client_id)

    # Send integer data
    command = Command(INTEGER_DATA_TYPE, 643)
    server.send_command(command, client_id)

    # Send string data
    command = Command(STRING_DATA_TYPE, "String data")
    server.send_command(command, client_id)


def on_client_disconnect(client_id):
    print("Client disconnect", "ID: ", client_id)


def on_command(client_id, command: Command):
    data = None

    if command.get_type() == STRING_DATA_TYPE:
        data = command.get_string_data()
    elif command.get_type() == FLOAT_DATA_TYPE:
        data = command.get_float_data()
    elif command.get_type() == INTEGER_DATA_TYPE:
        data = command.get_integer_data()

    print("New Command: CLIENT_ID: ", client_id, "   TYPE:", command.get_type(), "    DATA:", data)

    if client_id == 1:
        server.close_client(0)
        server.close_client(1)


def on_error(client_id, message):
    print("Error: ", message)


if __name__ == '__main__':
    server = CommandProtocolSocketServer(8888)

    server.add_on_client_connect_event_handler(on_client_connect)
    server.add_on_client_disconnect_event_handler(on_client_disconnect)
    server.add_on_command_event_handler(on_command)
    server.add_on_error_event_handler(on_error)
    server.start()
    print("SERVER START")
