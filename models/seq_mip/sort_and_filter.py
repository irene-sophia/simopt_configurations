import networkx as nx


def unit_nodes_func(start_police, graph, run_length, U):
    """
    Returns a dict of the reachable nodes within the run length for each unit
    """

    unit_nodes = {}
    for u in range(U):
        unit_nodes[u] = list(nx.single_source_shortest_path_length(G=graph,
                                                                   source=start_police[u],
                                                                   cutoff=run_length
                                                                   ).keys()) + [start_police[u]]

    return unit_nodes


def sort_and_filter_pol_fug(graph, start_fugitive, route_fugitive, start_police, run_length):
    """
    Sorts the nodes of a graph on distance to start_fugitive,
    filters the nodes on reachibility by the fugitive,
    and returns the updated labels
    """

    U = len(start_police)
    unit_nodes = unit_nodes_func(start_police, graph, run_length, U)

    distance_dict = {}
    for node in graph.nodes():
        if nx.has_path(graph, start_fugitive, node):
            distance_dict[node] = nx.shortest_path_length(G=graph,
                                                          source=start_fugitive,
                                                          target=node,
                                                          weight='travel_time',
                                                          method='dijkstra')
        else:
            distance_dict[node] = 42424242

    nx.set_node_attributes(graph, distance_dict, "distance")

    fugitive_nodes = set([num for sublist in route_fugitive for num in sublist])

    labels_perunit_sorted = {}
    labels_perunit_inv_sorted = {}

    for u in range(U):
        police_nodes = set([y for x in [unit_nodes[u]] for y in x])

        node_subset = (list(fugitive_nodes.intersection(police_nodes)))
        if len(node_subset) < 2:
            node_subset = node_subset + [start_police[u]] + [[n for n in graph.neighbors(start_police[u])][0]]

        subgraph = graph.subgraph(nodes=node_subset)

        labels_perunit_sorted[u] = {node: index for index, node in
                                    enumerate(sorted(subgraph.nodes(), key=lambda n: subgraph.nodes[n]['distance']))}
        labels_perunit_inv_sorted[u] = {index: node for index, node in enumerate(
            sorted(subgraph.nodes(), key=lambda n: subgraph.nodes[n]['distance']))}

    all_police_nodes = set()
    for u in range(U):
        all_police_nodes.update(set([y for x in [unit_nodes[u]] for y in x]))

    # node_subset_full = (list(fugitive_nodes.intersection(all_police_nodes)))  # was union!
    # if len(node_subset_full) == 0:  # als geen kruispunten om op te onderscheppen - misschien gewoon error gooien?
    #     node_subset_full = (list(fugitive_nodes.union(all_police_nodes)))
    node_subset_full = (list(fugitive_nodes.union(all_police_nodes)))

    subgraph_full = graph.subgraph(nodes=node_subset_full)
    labels_full_sorted = {node: index for index, node in
                          enumerate(sorted(subgraph_full.nodes(), key=lambda n: subgraph_full.nodes[n]['distance']))}

    return labels_perunit_sorted, labels_perunit_inv_sorted, labels_full_sorted


def sort_and_filter_pol_fug_Rotterdam(graph, start_fugitive, route_fugitive, start_police, run_length):
    """
    Sorts the nodes of a graph on distance to start_fugitive,
    filters the nodes on reachibility by the fugitive,
    and returns the updated labels
    """

    U = len(start_police)
    unit_nodes = unit_nodes_func(start_police, graph, run_length, U)

    distance_dict = {}
    for node in graph.nodes():
        if nx.has_path(graph, start_fugitive, node):
            distance_dict[node] = nx.shortest_path_length(G=graph,
                                                          source=start_fugitive,
                                                          target=node,
                                                          weight='travel_time',
                                                          method='dijkstra')
        else:
            distance_dict[node] = 42424242

    nx.set_node_attributes(graph, distance_dict, "distance")

    fugitive_nodes = set()
    for r, sublist in enumerate(route_fugitive):
        fugitive_nodes.update(set(sublist.values()))
    # fugitive_nodes = set([num for sublist in route_fugitive for num in sublist])

    labels_perunit_sorted = {}
    labels_perunit_inv_sorted = {}

    for u in range(U):
        police_nodes = set([y for x in [unit_nodes[u]] for y in x])

        node_subset = (list(fugitive_nodes.intersection(police_nodes)))
        if len(node_subset) < 2:
            node_subset = node_subset + [start_police[u]] + [[n for n in graph.neighbors(start_police[u])][0]]

        subgraph = graph.subgraph(nodes=node_subset)

        labels_perunit_sorted[u] = {node: index for index, node in
                                    enumerate(sorted(subgraph.nodes(), key=lambda n: subgraph.nodes[n]['distance']))}
        labels_perunit_inv_sorted[u] = {index: node for index, node in enumerate(
            sorted(subgraph.nodes(), key=lambda n: subgraph.nodes[n]['distance']))}

    all_police_nodes = set()
    for u in range(U):
        all_police_nodes.update(set([y for x in [unit_nodes[u]] for y in x]))

    # node_subset_full = (list(fugitive_nodes.intersection(all_police_nodes)))  # was union!
    # if len(node_subset_full) == 0:  # als geen kruispunten om op te onderscheppen - misschien gewoon error gooien?
    #     node_subset_full = (list(fugitive_nodes.union(all_police_nodes)))
    node_subset_full = (list(fugitive_nodes.union(all_police_nodes)))
    subgraph_full = graph.subgraph(nodes=node_subset_full)
    labels_full_sorted = {node: index for index, node in
                          enumerate(sorted(subgraph_full.nodes(), key=lambda n: subgraph_full.nodes[n]['distance']))}

    return labels_perunit_sorted, labels_perunit_inv_sorted, labels_full_sorted


