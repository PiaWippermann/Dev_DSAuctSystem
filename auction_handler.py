import json
import socket
import sys
import time
from time import sleep
import threading

import global_variables

# clients send data to this port and the server listens to it
TCP_PORT = 10005
# servers listen to this port
# servers communicate with each other about auction related data
AUCTION_MANAGEMENT_PORT = 2
# clients listen to this port
BROADCAST_PORT_AUCTION = 58002

NEW_BID_ELEMENT_MESSAGE = {
    "is_auction_active": True,
    "active_auction_element": {
        "client_uuid": "",
        "element_name": "",
        "highest_bid": 0
    },
    "type": "new_bid_element"
}


# Methods for the auction
# Implementation a TCP listener for incoming messages from clients
def client_listener():
    # Start listening to clients
    # create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind the socket to specific address and port
    s.bind((global_variables.s_address, TCP_PORT))
    # listen for incoming connections
    s.listen()
    print('Start listening to clients')

    while True:
        try:
            # wait for client to connect
            client_socket, client_address = s.accept()
            if client_socket:
                # receive data
                user_input = client_socket.recv(1024)

                # decode and transform to json object
                user_input = user_input.decode('utf-8')
                try:
                    bid_element = json.loads(user_input)
                except json.JSONDecodeError as e:
                    print("No JSON object received from the clien.")

                if (global_variables.is_auction_active):
                    try:
                        bid = bid_element.get("bid")
                        # convert input to integer
                        bid = int(bid)
                    except ValueError:
                        print(f"User did not send a new highest bid")
                        continue
                    else:
                        if (bid > global_variables.active_auction_element.get("highest_bid")):
                            # send new highest bid to the leader server
                            global_variables.active_auction_element["client_uuid"] = bid_element.get(
                                "user_uuid")
                            global_variables.active_auction_element["highest_bid"] = bid
                else:
                    print("Received a new bid element from a client.")
                    if (global_variables.server_uuid == global_variables.leader_server.get("leader_server_uuid")):
                        handle_new_bid_element(bid_element)
                    else:
                        # send new bid element to the leader server
                        print()
        except TimeoutError:
            pass
        # close socket
        except ConnectionRefusedError:
            s.close()


# Method only called by the leader server
def handle_new_bid_element(bid_element):
    if (not (global_variables.is_auction_active)):
        # set the new bid element
        global_variables.is_auction_active = True
        global_variables.active_auction_element["element_name"] = bid_element.get(
            "bid")
        global_variables.active_auction_element["client_uuid"] = bid_element.get(
            "client_uuid")
