"""
Global variables accessible in all files

"""

import uuid
import socket

is_client = False

# server address
MY_HOST = socket.gethostname()
s_address = socket.gethostbyname(MY_HOST)

# uuid of the client
server_uuid = str(uuid.uuid4())

# uuid of the client
client_address = ""

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

# auction related data
is_auction_active = False
active_auction_element = {
    "client_address": "",
    "element_name": "",
    "highest_bid": 0,
    "bid_owner_client_address": ""
}