def sort_nodes(graph, start_fugitive):
    """
    Sorts the nodes of a graph on distance to start_fugitive and returns the updated labels
    """

    distance_dict = {}
    for node in graph.nodes():
        distance_dict[node] = nx.shortest_path_length(
            G=graph,
            source=start_fugitive,
            target=node,
            weight="travel_time",
            method="dijkstra",
        )

    nx.set_node_attributes(graph, distance_dict, "distance")

    labels_sorted = {
        node: index
        for index, node in enumerate(
            sorted(graph.nodes(), key=lambda n: graph.nodes[n]["distance"])
        )
    }
    labels_inv_sorted = {
        index: node
        for index, node in enumerate(
            sorted(graph.nodes(), key=lambda n: graph.nodes[n]["distance"])
        )
    }

    return labels_sorted, labels_inv_sorted, labels_sorted


def filter_pol_fug(graph, start_fugitive, route_fugitive, start_police, run_length):
    """
    Filters the nodes on reachibility by the fugitive,
    and returns the updated labels
    """

    U = len(start_police)
    unit_nodes = unit_nodes_func(start_police, graph, run_length, U)

    distance_dict = {}
    for node in graph.nodes():
        if nx.has_path(graph, start_fugitive, node):
            distance_dict[node] = nx.shortest_path_length(G=graph,
                                                          source=start_fugitive,
                                                          target=node,
                                                          weight='travel_time',
                                                          method='dijkstra')
        else:
            distance_dict[node] = 42424242

    nx.set_node_attributes(graph, distance_dict, "distance")

    fugitive_nodes = set([num for sublist in route_fugitive for num in sublist])

    labels_perunit_sorted = {}
    labels_perunit_inv_sorted = {}

    for u in range(U):
        police_nodes = set([y for x in [unit_nodes[u]] for y in x])

        node_subset = (list(fugitive_nodes.intersection(police_nodes)))
        if len(node_subset) < 2:
            node_subset = node_subset + [start_police[u]] + [[n for n in graph.neighbors(start_police[u])][0]]

        subgraph = graph.subgraph(nodes=node_subset)

        labels_perunit_sorted[u] = {node: index for index, node in enumerate(subgraph.nodes())}
        labels_perunit_inv_sorted[u] = {index: node for index, node in enumerate(subgraph.nodes())}

    all_police_nodes = set()
    for u in range(U):
        all_police_nodes.update(set([y for x in [unit_nodes[u]] for y in x]))

    # node_subset_full = (list(fugitive_nodes.intersection(all_police_nodes)))  # was union!
    # if len(node_subset_full) == 0:  # als geen kruispunten om op te onderscheppen - misschien gewoon error gooien?
    #     node_subset_full = (list(fugitive_nodes.union(all_police_nodes)))
    node_subset_full = (list(fugitive_nodes.union(all_police_nodes)))
    subgraph_full = graph.subgraph(nodes=node_subset_full)
    labels_full_sorted = {node: index for index, node in enumerate(subgraph_full.nodes())}

    return labels_perunit_sorted, labels_perunit_inv_sorted, labels_full_sorted
