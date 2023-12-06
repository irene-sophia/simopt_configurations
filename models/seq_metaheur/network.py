import networkx as nx


# import osmnx as ox


def manhattan_graph(N):
    """
    Generate manhattan graph

    Parameters
    ----------
    N : int
        width of graph.

    Returns
    -------
    G : networkx graph
        graph of size (N,N).
    labels : dict
        {pos: vertex number}.
    pos : dict
        {vertex:pos}.

    """

    G = nx.grid_2d_graph(N, N)

    # set x and y
    i = 0
    locations = {}
    for u, v in G.nodes():
        locations[(u, v)] = {"x": u, "y": v}
        i += 1
    nx.set_node_attributes(G, locations)

    # set travel time (unidistant)
    travel_time = 1
    nx.set_edge_attributes(G, travel_time, "travel_time")

    pos = dict((n, n) for n in G.nodes())
    labels = dict(((i, j), i * N + j) for i, j in G.nodes())  #
    labels_inv = dict((i * N + j, (i, j)) for i, j in G.nodes())

    return G, labels, labels_inv, pos


def city_graph(city, distance):
    filepath = f"graphs/Graph_{city}_{distance}.graph.graphml"

    graph = nx.read_graphml(path=filepath, node_type=int, edge_key_type=float)

    for u, v in graph.edges():
        for i in graph[u][v]:  # if multiple edges between nodes u and v
            graph[u][v][i]['travel_time'] = float(graph[u][v][i]['travel_time'])

    labels = {}
    labels_inv = {}
    for i, node in enumerate(graph.nodes()):
        labels[node] = i
        labels_inv[i] = node

    return graph, labels, labels_inv, {}

# G, labels, labels_inv, pos = manhattan_graph(10)
# graph, labels, labels_inv, pos = rotterdam_graph(800)
