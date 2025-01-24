import json
import socket
import time
import threading

import global_variables

# clients send data to this port and the server listens to it
TCP_PORT = 10005
# clients listen to this port
BROADCAST_PORT_AUCTION = 58002

AUCTION_UPDATE_MESSAGE = {
    "type": "auction_element_new",
    "active_auction_element": {
        "element_name": "",
        "highest_bid": 0,
        "client_uuid": ""
    },
    "sender_server_uuid": global_variables.server_uuid
}

last_auction_status_change = time.time()


def client_listener():
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
    print(f"Client {client_address} connected.\n")
    while True:
        try:
            # Empfang der Nachricht vom Client
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break  # Verbindung geschlossen

            try:
                bid_element = json.loads(message)
            except json.JSONDecodeError as e:
                print("No JSON object received from the client.\n")

            if (global_variables.is_auction_active):
                try:
                    bid = bid_element.get("bid")
                    # convert input to integer
                    bid = int(bid)
                    bid_element["bid"] = bid
                except ValueError:
                    print(f"User did not send a new highest bid!\n")
                    continue
                else:
                    response = "OK"

                    if (bid > global_variables.active_auction_element.get("highest_bid")):
                        handle_new_client_bid(bid_element)
                    else:
                        response = "There is a higher bid than yours!\n"
                    # Antwort an den Client senden
                    client_socket.send(response.encode('utf-8'))
            else:
                # string that is received from the user is taken as a new element_name
                handle_new_client_auction_element(bid_element)

                # send response to client such that it can continue
                response = "OK"
                # Antwort an den Client senden
                client_socket.send(response.encode('utf-8'))

        except ConnectionResetError:
            print(f"Client {client_address} disconnected.")
            break


def handle_new_client_bid(bid):
    AUCTION_UPDATE_MESSAGE = {
        "type": "auction_element_update",
        "active_auction_element": {
            "element_name": global_variables.active_auction_element.get("element_name"),
            "highest_bid": bid.get("bid"),
            "client_uuid": bid.get("client_uuid")
        },
        "sender_server_uuid": global_variables.server_uuid
    }

    global_variables.active_auction_element = AUCTION_UPDATE_MESSAGE.get(
        "active_auction_element")

    auction_update_sender(AUCTION_UPDATE_MESSAGE)
    # start the auction timer if the leader server received the message from the client
    if (global_variables.leader_server.get("leader_server_uuid") == global_variables.server_uuid):
        start_auction_timer()


def handle_new_client_auction_element(bid_element):
    AUCTION_UPDATE_MESSAGE = {
        "type": "auction_element_new",
        "active_auction_element": {
            "element_name": bid_element.get("element_name"),
            "highest_bid": 0,
            "client_uuid": bid_element.get("client_uuid")
        },
        "sender_server_uuid": global_variables.server_uuid
    }

    global_variables.active_auction_element = AUCTION_UPDATE_MESSAGE.get(
        "active_auction_element")
    global_variables.is_auction_active = True

    auction_update_sender(AUCTION_UPDATE_MESSAGE)

    # start the auction timer if the leader server received the message from the client
    if (global_variables.leader_server.get("leader_server_uuid") == global_variables.server_uuid):
        start_auction_timer()


# All other servers and clients are updated with the given message
def auction_update_sender(auction_message):
    # address can be '255.255.255.255' or the leader_server_address depending on the sender
    auction_update_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    auction_update_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    auction_update_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    auction_update_socket.sendto(json.dumps(
        auction_message).encode(), ("255.255.255.255", BROADCAST_PORT_AUCTION))


# Listener that runs for the whole lifetime of the client or server that has been started
# Global updates on the action element are published by the leader server
# The global variables regarding the auction are reininitialized
def auction_update_listener():
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
                if (global_variables.is_client):
                    print(
                        f"\n ### NEW BID ELEMENT ###\nPlease insert your bids for the element: {global_variables.active_auction_element.get('element_name')}\n")

                # start the auction timer if the leader server received the message
                if (global_variables.leader_server.get("leader_server_uuid") == global_variables.server_uuid):
                    start_auction_timer()
        # new highest bid for the active element
        elif (message.get("type") == "auction_element_update"):
            if (global_variables.active_auction_element.get("highest_bid") < message["active_auction_element"].get("highest_bid")):
                global_variables.active_auction_element["highest_bid"] = message["active_auction_element"].get(
                    "highest_bid")

                # inform the user that the highest bid has been updated
                if (global_variables.is_client):
                    print(
                        f"\n ### NEW HIGHEST BID ###\nThe new highest bid is: {global_variables.active_auction_element.get('highest_bid')}\n")

                # start the auction timer if the leader server received the message
                if (global_variables.leader_server.get("leader_server_uuid") == global_variables.server_uuid):
                    start_auction_timer()
        # active auction is completed
        elif (message.get("type") == "auction_completed"):
            # inform the user that the auction has been completed
            if (global_variables.is_client):
                if (message["active_auction_element"].get("client_uuid") == message["active_auction_element"].get("client_uuid")):
                    print(
                        f"\n ### AUCTION COMPLETED ###\nYour are the winner!\nYour bid is: {message['active_auction_element'].get('highest_bid')}\n")
                else:
                    print(
                        f"\n ### AUCTION COMPLETED ###\nThe element is sold to: {message['active_auction_element'].get('client_uuid')}.\nThe bid is: {message['active_auction_element'].get('highest_bid')}\n")

            global_variables.is_auction_active = False
            global_variables.active_auction_element = {
                "client_uuid": "",
                "element_name": "",
                "highest_bid": 0
            }
        # message only for clients informing that the client has 30 more seconds to bid on the active element
        elif (global_variables.is_client & (message.get("type") == "auction_timer_information")):
            print("### 30 MORE SECONDS TO ENTER YOUR BID ###\n")


# Method called when the action status changes (new auction element or new highest bid)
# If there is no auction status change within one minute the auction is closed by the leader server
# After 30 seconds all clients are informed about the remaining time
def start_auction_timer():
    last_auction_status_change = time.time()
    # wait for 30 seconds
    time.sleep(30)
    # check if the auction status has changed again
    if (time.time() - last_auction_status_change >= 30):
        # status has not changed
        # inform all clients that 30 seconds are left to make a bid
        auction_information_message = {
            "type": "auction_timer_information",
            "sender_server_uuid": global_variables.server_uuid
        }
        auction_update_sender(auction_information_message)

        # wait for 30 seconds more
        time.sleep(30)
        # check if the auction status has changed now
        if (time.time() - last_auction_status_change >= 60):
            auction_completed_message = {
                "type": "auction_completed",
                "sender_server_uuid": global_variables.server_uuid,
                "active_auction_element": global_variables.active_auction_element
            }
            auction_update_sender(auction_completed_message)
