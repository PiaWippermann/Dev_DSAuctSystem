"""
client.py

File that is run to start a client.
Dynamic discovery of hosts for a client is implemented as well as handling the user input.
Interaction with the user depends on the current status of the auction.

- broadcast sender for dynamic discovery of hosts
- user handler

"""

import json
import socket
import threading
import time

import global_variables
import auction_handler

# Listening ports for all sockets
TCP_PORT = 10005
BROADCAST_PORT_AUCTION = 58002

DYNAMIC_DISCOVERY_BROADCAST_IP = "255.255.255.255"
BROADCAST_PORT = 5973

server_data = None


def broadcast_sender():
    """
    Broadcast is sent to all servers.
    Waiting for a response from the leader server.
    Repeats this process until the client is included in the system

    """
    global server_data
    server_data = None

    client_discovery_message = {
        "type": "client_discovery"
    }

    # Create a UDP socket
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print(
        f"Client sends broadcast message of type: {client_discovery_message['type']} \n")
    broadcast_socket.sendto(json.dumps(client_discovery_message).encode(
    ), (DYNAMIC_DISCOVERY_BROADCAST_IP, BROADCAST_PORT))

    # if the broadcast message sent is a discovery message wait for a response
    broadcast_socket.settimeout(2)

    try:
        # Wait for a response
        data, addr = broadcast_socket.recvfrom(1024)
        response = json.loads(data.decode())

        server_data = {
            "server_address": response.get("server_address"),
            "server_uuid": response.get("server_uuid")
        }

        global_variables.is_auction_active = response.get("is_auction_active")
        global_variables.active_auction_element = response.get(
            "active_auction_element")

        # Create a thread for handling messages
        threadMessages = threading.Thread(target=handling_messages)
        # Start the handling messages thread
        threadMessages.start()

        print("\n" + "=" * 50)
        print("### CLIENT SETUP DONE, SERVER FOUND ###")
        print("=" * 50)

    except socket.timeout:
        # no server is responding
        print("\n### NO SERVERS FOUND ###")
        print("### Try to connect again ###\n")

        time.sleep(3)
        broadcast_sender()


def handling_messages():
    """
    Function that is run after the client is included in the system.
    Handles the user input and sends the user input to the server that is assigned to this client.
    If this server is offline then a new broadcast message is sent to all servers.

    """
    global server_data

    while True:
        try:
            # Verbindung zum Server herstellen
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(
                (server_data.get("server_address"), TCP_PORT))

            socket_socketname = client_socket.getsockname()
            if (len(socket_socketname) == 2):
                global_variables.client_address = socket_socketname[0]

            while True:
                if (global_variables.is_auction_active):
                    # check if the client is the owner of the currently active auction element
                    if (global_variables.active_auction_element.get("bid_owner_client_address") == global_variables.client_address):
                        user_input = input(
                            f"There is an active auction element: '{global_variables.active_auction_element.get('element_name')}' made by you. Type 'break' when you want to sell your element.\n")
                    else:
                        user_input = input(
                            f"### ACTIVE AUCTION ###\nAuction element: '{global_variables.active_auction_element['element_name']}': \n Currently the highest bid is: {global_variables.active_auction_element['highest_bid']}\n Enter your bid:\n")
                else:
                    user_input = input("Choose a new bid element: \n")

                # separate condition for checking if global_variables.is_auction_active is required
                # global auction status could have been changed in the time between the promt to insert a new auction or make a new bid and handling the user input
                if (global_variables.is_auction_active):
                    if (global_variables.active_auction_element.get("bid_owner_client_address") == global_variables.client_address):
                        if (user_input == "break"):
                            global_variables.is_auction_active = False
                            message = str.encode(user_input)
                        else:
                            continue
                    else:
                        if not user_input.strip():
                            print("Empty message. Please try again.\n")
                            continue

                        try:
                            # only integers are taken from the user
                            # convert input to integer
                            bid = int(user_input)

                            if (global_variables.active_auction_element.get("highest_bid") > bid):
                                print("You need to make a higher bid!")

                            message = str.encode(user_input)
                        except ValueError:
                            print(f"You need to make a bid! \n")
                            continue
                else:
                    if not user_input.strip():
                        print("Empty message. Please try again. \n")
                        continue

                    message = str.encode(user_input)

                # Send message to server
                client_socket.send(message)

                # Antwort vom Server empfangen
                response = client_socket.recv(1024).decode('utf-8')
                if (response != "OK"):
                    print(response)

        except (ConnectionRefusedError, ConnectionResetError):
            print("Error: Unable to connect to the server. Retrying... \n")
            broadcast_sender()
        except KeyboardInterrupt:
            print("\nExiting client.")
            break
        finally:
            client_socket.close()


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("### CLIENT SETUP ###")
    print("=" * 50)
    global_variables.is_client = True

    # Start the broadcast sender
    broadcast_sender()
    # Create a thread for the broadcast listener
    threadAuction = threading.Thread(
        target=auction_handler.auction_update_listener)
    # Start the broadcast listener thread
    threadAuction.start()
