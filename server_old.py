import json
import socket
import sys
import time
from time import sleep
import threading

# import auction functions in other files
import broadcast
import leader_election

# import global variables
import global_variables

# Listening ports for all sockets
DYNAMIC_DISCOVERY_PORT = 57697
MESSAGE_TO_SERVER_PORT = 57777
HB_PORT = 59001
TCP_PORT = 10005
TCP_AUCTION_PORT = 10006
BROADCAST_PORT_CHAT = 58002
BROADCAST_PORT_AUCTION = 58003
ELECTION_PORT = 10001

# Buffer size
BUFFER_SIZE = 5120

# message definitions
SERVER_DISCOVERY_MESSAGE = {
    "type": "server_discovery",
    "sender_server_uuid": global_variables.server_uuid,
    "server_address": global_variables.s_address,
    "message": "Hello, any servers there?"
}

# Auction related data
IS_AUCTION_ACTIVE = False
ACTIVE_AUCTION_ELEMENT = {
    "NAME": "",
    "HIGHEST_BID": 0
}

# List of server components
servers = [global_variables.s_address]
# List of all clients
overall_clients = []

# Global variables for leadership, heartbeat and voting
leader = None
isLeader = False
neighbor = None
participant = False


#
def start_listeners():
    # create a separate thread to run the broadcast listener function
    threadBL = threading.Thread(target=discovery_listener)
    threadBL.start()
    # create a separate to run the election listener function
    threadEL = threading.Thread(target=election_listener)
    threadEL.start()
    # create a separate thread to run the heartbeat Listen function
    threadHL = threading.Thread(target=heartbeat_listener)
    threadHL.start()
    # create a separate thread to run the TCP listener function
    threadTL = threading.Thread(target=tcp_listener)
    threadTL.start()


#
def start_senders():
    # create a separate thread to run message from server function
    threadMS = threading.Thread(target=message_from_server)
    threadMS.start()
    # create a separate thread to run the heartbeat function
    threadHB = threading.Thread(target=heartbeat_sender)
    threadHB.start()


# Method to check if the neighbor is still available
# def heartbeat_sender():
#     message = '#'
#     ping = str.encode(message)
#     heartbeat = 0
#     while True:
#         if neighbor:
#             try:
#                 # Message is sent via TCP socket to the neighbor in a second cycle
#                 # If no connection could be established, the heartbeat is counted up
#                 heartbeat_socket = socket.socket(
#                     socket.AF_INET, socket.SOCK_STREAM)
#                 heartbeat_socket.settimeout(1)
#                 heartbeat_socket.connect((neighbor, HB_PORT))
#                 heartbeat_socket.send(ping)
#                 heartbeat_socket.close()
#                 sleep(1)
#             # No incrementing of the heartbeat when connecting
#             except (ConnectionRefusedError, TimeoutError):
#                 heartbeat += 1
#             else:
#                 heartbeat = 0
#             # With more than 5 heartbeats the neighbor counts as crashed

#             # Checks if this neighbor was the leader, if so a new election is started
#             if heartbeat > 5:
#                 heartbeat = 0
#                 print(
#                     f'failed heartbeats to neighbor, remove {neighbor} and get a new environment')
#                 # This neighbor is removed from the list, all servers are informed and a new neigbor is selected
#                 servers.remove(neighbor)
#                 # message_to_server(servers)
#                 # check if the neighbor was the leader
#                 neighbor_leader = neighbor == leader
#                 time.sleep(2)
#                 get_environment()
#                 # if a leader crashes, the election is started
#                 if neighbor_leader:
#                     print('Previous neighbor was leader, starting election')
#                     time.sleep(2)
#                     leader_election()
#                     # discovery_listener()


# Listener to heartbeat_sender
def heartbeat_listener():
    # Create TCP socket to listen so heartbeats from neighbor
    heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    heartbeat_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    heartbeat_socket.bind((global_variables.s_address, HB_PORT))
    heartbeat_socket.settimeout(4)

    while True:
        try:
            heartbeat_socket.listen()
            heartbeat, heartbeat_neighbour = heartbeat_socket.accept()
            # Continue by receiving heartbeats
            if heartbeat:
                time.sleep(1)
        except TimeoutError:
            pass


# Form rings for finding neighbor
# Basic from practical codes
def form_ring(server_list):
    sorted_binary_ring = sorted([socket.inet_aton(member)
                                for member in server_list])
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]

    return sorted_ip_ring


# Method to find a neighbor from the server list
def get_environment():
    global neighbor
    # If there is only one server in the list, there is no neighbor
    if len(servers) == 1:
        neighbor = None
        print('No neighbor available')
        return
    # The list servers is sorted by the method form_ring()
    form_ring(servers)
    time.sleep(1)
    # searches position of the server in the server list
    index = servers.index(global_variables.s_address)
    # Determines the next element in the list servers after the element whose position is stored in the variable index.
    neighbor = servers[0] if index + 1 == len(servers) else servers[index + 1]
    print(f'New neighbor: {neighbor}')


# Method to start the leader election
# def leader_election():
#     # Global variable for using them in the hole program
#     global leader, isLeader, participant
#     election_message = {'mid': global_variables.s_address, 'isLeader': False}

#     # if only one server in the server list
#     if len(servers) == 1:
#         print(f'I am the only server in the system')
#         leader = global_variables.s_address

