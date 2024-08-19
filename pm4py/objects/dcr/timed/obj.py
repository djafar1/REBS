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

    def __init__(self, template=None):
        super().__init__(template)
        self.__marking = TimedMarking(set(), set(), set()) if template is None else (
            TimedMarking(template['marking']['executed'], template['marking']['included'], template['marking']['pending'],
                         template['marking']['executedTime'], template['marking']['pendingDeadline']))
        self.__timed_conditions = {} if template is None else template['conditionsForDelays']
        self.__timed_responses = {} if template is None else template['responseToDeadlines']

    @property
    def timed_conditions(self) -> Dict[str, Dict[str, timedelta]]:
        return self.__timed_conditions

    @property
    def timed_responses(self) -> Dict[str, Dict[str, timedelta]]:
        return self.__timed_responses
