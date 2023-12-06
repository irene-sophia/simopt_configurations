import os

import numpy as np
import pandas as pd
from ema_workbench import MultiprocessingEvaluator
from ema_workbench import RealParameter, ScalarOutcome, Constant, Model
from ema_workbench.em_framework.optimization import ArchiveLogger, SingleObjectiveBorgWithArchive

from pydsol_borg.network import city_graph
from pydsol_borg.sort_and_filter import sort_and_filter_pol_fug as sort_and_filter_nodes
from pydsol_borg.unit_ranges import unit_ranges


def define_path(d_type, vary_param, city, distance, run_length, num_fugitive_routes, num_units, config, file_type):
    directory = os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))
    data_folder = 'simopt'
    data_folder_ = 'data'
    file_name = f"{d_type}_N{distance}_R{num_fugitive_routes}_U{num_units}_config{config}.{file_type}"
    path = os.path.join(directory, data_folder, data_folder_, city, vary_param, file_name)

    return path


def FIP_model(route_fugitive_labeled=None, run_length=None, tau_uv=None, labels_full_sorted=None, labels_sorted=None,
              labels_sorted_inv=None,
              **kwargs):
    print('eval')
    pi_uv = {}
    z_r = {}
    pi_nodes = []

    for u, value in enumerate(list(kwargs.values())):
        associated_node = labels_sorted_inv[int(u)][int(np.floor(value))]
        universal_node_number = labels_full_sorted[associated_node]

        # construct pi_uv
        # for v in labels_full_sorted.values():
        #     if v == universal_node_number:
        #         pi_uv[int(u), int(v)] = 1
        #     else:
        #         pi_uv[int(u), int(v)] = 0

        pi_nodes.append(labels_full_sorted[associated_node])

    for i_r, _ in enumerate(route_fugitive_labeled):
        z_r[i_r] = 0

    for i_r, r in enumerate(route_fugitive_labeled):  # for each route
        if any([node in pi_nodes for node in r.values()]):
            for u, pi in enumerate(pi_nodes):  # for each police unit
                for time_at_node_fugitive, node_fugitive in r.items():  # for each node in the fugitive route
                    if node_fugitive == pi:  # if the fugitive node is the same as the target node of the police unit
                        if time_at_node_fugitive > tau_uv[u, node_fugitive]:  # and the police unit can reach that node
                            z_r[i_r] = 1  # intercepted

    # print(sum(z_r.values())/500)

    # for r in range(len(route_fugitive_labeled)):
    #     z_r[r] = sum(sum(sum(pi_uv[u, v] * phi_rt[r, t, v] * tau_uv[u, t, v] for v in labels_full_sorted.values()) for u in range(U)) for t in range(run_length))

    print(float(sum(z_r.values())))
    return [float(sum(z_r.values()))]


if __name__ == "__main__":
    start_time = 0
    warmup_time = 0
    distance = 1400
    num_units = 1
    num_configs = 1
    config = 0
    num_seeds = 1
    num_fugitive_routes = 500
    run_length = int(distance / 5)
    city = 'Rotterdam'
    vary_param = 'units'

    graph, labels, labels_inv, pos = city_graph(city, distance)

    # import data
    start_police_path = define_path('units_start', vary_param, city, distance, run_length, num_fugitive_routes,
                                    num_units, config, 'pkl')
    start_police = pd.read_pickle(start_police_path)

    start_fugitive_path = define_path('fugitive_start', vary_param, city, distance, run_length, num_fugitive_routes,
                                      num_units, config, 'pkl')
    start_fugitive = pd.read_pickle(start_fugitive_path)

    route_fugitive_path = define_path('fugitive_routes', vary_param, city, distance, run_length, num_fugitive_routes,
                                      num_units, config, 'pkl')
    route_fugitive = pd.read_pickle(route_fugitive_path)
    print('imported data')

    # sort indices on distance to start_fugitive
    labels_perunit_sorted, labels_perunit_inv_sorted, labels_full_sorted = sort_and_filter_nodes(graph,
                                                                                                 start_fugitive,
                                                                                                 route_fugitive,
                                                                                                 start_police,
                                                                                                 run_length)
    print('sorted')
    route_fugitive_labeled = []
    for r in route_fugitive:
        r_labeled = {x: labels_full_sorted[y] for x, y in r.items()}
        route_fugitive_labeled.append(r_labeled)

    tau_uv = unit_ranges(start_units=start_police, U=num_units, G=graph, L=run_length,
                         labels_full_sorted=labels_full_sorted)
    print('tau_uv')
    # problem_name = f'T{run_length}_N{manhattan_diameter}_R{num_fugitive_routes}_U{num_units}_config{config}'

    upper_bounds = []
    for u in range(num_units):
        if len(labels_perunit_sorted[u]) <= 1:
            upper_bounds.append(1)
        else:
            upper_bounds.append(len(labels_perunit_sorted[u]) - 1)  # different for each unit

    model = Model("FIPEMA", function=FIP_model)

    model.levers = [RealParameter(f"pi_{u}", 0, upper_bounds[u]) for u in range(num_units)]

    model.constants = model.constants = [
        Constant("route_fugitive_labeled", route_fugitive_labeled),
        Constant("run_length", run_length),
        Constant("tau_uv", tau_uv),
        Constant("labels_full_sorted", labels_full_sorted),
        Constant("labels_sorted", labels_perunit_sorted),
        Constant("labels_sorted_inv", labels_perunit_inv_sorted)
    ]

    model.outcomes = [
        ScalarOutcome("pct_intercepted", kind=ScalarOutcome.MAXIMIZE)
    ]


    convergence_metrics = [
        ArchiveLogger(
            f'./results/{vary_param}',
            [l.name for l in model.levers],
            [o.name for o in model.outcomes if o.kind != o.INFO],
        ),
    ]

    with MultiprocessingEvaluator(model) as evaluator:
        results = evaluator.optimize(
            algorithm=SingleObjectiveBorgWithArchive,
            nfe=1000,
            searchover="levers",
            convergence=convergence_metrics,
            convergence_freq=100
        )

    # with MultiprocessingEvaluator(model) as evaluator:
    #     results = evaluator.perform_experiments(policies=100)

    # with SequentialEvaluator(model) as evaluator:
    #     results = evaluator.perform_experiments(policies=100)

    print(results)
