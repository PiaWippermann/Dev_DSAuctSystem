"""
participants_ring.py

File that contains functions to manage the system environment

- form the ring
- update the neighbor

"""

# import global variables
import global_variables


def form_ring():
    """
    Function called by the leader.
    Except for the very first server that comes into the system that will automatically be the leader server after calling this function
    """
    # sort the server_list entries
    # the server_list is an array of uuids
    global_variables.server_list.sort(key=lambda x: x.get("server_uuid"))
    print(f"Sorted server list {global_variables.server_list}")


def update_neighbor(direction='left'):
    """
    Get the current server's neighbor

    """
    current_node_index = -1
    for i in range(len(global_variables.server_list)):
        if global_variables.server_list[i].get("server_uuid") == global_variables.server_uuid:
            current_node_index = i
            break

    if len(global_variables.server_list) == 1:
        # server is the only server so no neighbor is set
        global_variables.neighbor = None
    elif direction == 'left':
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
