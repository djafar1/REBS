from pm4py.objects.dcr.milestone_noresponse.obj import MilestoneNoResponseDcrGraph
from typing import Set, Dict


class GroupSubprocessDcrGraph(MilestoneNoResponseDcrGraph):

    def __init__(self, template=None):
        super().__init__(template)
        self.__nested_groups = {} if template is None else template['nestings']
        self.__subprocesses = {} if template is None else template['subprocesses']
        self.__nested_groups_map = {} if template is None else template['nestingsMap']
        if len(self.__nested_groups_map) == 0 and len(self.__nested_groups) > 0:
            for group, events in self.__nested_groups.items():
                for e in events:
                    self.__nested_groups_map[e] = group

    @property
    def nested_groups(self) -> Dict[str, Set[str]]:
        return self.__nested_groups

    @nested_groups.setter
    def nested_groups(self, ng):
        self.__nested_groups = ng

    @property
    def nested_groups_map(self) -> Dict[str, str]:
        return self.__nested_groups_map

    @nested_groups_map.setter
    def nested_groups_map(self, ngm):
        self.__nested_groups_map = ngm

    @property
    def subprocesses(self) -> Dict[str, Set[str]]:
        return self.__subprocesses

    @subprocesses.setter
    def subprocesses(self, sps):
        self.__subprocesses = sps