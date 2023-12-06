from pydsol.model.source import Source
from model_elements.entities import Fugitive


class SourceFugitive(Source):
    def __init__(self, simulator, interarrival_time="default", num_entities=1, **kwargs):
        super().__init__(simulator, interarrival_time, num_entities, **kwargs)

        self.graph = kwargs['graph']
        self.location = kwargs['location']
        self.route_fugitive = kwargs['route'].copy()

        self.entity_type = Fugitive
        self.entities_created = None

    def exit_source(self, entity, **kwargs):
        super().exit_source(entity, **kwargs)

        entity.route = self.route_fugitive.copy()
        entity.route_planned = self.route_fugitive.copy()

        self.entities_created = entity

