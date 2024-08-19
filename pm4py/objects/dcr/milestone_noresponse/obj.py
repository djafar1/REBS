"""
This module extends the RoleDcrGraph class to include support for milestone and
no-response relations within Dynamic Condition Response (DCR) Graphs.

The module adds functionality to handle milestone and no-response constraints,
allowing for more expressive process models with additional types of relations
between events.

Classes:
    MilestoneNoResponseDcrGraph: Extends RoleDcrGraph to include milestone and no-response relations.

This class provides methods to manage and manipulate milestone and no-response
relations within a DCR Graph, enhancing the model's ability to represent complex
process behaviors and dependencies.
"""
from typing import Dict, Set

from pm4py.objects.dcr.roles.obj import RoleDcrGraph


class MilestoneNoResponseDcrGraph(RoleDcrGraph):
    """
    This class extends the RoleDcrGraph to include milestone and no-response
    relations, allowing for more expressive DCR Graphs with additional constraints.

    Attributes
    ----------
    self.__milestonesFor: Dict[str, Set[str]]
        A dictionary mapping events to sets of their milestone events.
    self.__noResponseTo: Dict[str, Set[str]]
        A dictionary mapping events to sets of their no-response events.

    Methods
    -------
    obj_to_template(self) -> dict:
        Converts the object to a template dictionary, including milestone and no-response relations.
    get_constraints(self) -> int:
        Computes the total number of constraints in the DCR Graph, including milestone and no-response relations.
    """
    def __init__(self, template=None):
        super().__init__(template)
        self.__milestonesFor = {} if template is None else template['milestonesFor']
        self.__noResponseTo = {} if template is None else template['noResponseTo']

    def obj_to_template(self):
        res = super().obj_to_template()
        res['milestonesFor'] = self.__milestonesFor
        res['noResponseTo'] = self.__noResponseTo
        return res

    @property
    def milestones(self) -> Dict[str, Set[str]]:
        return self.__milestonesFor

    @property
    def noresponses(self) -> Dict[str, Set[str]]:
        return self.__noResponseTo

    def get_constraints(self) -> int:
        no = super().get_constraints()
        for i in self.__milestonesFor.values():
            no += len(i)
        for i in self.__noResponseTo.values():
            no += len(i)
        return no

    def __eq__(self, other):
        return super().__eq__(other) and self.milestones == other.milestones and self.noresponses == other.noresponses

