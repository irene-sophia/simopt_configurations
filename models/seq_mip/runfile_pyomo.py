# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 09:33:56 2021

@author: Irene
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import random
import time
import pickle
import importlib

from pyomo.environ import *
from pyomo.opt import SolverFactory

from graph_manhattan import graph as manhattan_graph

from optimization_FIP_pyomo import optimization, unit_ranges


def fugitive_routes_to_phi_rtv(route_fugitive, labels):
    routes_time_nodes_index = pd.MultiIndex.from_product([range(len(route_fugitive)),
                                                          range(len(route_fugitive[0])), # +1
                                                          labels.values()],
                                                         names=('route', 'time', 'node'))
    routes_time_nodes = pd.DataFrame(index=routes_time_nodes_index, columns=['presence'])

    # Generate multiple walks
    for i in range(len(route_fugitive)):
        walk = route_fugitive[i]
        for t in range(len(walk)):
            routes_time_nodes.loc[(i, t, labels[walk[t]])]['presence'] = 1
    routes_time_nodes = routes_time_nodes.fillna(0)

    # return np.squeeze(routes_time_nodes).to_dict()
    return routes_time_nodes


def run_optimization(nums_units, num_fugitive_routes, manhattan_diameters, num_configs, num_seeds, vary_param):
    for manhattan_diameter in manhattan_diameters:
        for num_units in nums_units:
            run_length = int(5 + (0.5 * manhattan_diameter))

            results_dict = {}
            for config in range(num_configs):
                graph, labels, pos = manhattan_graph(manhattan_diameter)
                # pickle.dump(labels,
                #             open(
                #                 f"results/nodes/debug/labels_T{run_length}_N{manhattan_diameter}_R{num_fugitive_routes}_U{U}_config{config}.pkl",
                #                 'wb'))

                start_police = pd.read_pickle(
                    f"../../simopt/data/grid/{vary_param}/units_start_T{run_length}_N{manhattan_diameter}_R{num_fugitive_routes}_U{num_units}_config{config}.pkl")
                start_fugitive = pd.read_pickle(
                    f"../../simopt/data/grid/{vary_param}/fugitive_start_T{run_length}_N{manhattan_diameter}_R{num_fugitive_routes}_U{num_units}_config{config}.pkl")
                route_fugitive = pd.read_pickle(
                    f"../../simopt/data/grid/{vary_param}/fugitive_routes_T{run_length}_N{manhattan_diameter}_R{num_fugitive_routes}_U{num_units}_config{config}.pkl")

                routes_time_nodes = fugitive_routes_to_phi_rtv(route_fugitive, labels)

                units_range_time = unit_ranges(start_units=start_police, U=num_units, G=graph, L=run_length, labels=labels)

                duration_dict = {}

                for seed in range(num_seeds):
                    random.seed(seed)
                    routes_intercepted, list_unit_nodes, opt_time = optimization(G=graph,
                                                                       U=num_units,
                                                                       routes_time_nodes=routes_time_nodes,
                                                                       units_range_time=units_range_time,
                                                                       R=num_fugitive_routes,
                                                                       V=len(labels),
                                                                       T=run_length,
                                                                       labels=labels)

                    # print('run time in seconds: ', duration)
                    # print('run time in minutes: ', duration/60)
                    # print(list_unit_nodes)

                    duration_dict[seed] = {'elapsed time': opt_time,
                                           'score': sum(routes_intercepted.values()) / num_fugitive_routes}
                    for u, unit_node in enumerate(list_unit_nodes):
                        duration_dict[seed][f'pi_{u}'] = unit_node

                results_dict[config] = duration_dict

            results_df = pd.DataFrame()
            for config, results_config in results_dict.items():
                for seed, results_seed in results_config.items():
                    results_seed_df = pd.DataFrame()
                    for stat in results_seed.keys():
                        results_seed_df[stat] = [results_seed[stat]]

                    results_seed_df['config'] = [config]
                    results_seed_df['seed'] = [seed]

                    results_df = pd.concat([results_df, results_seed_df])

            results_df.to_csv(
                f"results/grid_rep2/{vary_param}/final_solution_T{run_length}_N{manhattan_diameter}_R{num_fugitive_routes}_U{num_units}.csv",
                index=False,
            )


if __name__ == "__main__":
    manhattan_diameters = [10]
    nums_units = [5]
    vary_param = 'nodes'

    run_optimization(nums_units=nums_units,
                     num_fugitive_routes=500,
                     manhattan_diameters=manhattan_diameters,
                     num_configs=1,
                     num_seeds=1,
                     vary_param=vary_param)
