import random


def route_generator(G, L, start_escape_route):
    """
    Generate an escape route from a starting position

    Parameters
    ----------
    G : networkx graph
        graph of size (N,N).
    L : int
        length of escape route.
    start_escape_route : tuple
        starting node of offender.

    Returns
    -------
    walk : list
        escape route (random walk) given starting position.

    """
    walk = []
    # Generate random escape route
    node = start_escape_route
    walk.append(node)

    # previous_node = node

    for i in range(L):  # TODO: take travel_time into account
        list_neighbor = list(G.neighbors(node))

        if i == 0:
            previous_node = node
            nextnode = random.choice(list_neighbor)

        else:
            # exclude previous node for 'normal' walk (only if other choices)
            if len(list_neighbor) > 1:
                if previous_node in list_neighbor:
                    list_neighbor.remove(previous_node)

            # save previous node
            previous_node = node
            nextnode = random.choice(list_neighbor)

        walk.append(nextnode)
        node = nextnode

    return walk
