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
    
    def __init__(self, id, parents=None, template=None, isTemplate=False):
        self.__id = id
        self.__parents = [] if parents is None else parents
        self.__parentsIncluded = True if template is None else template.parentsIncluded
        self.__childrenPending = False if template is None else template.childrenPending
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
    def parentsIncluded(self) -> bool:
        return self.__parentsIncluded
    
    @parentsIncluded.setter
    def parentsIncluded(self, value: bool):
        self.__parentsIncluded = value

    @property
    def childrenPending(self) -> bool:
        return self.__childrenPending
    
    @childrenPending.setter
    def childrenPending(self, value: bool):
        self.__childrenPending = value

    @property
    def included(self) -> bool:
        return self.parentsIncluded

    @property
    def pending(self) -> bool:
        return self.childrenPending

    @property
    def isTemplate(self) -> bool:
        return self.__template
    
    @isTemplate.setter
    def isTemplate(self, value: bool):
        self.__template = value

    def __hash__(self) -> int:
        return hash(self.ID)
    
    def __eq__(self, value: object) -> bool:
        return hash(self) == hash(value)
    
    def __str__(self) -> str:
        return self.ID


class DcrActivity(DcrElement):
    
    def __init__(self, id, parents=None, expression=None, template=None, isTemplate=False):
        super().__init__(id, parents, template, isTemplate)
        self.__included = True if template is None else template.included
        self.__pending = False if template is None else template.pending
        self.__executed = None if template is None else template.executed # set as None or a datetime denoting execution time. Not currently used but for compatability with timed graphs.
        self.__expression = expression if template is None else template.expression
        self.__data = None

    @property
    def included(self) -> bool:
        return self.__included and self.parentsIncluded
    
    @included.setter
    def included(self, value: bool):
        self.__included = value

    @property
    def pending(self) -> bool:
        return self.__pending or self.childrenPending
    
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
    
    def __init__(self, id, parents=None, isTemplate=False):
        super().__init__(id, parents, isTemplate=isTemplate)


class DcrSubProcess(DcrActivity):
    
    def __init__(self, id, parents=None, expression=None, template=None, isTemplate=False):
        super().__init__(id, parents, expression, template, isTemplate)


class DcrRelation:
    
    def __init__(self, type, source, target, guard=None):
        self.__relationType = type
        self.__source = source
        self.__target = target
        self.__guard = guard

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
    
    def __repr__(self):
        return "Relation type: " + str(self.relationType) + ", Source: " + str(self.source) + ", Target: " + str(self.target) + ", Guard: " + str(self.guard)

    def __hash__(self) -> int:
        return hash(repr(self))
    
    def __eq__(self, value: object) -> bool:
        return hash(self) == hash(value)
    

class Spawn(DcrRelation):
    
    def __init__(self, source, target, guard=None):
        super().__init__(RelationType.S, source, target, guard)
        self.__spawned = 0
    
    @property
    def spawned(self) -> int:
        return self.__spawned
    
    @spawned.setter
    def spawned(self, value: int):
        self.__spawned = value


class DcrGraph:
    
    def __init__(self, id, template=None, isTemplate=False):
        self.__id = id
        self.__events = set() if template is None else template.events
        self.__elements = set() if template is None else template.elements
        self.__activityMap = {} if template is None else template.labelMapping
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
    def elements(self) -> Set[DcrElement]:
        return self.__elements

    @elements.setter
    def labels(self, value: Set[DcrElement]):
        self.__elements = value

    @property
    def activity_map(self) -> Dict[str, DcrActivity]:
        return self.__activityMap

    @activity_map.setter
    def activity_map(self, value: Dict[str, DcrActivity]):
        self.__activityMap = value

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
        for event, dcrActivity in self.activity_map.items():
            if activity == dcrActivity:
                return event

    def get_activity(self, event: str) -> DcrActivity:
        return self.activity_map[event]

    def get_constraints(self) -> int:
        return len(self.__relations)


    """
    def __repr__(self):
        string = ""
        for key, value in vars(self).items():
            string += str(key.split("_")[-1]) + ": " + str(value) + "\n"
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