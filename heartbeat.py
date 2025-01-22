import time
import socket
import json

import global_variables
import broadcast
import participants_ring
import leader_election

HB_PORT = 59001
LAST_HEARTBEAT_TIME = time.time()


def heartbeat_listener():
    heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    heartbeat_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    heartbeat_socket.bind(('', HB_PORT))

    while True:
        message, addr = heartbeat_socket.recvfrom(1024)
        handle_heartbeat_message(json.loads(message.decode()), addr)


def handle_heartbeat_message(message, addr):
    heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    heartbeat_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    if (message.get("type") == "HEARTBEAT_ACK"):
        LAST_HEARTBEAT_TIME = time.time()
    elif ((message.get("type") == "HEARTBEAT")):
        heartbeat_message = {
            "type": "HEARTBEAT_ACK",
            "sender_server_uuid": global_variables.server_uuid
        }
        # send a HEARTBEAT_ACK
        heartbeat_socket.sendto(json.dumps(heartbeat_message).encode(), addr)


def heartbeat_sender():
    heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    heartbeat_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    heartbeat_message = {
        "type": "HEARTBEAT",
        "sender_server_uuid": global_variables.server_uuid
    }

    """Sendet regelmäßig HEARTBEAT-Nachrichten an den Nachbarn."""
    while True:
        if (global_variables.neighbor != None):
            # print(f"Send HEARTBEAT to neighbour: ",
            #   global_variables.neighbor.get("server_address"))
            heartbeat_socket.sendto(json.dumps(heartbeat_message).encode(
            ), (global_variables.neighbor.get("server_address"), HB_PORT))

            # Überprüfen, ob der Nachbar reagiert hat
            heartbeat_socket.settimeout(2)
            try:
                # Wait for a response
                data, addr = heartbeat_socket.recvfrom(1024)
                response = json.loads(data.decode())

            except socket.timeout:
                # no server is responding
                print("No heartbeat received from neighbor. Update the group view.")
                old_neighbor_server_uuid = global_variables.neighbor.get(
                    "server_uuid")

                # udpate the group view by removing the neighbor that is offline
                global_variables.server_list.remove(key=lambda x: x.get(
                    "server_uuid") == global_variables.neighbor.get("server_uuid"))

                # form the ring after neighbor server has been removed from the server list
                participants_ring.form_ring()

                # set the new neighbor of the server
                participants_ring.update_neighbor()

                # send broadcast message to all servers with the updated sorted group_view
                broadcast.broadcast_sender(
                    global_variables.ENVIRONMENT_MESSAGE)

                # if the previous neighbor has been the leader server start new leader elections
                if (old_neighbor_server_uuid == global_variables.leader_server.get("leader_server_uuid")):
                    leader_election.start_leader_election()

        else:
            print(f"Server has no neighbor configured!")
            # wait for 5 seconds to try sending the heartbeat message again and check if the server has a neighbor now
            time.sleep(5)
        time.sleep(1)
