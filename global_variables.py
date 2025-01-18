import uuid
import socket

# GLOBAL VARIABLES THAT NEED TO BE ACCESSIBLE IN MULTIPLE FILES

# server address
MY_HOST = socket.gethostname()
s_address = socket.gethostbyname(MY_HOST)

# uuid of the server itself
server_uuid = str(uuid.uuid4())

# uuid of the leader server in the system
leader_server = {
    "leader_server_uuid": "",
    "leader_server_address": None
}

# list of all servers in the system
server_list = [
    {
        "server_uuid": server_uuid,
        "server_address": s_address
    }
]

# uuid of the neighbor server
neighbor = None

# message definitions
ENVIRONMENT_MESSAGE = {
    "type": "environment_update",
    "server_list": server_list,
    "message": "System environment has been updated",
    "sender_server_uuid": server_uuid
}
