import os
import pandas as pd
import time
import networkx as nx
import numpy as np

from ema_workbench import MultiprocessingEvaluator, SequentialEvaluator
from ema_workbench import RealParameter, ScalarOutcome, Constant, Model, ema_logging
from ema_workbench.em_framework.optimization import ArchiveLogger, SingleObjectiveBorgWithArchive

from pydsol.core.simulator import DEVSSimulatorFloat
from pydsol.core.experiment import SingleReplication

from model import InterceptionModel
from network import city_graph
from sort_and_filter import sort_and_filter_pol_fug_Rotterdam as sort_and_filter_nodes
from unit_ranges import unit_ranges

ema_logging.log_to_stderr(ema_logging.INFO)

import sys
sys.setrecursionlimit(10000)

def define_path(d_type, vary_param, run_length, manhattan_diameter, num_fugitive_routes, U, config, file_type):
    directory = os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))
    data_folder = 'simopt'
    data_folder_ = 'data'
    network = 'Rotterdam'
    file_name = f"{d_type}_N{manhattan_diameter}_R{num_fugitive_routes}_U{U}_config{config}.{file_type}"
    path = os.path.join(directory, data_folder, data_folder_, network, vary_param, file_name)

    return path


def evaluate_func(simulator, model, graph, start_police, start_fugitive, route_fugitive, num_fugitive_routes,
                  run_length, seed, labels_sorted, labels_inv_sorted, **kwargs):
    """
    Runs a single replication of the pyDSOL Interception model and returns the objective value.
    """

    police_target = {}
    for key, value in kwargs.items():
        _, u = key.split('_')
        police_target[int(u)] = labels_inv_sorted[int(u)][int(np.floor(value))]

    # generate route of police units from start to target node
    route_police = {u: nx.shortest_path(G=graph, source=start_police[u], target=target, weight='travel_time',
                                        method='bellman-ford') for u, target in police_target.items()}
    # route_police = {u: nx.shortest_path(G=graph, source=start_police[u], target=target) for u, target in police_target.items()}

    run_length = run_length + 2

    replication = SingleReplication(str(0), 0.0, 0.0, run_length)

    # set route police to decision variable values
    model.route_police = route_police

    # initialize simulation
    simulator.initialize(model, replication)

    #run simulation
    simulator.start()

    while simulator.simulator_time < run_length:
        time.sleep(0.01)
    if simulator.simulator_time == run_length:
        time.sleep(0.005)
    num_intercepted = model.get_output_statistics()
    # print(num_intercepted/500)
    model.reset_model()
    simulator.cleanup()

    # print('eval func')

    return [num_intercepted]


def run_optimization(nfe, distance, num_units, config, num_seeds=4, num_fugitive_routes=500,
                     city='Rotterdam', vary_param='units', saving_results=True):
    start_time = 0
    warmup_time = 0
    run_length = int(distance / 5)

    ema_logging.log_to_stderr(ema_logging.INFO)

    for seed in range(num_seeds):
        graph, labels, labels_inv, pos = city_graph(city, distance)

        # import data
        start_police_path = define_path('units_start', vary_param, run_length, distance, num_fugitive_routes,
                                        num_units, config, 'pkl')
        start_police = pd.read_pickle(start_police_path)

        start_fugitive_path = define_path('fugitive_start', vary_param, run_length, distance,
                                          num_fugitive_routes, num_units, config, 'pkl')
        start_fugitive = pd.read_pickle(start_fugitive_path)

        route_fugitive_path = define_path('fugitive_routes', vary_param, run_length, distance,
                                          num_fugitive_routes, num_units, config, 'pkl')
        route_fugitive = pd.read_pickle(route_fugitive_path)

        route_fugitive_lists = []
        for idx, r in enumerate(route_fugitive):
            route = list(r.values())
            route_fugitive_lists.append(route)

        # sort indices on distance to start_fugitive
        labels_perunit_sorted, labels_perunit_inv_sorted, labels_full_sorted = sort_and_filter_nodes(graph,
                                                                                                     start_fugitive,
                                                                                                     route_fugitive,
                                                                                                     start_police,
                                                                                                     run_length)

        # route_fugitive_labeled = []
        # for r in route_fugitive:
        #     r_labeled = [labels_full_sorted[x] for x in r]
        #     route_fugitive_labeled.append(r_labeled)
        #
        # tau_uv = unit_ranges(start_units=start_police, U=num_units, G=graph, L=run_length,
        #                      labels_full_sorted=labels_full_sorted)
        #
        # problem_name = f'T{run_length}_N{distance}_R{num_fugitive_routes}_U{num_units}_config{config}'

        upper_bounds = []
        for u in range(num_units):
            if len(labels_perunit_sorted[u]) <= 1:
                upper_bounds.append(1)
            else:
                upper_bounds.append(len(labels_perunit_sorted[u]) - 1)  # different for each unit

        # initialize model
        simulator = DEVSSimulatorFloat("sim")
        route_police_default = {u: [start_police[u]] for u in range(num_units)}
        pydsol_model = InterceptionModel(simulator=simulator,
                                       input_params={'graph': graph,
                                                     'start_police': start_police,
                                                     'route_police': route_police_default,
                                                     'start_fugitive': start_fugitive,
                                                     'route_fugitive': route_fugitive_lists,
                                                     'num_fugitive_routes': num_fugitive_routes
                                                     },
                                       seed=113)

        model = Model("FIPEMA", function=evaluate_func)

        model.levers = [RealParameter(f"pi_{u}", 0, upper_bounds[u]) for u in range(num_units)]

        model.constants = model.constants = [
            Constant("model", pydsol_model),
            Constant("simulator", simulator),
            Constant("graph", graph),
            Constant("start_police", start_police),
            Constant("start_fugitive", start_fugitive),
            Constant("route_fugitive", route_fugitive_lists),
            Constant("num_fugitive_routes", num_fugitive_routes),
            Constant("run_length", run_length),
            Constant("seed", seed),
            Constant("labels_sorted", labels_perunit_sorted),
            Constant("labels_inv_sorted", labels_perunit_inv_sorted)
        ]

        model.outcomes = [
            ScalarOutcome("pct_intercepted", kind=ScalarOutcome.MAXIMIZE)
        ]

        convergence_metrics = [
            ArchiveLogger(
                f"./results/{city}/{vary_param}",
                [l.name for l in model.levers],
                [o.name for o in model.outcomes if o.kind != o.INFO],
                base_filename=f"archives_N{distance}_U{num_units}_config{config}_seed{seed}.tar.gz"
            ),
        ]


        with SequentialEvaluator(model) as evaluator:
            results = evaluator.optimize(
                algorithm=SingleObjectiveBorgWithArchive,
                nfe=nfe,
                searchover="levers",
                convergence=convergence_metrics,
                convergence_freq=100
            )

        # print(results)


if __name__ == "__main__":
    ema_logging.log_to_stderr(ema_logging.INFO)

    for config in [9]:
        run_optimization(nfe=1000,
                         distance=600,
                         num_units=5,
                         config=config,
                         num_seeds=1,
                         num_fugitive_routes=500,
                         city='Rotterdam',
                         vary_param='nodes',
                         saving_results=True
                         )

    # ArchiveLogger.load_archives(f"results/units/archives_U_{1}_config{0}_seed{0}.tar.gz")
