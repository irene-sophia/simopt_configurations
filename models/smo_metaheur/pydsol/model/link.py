"""
Created on: 22-7-2021 13:42

@author: IvS
"""
import itertools

from basic_logger import get_module_logger
logger = get_module_logger(__name__)


class Link(object):
    """This class defines a basic link between an origin and destination for a model."""
    id_iter = itertools.count(1)

    def __init__(self, simulator, origin, destination, length, selection_weight=1, **kwargs):
        """

        Parameters
        ----------
        simulator: Simulator object
            simulator of the model.
        origin: object
            origin of the link, i.e., 'from'.
        destination: object
            destination of the link, i.e., 'to'.
        length: int
            length of the link in a distance unit.
        selection_weight: float
            weight expression for the link when selecting a link.
        kwargs:
            kwargs are the keyword arguments that are used to expand the link class.
            *name: str
                user-specified name for the link
        """
        self.simulator = simulator
        self.id = next(self.id_iter)
        self.name = f"{self.__class__.__name__} {str(self.id)}"
        if "name" in kwargs:
            self.name = kwargs["name"]

        self.next = None #is next item

        #TODO origin and destination are optional. Not necessary for modelling
        self.origin = origin
        self.destination = destination

        self.length = float(length)
        self.selection_weight = selection_weight

        self.kwargs = kwargs

    def enter_input_node(self, entity, **kwargs):
        self.enter_link(entity)

    def enter_link(self, entity, **kwargs):
        """Determines the time for travelling on the link by length and speed of the entity, and
        schedules the event for exiting the link.

        Parameters
        ----------
        entity: object
            the target on which a state change is scheduled.
        kwargs:
            kwargs are the keyword arguments that are used to expand the link class.

        """
        relative_delay = self.length/entity.speed

        self.simulator.schedule_event_rel(relative_delay, self, "exit_link", entity=entity)

        logger.debug("Time {0:.2f}: {1} enters {2} from {3} to {4}".format(self.simulator.simulator_time,
                                                                                      entity.name, self.name,
                                                                            self.origin.name, self.destination.name))

    def exit_link(self, entity, **kwargs):
        """Schedules the event for entering the input node of the destination of the link. Each destination needs
        a method "enter_input_node".

        Parameters
        ----------
        entity: object
            the target on which a state change is scheduled.
        kwargs:
            kwargs are the keyword arguments that are used to expand the link class.

        """
        self.next.enter_input_node(entity)


