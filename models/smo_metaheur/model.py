import itertools

import numpy as np

from model_elements.entities import Fugitive, Police
from model_elements.intersection import Intersection
from model_elements.road import Road
from model_elements.source_fugitive import SourceFugitive
from model_elements.source_police import SourcePolice
from pydsol.core.model import DSOLModel
from pydsol.model.entities import Entity
from pydsol.model.server import Server
from pydsol.model.sink import Sink
from pydsol.model.source import Source


class InterceptionModel(DSOLModel):
    def __init__(self, simulator, input_params, seed=None):
        super().__init__(simulator)
        self.seed = seed

        self.input_params = input_params
        self.graph = input_params['graph']
        self.start_police = input_params['start_police']
        self.route_police = input_params['route_police']
        self.start_fugitive = input_params['start_fugitive']
        self.route_fugitive = input_params['route_fugitive']
        self.num_fugitive_routes = input_params['num_fugitive_routes']

        self.num_intercepted = 0
        self.pct_intercepted = 0

        # construct graph
        self.components = []
        self.sources = []
        self.source_fugitive = []
        self.source_police = []
        self.roads = []
        self.roads_from_sources = []

        self.construct_nodes()  # construct intersections
        self.construct_links()  # construct roads

    def construct_nodes(self):
        for node, data in self.graph.nodes(data=True):
            locX = data["x"]
            locY = data["y"]

            component = Intersection(simulator=self.simulator,
                                     location="(" + str(locX) + "," + str(locY) + ")",
                                     name=node,
                                     graph=self.graph)

            self.components.append(component)

    def construct_links(self):
        for i, (u, v, data) in enumerate(self.graph.edges(data=True)):  # TODO delete when importing
            origin = next((x for x in self.components if x.name == u), None)
            destination = next((x for x in self.components if x.name == v), None)

            road = Road(simulator=self.simulator,
                        origin=origin,
                        destination=destination,
                        destination_name=v,
                        length=data['travel_time'],
                        selection_weight=1,
                        graph=self.graph,
                        next=destination
                        )

            self.roads.append(road)

            road_reverse = Road(simulator=self.simulator,
                                origin=destination,
                                destination=origin,
                                destination_name=u,
                                length=data['travel_time'],
                                selection_weight=1,
                                graph=self.graph,
                                next=origin
                                )

            self.roads.append(road_reverse)

        for node, data in self.graph.nodes(data=True):
            component = next((x for x in self.components if x.name == node), None)
            if type(component) == Intersection:
                component.next = [x for x in self.roads if x.origin == component]

    def construct_sources(self):
        self.sources = []
        self.source_fugitive = []
        self.source_police = []

        # police
        for u in range(len(self.start_police)):
            route = self.route_police[u].copy()
            node = self.start_police[u]
            locX = self.graph.nodes(data=True)[node]["x"]
            locY = self.graph.nodes(data=True)[node]["y"]

            component = SourcePolice(simulator=self.simulator,
                                     location="(" + str(locX) + "," + str(locY) + ")",
                                     name=node,
                                     interarrival_time=10000000,
                                     num_entities=1,
                                     graph=self.graph,
                                     route=route
                                     )

            self.sources.append(component)
            self.source_police.append(component)

            # print('sources: ', len(self.sources))
            # print('source police: ', len(self.source_police))

            # ADD EDGES FROM SOURCES TO SOURCE LOCATIONS OF LENGTH 0
            origin = component
            destination = next((x for x in self.components if x.name == node), None)

            road = Road(simulator=self.simulator,
                        origin=origin,
                        destination=destination,
                        destination_name=node,
                        length=0.001,
                        selection_weight=1,
                        graph=self.graph,
                        next=destination
                        )
            component.next = road
            self.roads_from_sources.append(road)
            # print('roads: ', len(self.roads))

        # fugitive
        for fug in range(self.num_fugitive_routes):
            route = self.route_fugitive[fug].copy()
            node = self.start_fugitive
            locX = self.graph.nodes(data=True)[node]["x"]
            locY = self.graph.nodes(data=True)[node]["y"]

            component = SourceFugitive(simulator=self.simulator,
                                       location="(" + str(locX) + "," + str(locY) + ")",
                                       name=node,
                                       interarrival_time=10000000,
                                       num_entities=1,
                                       graph=self.graph,
                                       route=route
                                       )
            self.sources.append(component)
            self.source_fugitive.append(component)

            # ADD EDGES FROM SOURCES TO SOURCE LOCATIONS OF LENGTH 0
            origin = component
            destination = next((x for x in self.components if x.name == self.start_fugitive), None)

            road = Road(simulator=self.simulator,
                        origin=origin,
                        destination=destination,
                        destination_name=self.start_fugitive,
                        length=0.001,
                        selection_weight=1,
                        graph=self.graph,
                        next=destination
                        )

            component.next = road
            self.roads_from_sources.append(road)

    def construct_model(self):
        self.reset_model()
        np.random.seed(self.seed)

        self.construct_sources()  # construct sources

        # reset police_on_node tally
        for intersection in [x for x in self.components if isinstance(x, Intersection)]:
            intersection.police_on_node = 0
            intersection.intercepted_on_node = 0
        # self.source_fugitive = [x for x in self.sources if isinstance(x, SourceFugitive)]
        # self.source_police = [x for x in self.sources if isinstance(x, SourcePolice)]

    @staticmethod
    def reset_model():
        classes = [Source, Sink, Server, Entity, SourcePolice, SourceFugitive, Police,
                   Fugitive]  # Road, Intersection,

        for i in classes:
            i.id_iter = itertools.count(1)

        # Intersection.id_iter = itertools.count(1)
        # SourceFugitive.id_iter = itertools.count(1)
        # SourcePolice.id_iter = itertools.count(1)
        # Road.id_iter = itertools.count(1)
        # Fugitive.id_iter = itertools.count(1)
        # Police.id_iter_pol = itertools.count(1)
        # Fugitive.id_iter_fug = itertools.count(1)
        # Link.id_iter = itertools.count(1)

    def get_output_statistics(self):
        self.simulator._eventlist.clear()

        for road in self.roads_from_sources:
            del road
        self.roads_from_sources = []

        # delete fugitives and sources
        list_fugitives = []
        for source in self.source_fugitive:
            list_fugitives.append(source.entities_created)
            del source

        self.num_intercepted = sum([fugitive.intercepted for fugitive in list_fugitives])  # TODO model.num_intercepted
        self.pct_intercepted = (self.num_intercepted / self.num_fugitive_routes) * 100

        del list_fugitives

        # print('pct intercepted: ', pct_intercepted)
        return self.num_intercepted

    @staticmethod
    def save(obj):
        return (obj.__class__, obj.__dict__)

    @staticmethod
    def restore(cls, attributes):
        obj = cls.__new__(cls)
        obj.__dict__.update(attributes)
        return obj
