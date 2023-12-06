from pydsol.model.link import Link


class Road(Link):
    def __init__(self, simulator, origin, destination, length, selection_weight=1, **kwargs):
        super().__init__(simulator, origin, destination, length, selection_weight, **kwargs)
        self.graph = kwargs['graph']
        self.destination_name = kwargs["destination_name"]
        self.next = kwargs['next']
