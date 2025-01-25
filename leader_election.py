"""
leader_election.py

File containing functions regarding the leader election.
Leader election is done with the Bully Algorithm.

- leader election listener
- leader election starter

"""

from ctypes import addressof
import json
import socket

# import files
import global_variables
import broadcast

ELECTION_PORT = 10001

# Listener started when the server is created
# Constantly listens for election messages
# TCP connection


def leader_election_listener():
    """
    Listens to incoming election messages

    """
    leader_election_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    leader_election_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    leader_election_socket.bind(('', ELECTION_PORT))
    while True:
        message, addr = leader_election_socket.recvfrom(1024)
        handle_election_message(leader_election_socket, message, addr)


def handle_election_message(socket, message, addr):
    """
    Handles election messages depending on the type of election message which can be ELECTION or ALIVE messages

    """
    # message that indicates to start an election
    message = json.loads(message.decode())
    if message.get("type") == "ELECTION":
        # check if the uuid of the server that has sent the election message is lower than the current server's uuid
        if (global_variables.server_uuid > message.get("sender_server_uuid")):
            # send an answer to this server with the message that the current server is alive
            alive_message = {
                "type": "ALIVE",
                "sender_server_uuid": global_variables.server_uuid
            }
            socket.sendto(json.dumps(alive_message).encode(), addr)
            start_leader_election()


def start_leader_election():
    """
    Function called to start a new leader election

    """
    print("Leader election startet.")

    # if the server list only consists of this server it is set as the leader server
    if (len(global_variables.server_list) == 1):
        global_variables.leader_server = {
            "leader_server_uuid": global_variables.server_uuid,
            "leader_server_address": global_variables.s_address
        }
        # no need to inform other servers as there are no other servers
        print("I am the only server so I am the leader.\n")
    else:
        send_election_messages()


def send_election_messages():
    """
    Sending the election messages to all servers with a higher uuid.
    Waiting for any alive messages and sends the victory message if no alive message is received.
    """
    # get the index of the server in the server list
    current_node_index = -1
    for i in range(len(global_variables.server_list)):
        if global_variables.server_list[i].get("server_uuid") == global_variables.server_uuid:
            current_node_index = i
            break

    # check if the server is the one with the highest server_uuid
    if current_node_index == (len(global_variables.server_list) - 1):
        send_victory_message()
    else:
        for i in range(current_node_index + 1, len(global_variables.server_list)):
            election_message = {
                "type": "ELECTION",
                "sender_server_uuid": global_variables.server_uuid
            }

            # send election message to all servers with higher uuid
            leader_election_socket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM)
            leader_election_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            leader_election_socket.sendto(json.dumps(election_message).encode(
            ), (global_variables.server_list[i].get("server_address"), ELECTION_PORT))

            print(f"ELECTION message sent to server at position {i}.\n")

            leader_election_socket.settimeout(2)

            try:
                message, addr = leader_election_socket.recvfrom(1024)
                message = json.loads(message.decode())
                if (message.get("type") == "ALIVE"):
                    print("Received an ALIVE message\n")

            except TimeoutError:
                send_victory_message()


def send_victory_message():
    """
    Function called to announce the server as the leader
    """
    election_message = {
        "type": "COORDINATOR",
        "leader_server": {
            "leader_server_uuid": global_variables.server_uuid,
            "leader_server_address": global_variables.s_address
        },
        "sender_server_uuid": global_variables.server_uuid
    }

    # update the global variable that contains the leader server which is the server itself
    global_variables.leader_server = {
        "leader_server_uuid": global_variables.server_uuid,
        "leader_server_address": global_variables.s_address
    }

    print(f"I am the leader server {global_variables.server_uuid}\n")

    # send a broadcast message to all servers
    broadcast.broadcast_sender(election_message)
