import json
import socket
import sys
import time
from time import sleep
import threading

import global_variables

# TODO:
#  Nur der Leader Server hört hier auf einen neu zu erstellenden Port wo alle Server ihre neuen höchsten Gebote hinschicken
# Der Leader Server entscheidet dann ob das reingekommene Gebot höher ist als das global höchste Gebot
# Wenn ja wird ein Broadcast an alle Server geschickt, wo der Auction status geupdated ist (mit dem neuen höchsten Gebot)
# TODO: Recherche wie man am besten 1 zu 1 communication macht


def global_auction_management():
    if global_variables.s_address == global_variables.leader_server_uuid:
        # Start listening to incoming auction status changes
        # create socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind the socket to specific address and port
        s.bind((global_variables.s_address, 333))
        # listen for incoming connections
        s.listen()
        print('Start listening to servers which can come with increased bids')
        while True:
            # if the server is not the leader anymore then stop listening to the socket
            if global_variables.s_address != global_variables.leader_server_uuid:
                s.close()

            try:
                # wait for client to connect
                data, client_address = s.accept()
                if data:
                    # receive data
                    incoming_auction_element = data.recv(1024).decode()

                    increased_bid = False

                    if incoming_auction_element['BID'] > ACTIVE_AUCTION_ELEMENT["BID"]:
                        # update the global active auction element
                        increased_bid = True
                        ACTIVE_AUCTION_ELEMENT = incoming_auction_element

                    # inform all other servers if the global active auction element has changed
                    if increased_bid:
                        # inform others
                        print()

            except TimeoutError:
                pass
            # close socket
            except ConnectionRefusedError:
                s.close()


# TODO:
# Diesen Listener haben alle Server. Wenn der Leader Server ein neues globales höchstes Gebot bekommt müssen alle anderen Server über dieses benachrichtigt werden
# Alle Server updaten dann das Auction Element Object
