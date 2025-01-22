from http import server
import json
import socket
import sys
import threading
import uuid

import global_variables
import broadcast

# Listening ports for all sockets
TCP_PORT = 10005
BROADCAST_PORT_AUCTION = 58002

DYNAMIC_DISCOVERY_BROADCAST_IP = "255.255.255.255"
BROADCAST_PORT = 5973

# Messages for identification
BROADCAST_MESSAGE = 'Could I join the Chatroom?'
BROADCAST_ANSWER_SERVER = 'Welcome'

# Local host information
MY_HOST = socket.gethostname()
c_address = socket.gethostbyname(MY_HOST)
client_uuid = str(uuid.uuid4())

# message definitions
CLIENT_DISCOVERY_MESSAGE = {
    "type": "client_discovery",
    "client_server_uuid": client_uuid,
    "client_address": c_address,
    "message": "I want to join the auction"
}

# Broadcasts that this client is looking for a server
# This shouts into the void until a server is found


def broadcast_sender():
    # Create a UDP socket
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Broadcast message of type: ", CLIENT_DISCOVERY_MESSAGE['type'])
    broadcast_socket.sendto(json.dumps(CLIENT_DISCOVERY_MESSAGE).encode(
    ), (DYNAMIC_DISCOVERY_BROADCAST_IP, BROADCAST_PORT))

    # if the broadcast message sent is a discovery message wait for a response
    broadcast_socket.settimeout(2)

    try:
        # Wait for a response
        data, addr = broadcast_socket.recvfrom(1024)
        response = json.loads(data.decode())

        global server_data
        server_data = {
            "server_address": response.get("server_address"),
            "server_uuid": response.get("server_uuid")
        }

    except socket.timeout:
        # no server is responding
        print("No servers found.")


def handling_messages():
    # Wait for user input
    while True:
        if (global_variables.is_auction_active):
            user_input = input("Your bid to the element: \n")

            try:
                # only integers are taken from the user
                user_input = int(user_input)  # convert input to integer
            except ValueError:
                print(f"You need to make a bid!")
                continue
        else:
            user_input = input("Choose a new bid element: \n")

        if len(user_input) > 1024 / 10:
            print('Input is too long')
            continue
        # Send message to server
        else:
            message_to_server(user_input)


# Sends a message to the server
# If the server isn't there, the client starts searching again
def message_to_server(bid):
    bid = str.encode(
        json.dumps(
            {
                "client_uuid": client_uuid,
                "bid": bid
            }
        )
    )

    try:
        # Create a TCP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the server
        client_socket.connect((server_data.get("server_address"), TCP_PORT))
        # Set the socket to be non-blocking
        client_socket.setblocking(False)
        # Send the bid
        client_socket.send(bid)
        # Close the socket
        client_socket.close()

    except (ConnectionRefusedError, TimeoutError):
        # Handling connection errors
        print('\rError - searching for server again')
        broadcast_sender()


def broadcast_listener():
    # Create a socket for listening to broadcast messages
    b_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Enable the socket to receive broadcast messages
    b_listener.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        # Bind the socket to the broadcast port for chat
        b_listener.bind(("", BROADCAST_PORT_AUCTION))

    except:
        pass

    while True:
        try:
            # Receive data and address from the broadcast
            data, address = b_listener.recvfrom(1024)
            data = json.dumps(data).encode()

            if (data.get("type") == "bid_update"):
                print("New bid for '", data.get(
                    "element_name", "' is ", data.get("highest_bid")))
            elif (data.get("type") == "new_bid_element"):
                print("New auction started for the following element: ",
                      data.get("element_name"))

        except TimeoutError:
            pass


if __name__ == '__main__':
    # Start the broadcast sender
    broadcast_sender()
    # Create a thread for the broadcast listener
    threadBL = threading.Thread(target=broadcast_listener)
    # Start the broadcast listener thread
    threadBL.start()

    if (server_data.get("server_address") != None):
        # Create a thread for handling messages
        threadHM = threading.Thread(target=handling_messages)
        # Start the handling messages thread
        threadHM.start()
