from enum import Flag
from typing import Set, Dict, Callable
from datetime import datetime


class RelationType(Flag):
    I = 'include'
    E = 'exclude'
    R = 'response'
    N = 'noResponse'
    S = 'spawn'
    V = 'setValue'
    C = 'condition'
    M = 'milestone'
    EFFECTS = I | E | R | N | S | V
    CONSTRAINTS = C | M


class DcrElement:
    
    def __init__(self, id, parents=None, isTemplate=False):
        self.__id = id
        self.__parents = set() if parents is None else parents
        self.__template = isTemplate

    @property
    def ID(self) -> str:
        return self.__id
    
    @ID.setter
    def ID(self, value: str):
        self.__id = value

    @property
    def parents(self) -> Set['DcrElement']:
        return self.__parents
    
    @parents.setter
    def parents(self, value: Set['DcrElement']):
        self.__parents = value

    @property
    def isTemplate(self) -> bool:
        return self.__template
    
    @isTemplate.setter
    def isTemplate(self, value: bool):
        self.__template = value


class DcrActivity(DcrElement):
    
    def __init__(self, id, parents=None, expression=None, template=None, isTemplate=False):
        super().__init__(id, parents, isTemplate)
        self.__included = True if template is None else template.included
        self.__pending = False if template is None else template.pending
        self.__executed = None if template is None else template.executed # set as None or a datetime denoting execution time. Not currently used but for compatability with timed graphs.
        self.__expression = expression if template is None else template.expression
        self.__data = None

    @property
    def included(self) -> bool:
        return self.__included
    
    @included.setter
    def included(self, value: bool):
        self.__included = value

    @property
    def pending(self) -> bool:
        return self.__pending
    
    @pending.setter
    def pending(self, value: bool):
        self.__pending = value

    @property
    def executed(self) -> datetime:
        return self.__executed
    
    @executed.setter
    def executed(self, value: datetime):
        self.__executed = value

    @property
    def deadline(self) -> datetime:
        return self.__deadline
    
    @deadline.setter
    def deadline(self, value: datetime):
        self.__deadline = value

    @property
    def expression(self) -> Callable:
        return self.__expression

    @property
    def data(self) -> any:
        return self.__data
    
    @data.setter
    def data(self, value: any):
        self.__data = value
    



class DcrNesting(DcrElement):
    
    def __init__(self, id, parents=None, children=None, isTemplate=False):
        super().__init__(id, parents, isTemplate)
        self.__children = set() if children is None else children

    @property
    def children(self) -> Set[DcrElement]:
        return self.__children
    
    @children.setter
    def children(self, value: Set[DcrElement]):
        self.__children = value


class DcrSubProcess(DcrActivity):
    
    def __init__(self, id, parents=None, children=None, expression=None, template=None, isTemplate=False):
        super().__init__(id, parents, expression, template, isTemplate)
        self.__children = set() if children is None else children

    @property
    def children(self) -> Set[DcrElement]:
        return self.__children
    
    @children.setter
    def children(self, value: Set[DcrElement]):
        self.__children = value


class DcrRelation:
    
    def __init__(self, type, source, target, guard=None, isTemplate=False):
        self.__relationType = type
        self.__source = source
        self.__target = target
        self.__guard = guard
        self.__template = isTemplate

    @property
    def relationType(self) -> RelationType:
        return self.__relationType
    
    @relationType.setter
    def relationType(self, value: RelationType):
        self.__relationType = value

    @property
    def source(self) -> DcrElement:
        return self.__source
    
    @source.setter
    def source(self, value: DcrElement):
        self.__source = value

    @property
    def target(self) -> DcrElement:
        return self.__target
    
    @target.setter
    def target(self, value: DcrElement):
        self.__target = value

    @property
    def guard(self) -> bool:
        return self.__guard
    
    @guard.setter
    def guard(self, value: bool):
        self.__guard = value

    @property
    def isTemplate(self) -> bool:
        return self.__template
    
    @isTemplate.setter
    def isTemplate(self, value: bool):
        self.__template = value


class DcrGraph:
    
    def __init__(self, id, template=None, isTemplate=False):
        self.__id = id
        self.__events = set() if template is None else template.events
        self.__activities = set() if template is None else template.activities
        self.__activityMap = {} if template is None else template.labelMapping
        self.__nestings = set() if template is None else template.nestings
        self.__subprocesses = set() if template is None else template.subprocesses
        self.__subgraphs = set() if template is None else template.subgraphs
        self.__relations = set() if template is None else template.relations
        self.__template = isTemplate

    @property
    def ID(self) -> str:
        return self.__id
    
    @ID.setter
    def ID(self, value: str):
        self.__id = value

    @property
    def events(self) -> Set[str]:
        return self.__events

    @events.setter
    def events(self, value: Set[str]):
        self.__events = value

    @property
    def activities(self) -> Set[DcrActivity]:
        return self.__activities

    @activities.setter
    def labels(self, value: Set[DcrActivity]):
        self.__activities = value

    @property
    def activity_map(self) -> Dict[str, DcrActivity]:
        return self.__activityMap

    @activity_map.setter
    def activity_map(self, value: Dict[str, str]):
        self.__activityMap = value

    @property
    def nestings(self) -> Set[DcrNesting]:
        return self.__nestings
    
    @nestings.setter
    def nestings(self, value: Set[DcrNesting]):
        self.__nestings = value

    @property
    def subprocesses(self) -> Set[DcrSubProcess]:
        return self.__subprocesses
    
    @subprocesses.setter
    def subprocesses(self, value: Set[DcrSubProcess]):
        self.__subprocesses = value

    @property
    def subgraphs(self) -> Set['DcrGraph']:
        return self.__subgraphs
    
    @subgraphs.setter
    def subgraphs(self, value: Set['DcrGraph']):
        self.__subgraphs = value

    @property
    def relations(self) -> Set[DcrRelation]:
        return self.__relations
    
    @relations.setter
    def relations(self, value: Set[DcrRelation]):
        self.__relations = value

    @property
    def isTemplate(self) -> bool:
        return self.__template
    
    @isTemplate.setter
    def isTemplate(self, value: bool):
        self.__template = value

    def get_event(self, activity: DcrActivity) -> str:
        """
        Get the event ID of an activity from graph.

        Parameters
        ----------
        activity
            the activity of an event

        Returns
        -------
        event
            the event ID of activity
        """
        for event, dcrActivity in self.activity_map.items():
            if activity == dcrActivity:
                return event

    def get_activity(self, event: str) -> DcrActivity:
        """
        get the activity of an Event

        Parameters
        ----------
        event
            event ID

        Returns
        -------
        activity
            the activity of the event
        """
        return self.activity_map[event]

    def get_constraints(self) -> int:
        """
        compute constraints in DCR Graph

        Returns
        -------
        no
            number of constraints
        """
        return len(self.__relations)


    """
    def __repr__(self):
        string = ""
        for key, value in vars(self).items():
            string += str(key.split("_")[-1])+": "+str(value)+"\n"
        return string

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.conditions == other.conditions and self.responses == other.responses and self.includes == other.includes and self.excludes == other.excludes

    def __lt__(self, other):
        return str(self.obj) < str(other.obj)

    def __getitem__(self, item):
        for key, value in vars(self).items():
            if item == key.split("_")[-1]:
                return value
        return set()

    def __setitem__(self, item, value):
        for key,_ in vars(self).items():
            if item == key.split("_")[-1]:
                setattr(self, key, value)
    """