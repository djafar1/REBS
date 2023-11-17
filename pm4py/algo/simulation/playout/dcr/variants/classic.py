'''
    This file is part of PM4Py (More Info: https://pm4py.fit.fraunhofer.de).

    PM4Py is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    PM4Py is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PM4Py.  If not, see <https://www.gnu.org/licenses/>.
'''
import datetime
import heapq
import math
import sys
import time
import random
from collections import Counter
from copy import deepcopy
from enum import Enum
from typing import Optional, Dict, Any, Union, Tuple

from pm4py.objects.log.obj import EventLog
from pm4py.objects.log.obj import Trace, Event
from pm4py.util import exec_utils, constants, xes_constants

from pm4py.objects.dcr.semantics import DCRSemantics


class Parameters(Enum):
    MAX_TRACE_LENGTH = "max_trace_length"
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    MAX_EXECUTION_TIME = "max_execution_time"
    NO_TRACES = "noTraces"
    INITIAL_CASE_ID = "initial_case_id"


def choose_next_activity(dcr, parameters=None):
    enabled = DCRSemantics().enabled(dcr)
    if tuple(enabled) == ():
        return dcr, None
    next_activity = random.choice(tuple(enabled))
    dcr = DCRSemantics().execute(dcr, next_activity)
    return dcr, next_activity


def generate_random_trace(dcr, min_trace_length, max_trace_length, start_time, max_execution_time, parameters=None):
    final_trace = []
    while True:
        if DCRSemantics.is_accepting(dcr):
            if len(final_trace) >= min_trace_length:
                break
        if len(final_trace) >= max_trace_length:
            break
        curr_time = time.time()
        if curr_time - start_time > max_execution_time:
            break
        dcr, next_activity = choose_next_activity(dcr, parameters)
        if next_activity is None:
            break
        final_trace.append(next_activity)
    return final_trace


def apply(dcr, parameters: Optional[Dict[Union[str, Parameters], Any]] = None) -> Union[
        EventLog, Dict[Tuple[str, str], int]]:
    """
    Applies the playout algorithm on a DFG, extracting the most likely traces according to the DFG

    Parameters
    ---------------
    dfg
        *Complete* DFG
    start_activities
        Start activities
    end_activities
        End activities
    parameters
        Parameters of the algorithm, including:
        - Parameters.ACTIVITY_KEY => the activity key of the simulated log
        - Parameters.TIMESTAMP_KEY => the timestamp key of the simulated log
        - Parameters.MAX_TRACE_LENGTH => maximum trace length (default: 1000)
        - Parameters.MIN_WEIGHTED_PROBABILITY => the minimum overall weighted probability that makes the method stop
                                                (default: 1)
        - Parameters.MAX_NO_OCC_PER_ACTIVITY => the maximum number of occurrences per activity in the traces of the log
                                                (default: 2)
        - Parameters.ADD_TRACE_IF_TAKES_NEW_ELS_TO_DFG => adds a simulated trace to the simulated log only if it adds
                                                    elements to the simulated DFG, e.g., it adds behavior;
                                                    skip insertion otherwise (default: False)
        - Parameters.RETURN_VARIANTS => returns the traces as variants with a likely number of occurrences

    Returns
    ---------------
    simulated_log
        Simulated log
    """
    if parameters is None:
        parameters = {}
    
    initial_case_id = exec_utils.get_param_value(Parameters.INITIAL_CASE_ID, parameters, 1)
    timestamp_key = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters,
                                               xes_constants.DEFAULT_TIMESTAMP_KEY)
    activity_key = exec_utils.get_param_value(
        Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)
    max_trace_length = exec_utils.get_param_value(
        Parameters.MAX_TRACE_LENGTH, parameters, 50)
    max_execution_time = exec_utils.get_param_value(
        Parameters.MAX_EXECUTION_TIME, parameters, sys.maxsize)
    no_traces = exec_utils.get_param_value(Parameters.NO_TRACES, parameters, 10)
    
    original_dcr = deepcopy(dcr)
    final_traces = []

    start_time = time.time()
    while len(final_traces) < no_traces:
        min_trace_length = random.randrange(max_trace_length)
        trace = generate_random_trace(dcr, min_trace_length, max_trace_length, start_time, max_execution_time, parameters)
        final_traces.append(trace)
        dcr = deepcopy(original_dcr)
    
    event_log = EventLog()
    # assigns to each event an increased timestamp from 1970
    curr_timestamp = 10000000
    for index, trace in enumerate(final_traces):
        log_trace = Trace(
            attributes={xes_constants.DEFAULT_TRACEID_KEY: str(index+initial_case_id)})
        for activity in trace:
            log_trace.append(
                Event({activity_key: activity, timestamp_key: datetime.datetime.fromtimestamp(curr_timestamp)})
            )
            # increases by 1 second
            curr_timestamp += 1
        event_log.append(log_trace)
    return event_log

