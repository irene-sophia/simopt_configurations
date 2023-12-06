from pydsol.model.source import Source
from model_elements.entities import Police


class SourcePolice(Source):
    def __init__(self, simulator, interarrival_time="default", num_entities=1, **kwargs):
        super().__init__(simulator, interarrival_time, num_entities, **kwargs)

        self.graph = kwargs['graph']
        self.location = kwargs['location']
        self.route_police = kwargs['route']
        self.list_police = []
        self.entity_type = Police
        #self.next = kwargs['next']

    def exit_source(self, entity, **kwargs):
        super().exit_source(entity, **kwargs)

        entity.route = self.route_police
        entity.route_planned = self.route_police

        #list of Police entities
        self.list_police.append(entity)

