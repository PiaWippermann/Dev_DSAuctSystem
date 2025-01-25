"""
auction_handler.py

This module manages the auction process, including:
- Listening to clients
- Handling clients and their messages
- Listening to auction update messages

"""

import json
import socket
import threading

import global_variables

# clients send data to this port and the server listens to it
TCP_PORT = 10005
# clients listen to this port
BROADCAST_PORT_AUCTION = 58002


def client_listener():
    """
    Listening to client connections. Each time a new client connects the client messages are handled in a separat thread.
    Function is run by the server and not by the clients.

    """

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", TCP_PORT))
    server_socket.listen()

    while True:
        client_socket, client_address = server_socket.accept()
        # Starte einen neuen Thread für jeden Client
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, client_address))
        client_thread.start()


def handle_client(client_socket, client_address):
    """
    Called when a client tries to connect to the server.
    Continuously listens to incoming client messages and handles the messages depending on the current auction status.

    """
    print(f"Client {client_address[0]} connected.")

    # init the client address as a string
    client_address = client_address[0]

    while True:
        try:
            # receive client message
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break  # ignore empty messages

            if (global_variables.is_auction_active):
                # check if the sender client address equals the owner address of the currently active element
                if (global_variables.active_auction_element.get("bid_owner_client_address") == client_address):
                    auction_completed_message = {
                        "type": "auction_completed",
                        "active_auction_element": global_variables.active_auction_element
                    }
                    auction_update_sender(auction_completed_message)

                    response = "OK"
                    # Antwort an den Client senden
                    client_socket.send(response.encode('utf-8'))
                # new bid is incoming
                else:
                    try:
                        # convert input to integer
                        bid = int(message)
                    except ValueError:
                        print(f"User did not send a new highest bid!\n")
                        continue
                    else:
                        response = "OK"

                        if (bid > global_variables.active_auction_element.get("highest_bid")):
                            handle_new_client_bid(bid, client_address)
                        else:
                            response = "There is a higher bid than yours!\n"
                        # Antwort an den Client senden
                        client_socket.send(response.encode('utf-8'))
            else:
                # string that is received from the user is taken as a new element_name
                handle_new_client_auction_element(message, client_address)

                # send response to client such that it can continue
                response = "OK"
                # Antwort an den Client senden
                client_socket.send(response.encode('utf-8'))
        # client disconnected
        # check if the currently active auction is initialized by the offline client
        except ConnectionResetError:
            print(f"Client {client_address} disconnected.")

            if (global_variables.active_auction_element.get("bid_owner_client_address") == client_address):
                auction_candelled_message = {
                    "type": "auction_cancelled"
                }

                auction_update_sender(auction_candelled_message)
            break


def handle_new_client_bid(bid, client_address):
    """
    Function called when the incoming client messages contains a new bid for the active auction element.
    All servers and clients are informed about this new bid via a broadcast message.

    """
    auction_update_message = {
        "type": "auction_element_update",
        "active_auction_element": {
            "element_name": global_variables.active_auction_element.get("element_name"),
            "bid_owner_client_address": global_variables.active_auction_element.get("bid_owner_client_address"),
            "highest_bid": bid,
            "client_address": client_address
        },
        "sender_server_uuid": global_variables.server_uuid
    }

    global_variables.active_auction_element = auction_update_message.get(
        "active_auction_element")

    auction_update_sender(auction_update_message)


def handle_new_client_auction_element(element_name, client_address):
    """
    Function called when the incoming client messages contains a new bid element.
    All servers and clients are informed about this new bid element via a broadcast message.

    """
    auction_update_message = {
        "type": "auction_element_new",
        "active_auction_element": {
            "element_name": element_name,
            "highest_bid": 0,
            "client_address": client_address,
            "bid_owner_client_address": client_address
        },
        "sender_server_uuid": global_variables.server_uuid
    }

    global_variables.active_auction_element = auction_update_message.get(
        "active_auction_element")
    global_variables.is_auction_active = True

    auction_update_sender(auction_update_message)


def auction_update_sender(auction_message):
    """
    Sends a boradcast message to update all clients and servers in the system.
    The auction message can be different depending on the user input and the current auction status.

    """
    auction_update_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    auction_update_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    auction_update_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    auction_update_socket.sendto(json.dumps(
        auction_message).encode(), ("255.255.255.255", BROADCAST_PORT_AUCTION))


def auction_update_listener():
    """
    Clients and server run this function such that they listen to incoming messages regarding auction updates.
    Different types of auction messages are handled in a different way.

    """
    auction_update_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    auction_update_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    auction_update_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    auction_update_socket.bind(('', BROADCAST_PORT_AUCTION))

    while True:
        message, addr = auction_update_socket.recvfrom(1024)

        message = json.loads(message.decode())

        # ignore own messages
        if (message.get("sender_server_uuid") == global_variables.server_uuid):
            continue

        # new bid element
        if (message.get("type") == "auction_element_new"):
            if (not (global_variables.is_auction_active)):
                global_variables.is_auction_active = True
                global_variables.active_auction_element = message.get(
                    "active_auction_element")

                # inform the user if the current instance is a client
                if (global_variables.is_client & (global_variables.client_address != message["active_auction_element"].get("bid_owner_client_address"))):
                    print(
                        f"\n ### NEW BID ELEMENT ###\nPlease insert your bids for the element: {global_variables.active_auction_element.get('element_name')}\n")

        # new highest bid for the active element
        elif (message.get("type") == "auction_element_update"):
            if (global_variables.active_auction_element.get("highest_bid") < message["active_auction_element"].get("highest_bid")):
                global_variables.active_auction_element = message.get(
                    "active_auction_element")

                # inform the user that the highest bid has been updated
                if (global_variables.is_client):
                    print(
                        f"\n ### NEW HIGHEST BID ###\nThe new highest bid is: {global_variables.active_auction_element.get('highest_bid')}\n")

        # active auction is completed
        elif (message.get("type") == "auction_completed"):
            # inform the user that the auction has been completed
            if (global_variables.is_client):
                if ((global_variables.client_address != message["active_auction_element"].get("bid_owner_client_address")) & (message["active_auction_element"].get("client_address") == global_variables.client_address)):
                    print(
                        f"\n ### AUCTION COMPLETED ###\nYour are the winner!\nYour bid is: {message['active_auction_element'].get('highest_bid')}\n")
                    print("Choose a new bid element:")
                elif ((global_variables.client_address == message["active_auction_element"].get("client_address")) & (global_variables.client_address == message["active_auction_element"].get("bid_owner_client_address"))):
                    print(
                        "\n ### AUCTION COMPLETED ###\nYou did not sell the element\n")
                else:
                    print(
                        f"\n ### AUCTION COMPLETED ###\nElement sold to {message['active_auction_element'].get('client_address')}\nThe bid is: {message['active_auction_element'].get('highest_bid')}\n")

                    if (global_variables.client_address != message["active_auction_element"].get("bid_owner_client_address")):
                        print("Choose a new bid element:")

            global_variables.is_auction_active = False
            global_variables.active_auction_element = {
                "client_address": "",
                "element_name": "",
                "highest_bid": 0,
                "bid_owner_client_address": ""
            }
        # active auction is cancelled because the element owner client is offline
        elif (message.get("type") == "auction_cancelled"):
            if (global_variables.is_client):
                print(
                    "\n ### AUCTION CANCELLED ###\n The auction element owner is offline.\n")
                print("Choose a new bid element:")

            global_variables.is_auction_active = False
            global_variables.active_auction_element = {
                "client_address": "",
                "element_name": "",
                "highest_bid": 0,
                "bid_owner_client_address": ""
            }
