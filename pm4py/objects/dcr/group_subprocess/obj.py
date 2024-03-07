from pm4py.objects.dcr.milestone_noresponse.obj import MilestoneNoResponseDcrGraph
from typing import Set, Dict


class GroupSubprocessDcrGraph(MilestoneNoResponseDcrGraph):

    def __init__(self, template=None):
        super().__init__(template)
        self.__nestedgroups = {} if template is None else template['nestings']
        self.__subprocesses = {} if template is None else template['subprocesses']
        self.__nestedgroupsmap = {}
        if len(self.__nestedgroupsmap) == 0 and len(self.__nestedgroups) > 0:
            for group, events in self.__nestedgroups.items():
                for e in events:
                    self.__nestedgroupsmap[e] = group

    def obj_to_template(self):
        res = super().obj_to_template()
        res['nestings'] = self.__nestedgroups
        res['subprocesses'] = self.__subprocesses
        res['nestingsMap'] = self.__nestedgroupsmap
        return res

    @property
    def nestedgroups(self) -> Dict[str, Set[str]]:
        return self.__nestedgroups

    @nestedgroups.setter
    def nestedgroups(self, ng):
        self.__nestedgroups = ng

    @property
    def nestedgroupsmap(self) -> Dict[str, str]:
        return self.__nestedgroupsmap

    @nestedgroupsmap.setter
    def nestedgroupsmap(self, ngm):
        self.__nestedgroupsmap = ngm

    @property
    def subprocesses(self) -> Dict[str, Set[str]]:
        return self.__subprocesses

    @subprocesses.setter
    def subprocesses(self, sps):
        self.__subprocesses = sps