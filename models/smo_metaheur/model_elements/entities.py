import itertools

from pydsol.model.entities import Entity


class Fugitive(Entity):
    id_iter_fug = itertools.count(1)

    def __init__(self, simulator, speed=1, route=None, **kwargs):
        super().__init__(simulator, speed=1, t=simulator.simulator_time, **kwargs)

        self.name = f"{self.__class__.__name__} {str(next(self.id_iter_fug))}"
        self.route = route
        self.route_planned = route
        self.intercepted = 0
        self.output_route = {}


class Police(Entity):
    id_iter_pol = itertools.count(1)

    def __init__(self, simulator, speed=1, route=None, **kwargs):
        super().__init__(simulator, speed=1, t=simulator.simulator_time, **kwargs)

        self.name = f"{self.__class__.__name__} {str(next(self.id_iter_pol))}"
        self.route = route
        self.route_planned = route
        self.output_route = {}
