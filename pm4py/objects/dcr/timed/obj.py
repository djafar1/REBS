from datetime import timedelta

from pm4py.objects.dcr.obj import Marking
from pm4py.objects.dcr.group_subprocess.obj import GroupSubprocessDcrGraph

from typing import Dict


class TimedMarking(Marking):

    def __init__(self, executed, included, pending, executed_time=None, pending_deadline=None) -> None:
        super().__init__(executed, included, pending)
        self.__executed_time = {} if executed_time is None else executed_time
        self.__pending_deadline = {} if pending_deadline is None else pending_deadline

    @property
    def executed_time(self):
        return self.__executed_time

    @property
    def pending_deadline(self):
        return self.__pending_deadline


class TimedDcrGraph(GroupSubprocessDcrGraph):

    def __init__(self, template=None, timing_dict=None):
        super().__init__(template)
        self.__marking = TimedMarking(set(), set(), set()) if template is None else (
            TimedMarking(template['marking']['executed'], template['marking']['included'], template['marking']['pending'],
                         template['marking']['executedTime'], template['marking']['pendingDeadline']))
        self.__timedconditions = {} if template is None else template['conditionsForDelays']
        self.__timedresponses = {} if template is None else template['responseToDeadlines']
        if timing_dict is not None:
            self.timed_dict_to_graph(timing_dict)

    def timed_dict_to_graph(self, timing_dict):
        for timing, value in timing_dict.items():
            if timing[0] == 'CONDITION':
                e1 = timing[2]
                e2 = timing[1]
                if e1 not in self.__timedconditions:
                    self.__timedconditions[e1] = {}
                self.__timedconditions[e1][e2] = value
            elif timing[0] == 'RESPONSE':
                e1 = timing[1]
                e2 = timing[2]
                if e1 not in self.__timedresponses:
                    self.__timedresponses[e1] = {}
                self.__timedresponses[e1][e2] = value

    def obj_to_template(self):
        res = super().obj_to_template()
        res['conditionsForDelays'] = self.__timedconditions
        res['responseToDeadlines'] = self.__timedresponses
        return res

    @property
    def timedconditions(self) -> Dict[str, Dict[str, timedelta]]:
        return self.__timedconditions

    @timedconditions.setter
    def timedconditions(self, value: Dict[str, Dict[str, timedelta]]):
        self.__timedconditions = value

    @property
    def timedresponses(self) -> Dict[str, Dict[str, timedelta]]:
        return self.__timedresponses

    @timedresponses.setter
    def timedresponses(self, value: Dict[str, Dict[str, timedelta]]):
        self.__timedresponses = value
