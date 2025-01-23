import threading

# import auction functions in other files
import broadcast
import leader_election
import heartbeat
import auction_handler

# import global variables
import global_variables

# message definitions
SERVER_DISCOVERY_MESSAGE = {
    "type": "server_discovery",
    "sender_server_uuid": global_variables.server_uuid,
    "server_address": global_variables.s_address,
    "message": "Hello, any servers there?"
}

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("### SERVER SETUP ###")
    print(f"Server UUID: {global_variables.server_uuid}")
    print("=" * 50)

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

    # create a separate thread to run the heartbeat listener
    thread_heartbeat_listener = threading.Thread(
        target=heartbeat.heartbeat_listener)
    thread_heartbeat_listener.start()

    # create a separate thread to run the heartbeat sender
    thread_heartbeat_sender = threading.Thread(
        target=heartbeat.heartbeat_sender)
    thread_heartbeat_sender.start()

    thread_client_listener = threading.Thread(
        target=auction_handler.client_listener)
    thread_client_listener.start()

    # 3. start new leader election
    # server has been started, broadcast message is sent and all listeners are started
    # the new server is successfully integrated into the system so a new leader server is elected
    leader_election.start_leader_election()
