"""
broadcast.py

File that contains functions regarding broadcast messages.
Different types of broadcast messages are handled here also depending on the current server's role.

- broadcast listener
- broadcast sender

"""

# python imports
import json
import socket

# import global variables
import global_variables
import leader_election
import participants_ring

###########################################################

SERVER_INDEX = 0

# port definitions
DYNAMIC_DISCOVERY_BROADCAST_IP = "255.255.255.255"
BROADCAST_PORT = 5973
DYNAMIC_DISCOVERY_BROADCAST_TIMEOUT = 2

###########################################################

# FUNCTION DEFINITIONS


def broadcast_sender(broadcast_message):
    """
    Method called when the server starts
    Broadcast message is sent to all computers in LAN
    Server is waiting for response from the leader server if there is already one
    If there is no leading server the leader election is run
    """
    # Create a UDP socket
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Broadcast message of type: ", broadcast_message['type'])
    broadcast_socket.sendto(json.dumps(broadcast_message).encode(
    ), (DYNAMIC_DISCOVERY_BROADCAST_IP, BROADCAST_PORT))

    # if the broadcast message sent is a discovery message wait for a response
    if broadcast_message.get("type") == "server_discovery":
        broadcast_socket.settimeout(DYNAMIC_DISCOVERY_BROADCAST_TIMEOUT)

        try:
            # Wait for a response
            data, addr = broadcast_socket.recvfrom(1024)
            response = json.loads(data.decode())

            if response.get("type") == "environment_update":
                # update the server list as the leader server has sent it
                global_variables.server_list = response.get("server_list")
                # update the current server's neighbor
                participants_ring.update_neighbor()
                print("### SERVER SUCCESSFULLY INTEGRATED ###")
                print("=" * 50)

        except socket.timeout:
            # no server is responding
            print("### NO OTHER SERVERS FOUND ###")
            print("=" * 50)


def broadcast_listener():
    """
    Server listen to broadcast messages from other servers.
    Different types of broadcast messages are handled differnt.
    If the current server is not the leader some messages are also ignored.

    """
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    listen_socket.bind(("", BROADCAST_PORT))

    while True:
        try:
            data, addr = listen_socket.recvfrom(1024)
            message = json.loads(data.decode())

            # do not react to messages from the current server itself
            if (message.get("sender_server_uuid") == global_variables.server_uuid):
                continue

            # different types of broadcasts can be received
            # check for the type of the incoming message and handle the message accordingly

            # 1. server wants to join the system
            # only answer if the current server is the leader server
            if message.get("type") == "server_discovery":
                # check if the current server is the leader server
                if (global_variables.leader_server.get("leader_server_uuid") == global_variables.server_uuid):
                    print(
                        "\nI am the leader server and I will integrate the new server\n")
                    # udpate the group view
                    global_variables.server_list.append({
                        "server_uuid": message.get("sender_server_uuid"),
                        "server_address": message.get("server_address")
                    })

                    # form the ring after the new server has been pushed to the group view
                    participants_ring.form_ring()

                    # update the neighbor of the leader server as well
                    participants_ring.update_neighbor()

                    environment_message = {
                        "type": "environment_update",
                        "server_list": global_variables.server_list,
                        "message": "System environment has been updated",
                        "sender_server_uuid": global_variables.server_uuid
                    }

                    # send a message to the requesting server
                    listen_socket.sendto(json.dumps(
                        environment_message).encode(), addr)

                    # send broadcast message to all servers with the updated sorted group_view
                    broadcast_sender(environment_message)

            # 2. the server environment has changed
            elif message.get("type") == "environment_update":
                # update the server list as the leader server has sent it
                global_variables.server_list = message.get("server_list")
                # update the current server's neighbor
                participants_ring.update_neighbor()
                print("System environment has been updated \n")

            # 3. leader server has changed
            elif message.get("type") == "COORDINATOR":
                # message received if a server that announces itself as the leader server
                # set the leader server
                global_variables.leader_server = message.get(
                    "leader_server")
                print(
                    f"New leader server: {global_variables.leader_server.get('leader_server_uuid')}\n")

                # check if the new leader server has a higher server_uuid than the current server has
                if global_variables.leader_server.get("leader_server_uuid") < global_variables.server_uuid:
                    # if the new leader server has a lower uuid then a new leader election is started
                    print(
                        "New leader server has a lower server uuid than me. I will start a new election.\n")
                    leader_election.start_leader_election()

            # 4. client wants to join the system
            # only answer if the current server is the leader server
            if message.get("type") == "client_discovery":
                # check if the current server is the leader server
                if (global_variables.leader_server.get("leader_server_uuid") == global_variables.server_uuid):
                    print("Client wants to join the auction.")

                    server_address = global_variables.s_address
                    server_uuid = global_variables.server_uuid

                    global SERVER_INDEX
                    # select a server that is assigned to the client
                    if (SERVER_INDEX < len(global_variables.server_list)):
                        server_address = global_variables.server_list[SERVER_INDEX].get(
                            "server_address")
                        server_uuid = global_variables.server_list[SERVER_INDEX].get(
                            "server_uuid")
                        SERVER_INDEX = SERVER_INDEX + 1
                    else:
                        SERVER_INDEX = 0
                        server_address = global_variables.server_list[SERVER_INDEX].get(
                            "server_address")
                        server_uuid = global_variables.server_list[SERVER_INDEX].get(
                            "server_uuid")
                        SERVER_INDEX = SERVER_INDEX + 1

                    # set the discovery message response
                    client_discovery_message_response = {
                        "type": "client_discovery",
                        "server_address": server_address,
                        "server_uuid": server_uuid,
                        "is_auction_active": global_variables.is_auction_active,
                        "active_auction_element": global_variables.active_auction_element
                    }

                    # send the response to the client
                    listen_socket.sendto(json.dumps(
                        client_discovery_message_response).encode(), addr)
                    print(f"Client successfully included.")

        except Exception as e:
            print(f"Error when trying to receive broadcast messages: {e}\n")
