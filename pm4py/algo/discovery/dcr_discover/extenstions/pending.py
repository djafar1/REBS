import pm4py
import pandas as pd

from copy import deepcopy
from pm4py.objects.dcr.semantics import DcrSemantics


def apply(log, dcr_model, ignore_lifecycle=True):
    if isinstance(log, pd.DataFrame):
        log = pm4py.convert_to_event_log(log)

    at_least_once_all_traces = set(dcr_model['events'])
    end_excluded_all_traces = set(dcr_model['events'])

    for trace in log:
        executed_events = set()
        im = deepcopy(dcr_model['marking'])
        dcr = deepcopy(dcr_model)
        complete = True
        semantics_obj = DcrSemantics()
        for event in trace:
            dcr = semantics_obj.execute(dcr, event['concept:name'])
            if event['concept:name'] in dcr.marking.executed:
                executed_events.add(event['concept:name'])
            if not ignore_lifecycle:
                complete = complete and event['lifecycle:transition'] == 'complete'
        if complete:
            fm = deepcopy(dcr['marking'])
            excluded_events = im['included'].difference(fm['included'])
            at_least_once_all_traces = at_least_once_all_traces.intersection(executed_events)
            end_excluded_all_traces = end_excluded_all_traces.intersection(excluded_events)

    initially_pending = at_least_once_all_traces.union(end_excluded_all_traces)
    dcr_model['marking']['pending'] = initially_pending
    return dcr_model