#     # Start the election if more than one server in the server list
#     elif len(servers) > 1:
#         print('start election')
#         participant = True
#         # the election message is sent via broadcast to the neighbor
#         # Using JSON to send the message because it is a dictionary
#         election_message = json.dumps(election_message)
#         election_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         try:
#             election_socket.sendto(
#                 election_message.encode(), (neighbor, ELECTION_PORT))

#         except ConnectionRefusedError:
#             pass


def election_listener():
    global leader, isLeader, participant
    election_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    election_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    election_socket.bind(('', ELECTION_PORT))

    while True:
        time.sleep(1)
        # Receiving messages by using JSON
        election, neighbor_right = election_socket.recvfrom(BUFFER_SIZE)
        election_message = json.loads(election.decode('utf-8'))

        # If an election message is received, compare the received IP with global_variables.s_address and the leader status
        if election:
            # First set the leader false
            leader = False

            # If the isLeader status is True, the received IP is the new leader
            if election_message['isLeader']:
                leader = election_message['mid']
                time.sleep(2)
                participant = False
                # The new received message is forwarded to the neighbor
                leader_message = json.dumps(election_message)
                time.sleep(1)
                election_socket.sendto(
                    leader_message.encode(), (neighbor, ELECTION_PORT))
                # Update the discovery_listener
                # discovery_listener()

            # If the received IP is smaller than global_variables.s_address and not participant
            elif election_message['mid'] < global_variables.s_address and not participant:
                # The election messages is updated with the current IP (global_variables.s_address) and is sent to the neighbor
                new_election = {
                    'mid': global_variables.s_address, 'isLeader': False}
                new_election = json.dumps(new_election)
                participant = True
                time.sleep(1)
                election_socket.sendto(
                    new_election.encode(), (neighbor, ELECTION_PORT))

            # If the received IP is greater than global_variables.s_address, the election messages is forwarded to the neighbor
            # Election message is not updated
            elif election_message['mid'] > global_variables.s_address:
                participant = True
                message = json.dumps(election_message)
                time.sleep(1)
                election_socket.sendto(
                    message.encode(), (neighbor, ELECTION_PORT))

            # if the received IP is equal to global_variables.s_address the election messages is updated with isLeader=True
            # Updated message is sent to the neighbor
            elif election_message['mid'] == global_variables.s_address:
                # Update the dynamic_listener
                # discovery_listener()
                time.sleep(1)
                # Set the new leader
                leader = global_variables.s_address
                new_election = {
                    'mid': global_variables.s_address, 'isLeader': True}
                new_election = json.dumps(new_election)
                # set participant False
                participant = False
                election_socket.sendto(
                    new_election.encode(), (neighbor, ELECTION_PORT))


# Methods for the auction
# Implementation a TCP listener for incoming messages from clients
def tcp_listener():
    # Start listening
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
            data, client_address = s.accept()
            if data:
                # receive data
                text = data.recv(BUFFER_SIZE).decode()
                # TODO: wenn active auction dann darf der input data type nur integer sein
                # TODO: check ob int und ob > 0
                # TODO: check ob das neue Gebot > als das aktuelle Gebot (aktueller Stand steht im globalen Auction Object)
                # TODO: wenn ja dann neue Methode, die neues höchstes Gebot an den Leader Server schickt

                # TODO: wenn keine active auction dann darf der input data type nur string sein
                # TODO: globalen Auction Variables setzen mit active auction = true und das auction element setzen
                # TODO: neue Methode, die neue auction startet -> Sendet das an den Leader Server

                print(f'incoming messages from ' + text)
                # send the reveived data to function
                # broadcastsender_chat(text)

        except TimeoutError:
            pass
        # close socket
        except ConnectionRefusedError:
            s.close()


def update_auction_to_leader():
    message = ACTIVE_AUCTION_ELEMENT

    try:
        # Create a TCP socket
        auction_info_soecket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the server
        auction_info_soecket.connect((leader, TCP_AUCTION_PORT))
        # Set the socket to be non-blocking
        auction_info_soecket.setblocking(False)
        # Send the message
        auction_info_soecket.send(message)
        # Close the socket
        auction_info_soecket.close()

    except (ConnectionRefusedError, TimeoutError):
        # Handling connection errors
        print('\rError - Not possible to send the new auction status to the leader server')


def broadcastsender_chat(message):
    bmessage = message.encode()

    b_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the socket to broadcast and enable reusing addresses
    b_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    b_socket.sendto(bmessage, ('255.255.255.255', BROADCAST_PORT_CHAT))
    b_socket.close()


if __name__ == '__main__':
    # send out a broadcast message to discover other Servers or clients on the network
    # discovery_broadcast()

    # # start listeners
    # start_listeners()

    # # start senders
    # start_senders()

    print("Meine eindeutige UUID", global_variables.server_uuid)

    # 1. send a broadcast messsage to discover other servers in the network
    broadcast.broadcast_sender(SERVER_DISCOVERY_MESSAGE)

    # 2. step: start listeners

    # create a separate thread to run the leader election listener
    thread_leader_election_listener = threading.Thread(
        target=leader_election.leader_election_listener)
    thread_leader_election_listener.start()

    # create a separate thread to run the broadcast listener
    thread_dynamic_discovery_listener = threading.Thread(
        target=broadcast.broadcast_listener)
    thread_dynamic_discovery_listener.start()

    # 3. start new leader election
    # server has been started, broadcast message is sent and all listeners are started
    # the new server is successfully integrated into the system so a new leader server is elected
    leader_election.start_leader_election()
