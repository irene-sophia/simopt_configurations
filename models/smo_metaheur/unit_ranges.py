import networkx as nx
import numpy as np
import pandas as pd


def unit_ranges(start_units, U, G, L, labels_full_sorted):
    # units_range_index = pd.MultiIndex.from_product(
    #     [range(U), range(L), labels.values()], names=("unit", "time", "node")
    # )
    # units_range_time = pd.DataFrame(index=units_range_index, columns=["inrange"])

    units_range_index = pd.MultiIndex.from_product(
        [range(U), range(len(labels_full_sorted))], names=("unit", "vertex")
    )
    units_range_time = pd.DataFrame(index=units_range_index, columns=["time_to_reach"])

    for u in range(U):
        for v in labels_full_sorted:
            # neighbors = list(
            #     nx.single_source_shortest_path_length(
            #         G, source=start_units[u], cutoff=t
            #     ).keys()
            # )
            # for neighbor in neighbors:
            #     if (
            #         neighbor in labels.keys()
            #     ):  # anders niet in range van fugitive, en dus geen goede target node
            #         units_range_time.loc[(u, t, labels[neighbor])]["inrange"] = 1

            if nx.has_path(G, start_units[u], v):
                units_range_time.loc[(u, labels_full_sorted[v])] = nx.shortest_path_length(G,
                                                                                           source=start_units[u],
                                                                                           target=v,
                                                                                           weight='travel_time',
                                                                                           method='bellman-ford')
            else:
                units_range_time.loc[(u, labels_full_sorted[v])] = 424242

    units_range_time = units_range_time.fillna(0)

    return np.squeeze(units_range_time).to_dict()



