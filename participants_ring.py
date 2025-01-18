# File that contains functions regarding forming a participants ring and informing servers in the system about the members in the system
# It also conatins function the receive the neighbor of the server

# IMPORTS

# import global variables
import global_variables


# Function only called by the leader
# Except for the very first server that comes into the system that will automatically be the leader server after calling this function
def form_ring():
    # sort the server_list entries
    # the server_list is an array of uuids
    global_variables.server_list.sort(key=lambda x: x.get("server_uuid"))
    print("Sorted server list {global_variables.server_list}")


# Get the current server's neighbor
def update_neighbor(direction='left'):
    current_node_index = -1
    for i in range(len(global_variables.server_list)):
        if global_variables.server_list[i].get("server_uuid") == global_variables.server_uuid:
            current_node_index = i
            break

    if direction == 'left':
        if current_node_index + 1 == len(global_variables.server_list):
            global_variables.neighbor = global_variables.server_list[0]
        else:
            global_variables.neighbor = global_variables.server_list[current_node_index + 1]
    else:
        if current_node_index == 0:
            global_variables.neighbor = global_variables.server_list[len(
                global_variables.server_list)]
        else:
            global_variables.neighbor = global_variables.server_list[current_node_index - 1]
