import math

import logging
from basic_logger import get_module_logger
logger = get_module_logger(__name__, level=logging.INFO)

from pydsol.model.node import Node
from model_elements.entities import Police, Fugitive


class Intersection(Node):
    def __init__(self, simulator, capacity=math.inf, **kwargs):
        super().__init__(simulator, **kwargs)
        self.location = kwargs['location']
        self.graph = kwargs['graph']
        self.simulator = simulator
        # self.route = kwargs['route']
        self.next = None

        self.intercepted_on_node = 0
        self.police_on_node = 0


    def enter_input_node(self, entity, **kwargs):
        super().enter_input_node(entity, **kwargs)
        logger.debug(f"Time {self.simulator.simulator_time:.2f}: Entity: {entity.name} entered node{self.name}")

        #save route
        entity.output_route[self.simulator.simulator_time] = self.name

        if type(entity) == Police:
            if len(entity.route_planned) <= 1:  # arrived at target node
                self.police_on_node += 1

        if all([type(entity) == Fugitive, self.police_on_node > 0]):
            if entity.intercepted == 0:
                entity.intercepted = 1
                self.intercepted_on_node += 1
                logger.debug(f"Time {self.simulator.simulator_time:.2f}: {entity.name} was intercepted at {self.name}")


    def exit_output_node(self, entity, **kwargs):
        assert self.name == entity.route_planned[0]

        if len(entity.route_planned) <= 1:  # reached destination node
            if type(entity) == Police:
                logger.debug(f"Time {self.simulator.simulator_time:.2f}: {entity.name} has reached destination node {self.name}")
                pass
            else:
                pass

        elif self.name == entity.route_planned[1]:  # next node is the current node; i.e., posting
            entity.route_planned.pop(0)
            self.simulator.schedule_event_rel(1, self, "enter_input_node", entity=entity)

            if type(entity) == Police:
                logger.debug(f"Time {self.simulator.simulator_time:.2f}: {entity.name} is posting at node {self.name}")
                pass
            else:
                pass

        else:
            try:
                entity.route_planned.pop(0)  # remove current node from planned route
                next_node = entity.route_planned[0]

                for link in self.next:
                    if link.destination_name == next_node:
                        destination_link = link
                        destination_link.enter_link(entity)  # stel er zijn twee links naar de next_node gaat het hier mis -> break na deze if

                        # if type(entity) == Police:
                        #     self.police_on_node -= 1

                        logger.debug("Time {0:.2f}: Entity: {1} exited node{2}".format(self.simulator.simulator_time,
                                                                                      entity.name, self.name))
                        break

                if 'destination_link' not in locals():
                    raise Exception(f'The destination node {next_node} of {entity.name} is not an output link of the current node {self.name}')

                #del destination_link

            except AttributeError:
                raise AttributeError(f"{self.name} has no output link")






