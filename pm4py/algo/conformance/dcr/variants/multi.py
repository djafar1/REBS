import pandas as pd
import numpy as np
from enum import Enum

import pm4py
from pm4py.util import exec_utils, constants, xes_constants
from typing import Optional, Dict, Any, Union, List, Tuple
from pm4py.objects.log.obj import EventLog
from pm4py.objects.dcr.semantics import DCRSemantics
from pm4py.objects.dcr.obj import DcrGraph
from pm4py.objects.dcr.roles.obj import RoledcrGraph
from pm4py.algo.conformance.dcr.variants.classic import RuleBasedConformance
from pm4py.analysis import cluster_log
from pm4py.objects.log.obj import EventLog
from pm4py.algo.conformance.dcr.decorators.decorator import ConcreteChecker
from pm4py.algo.conformance.dcr.decorators.roledecorator import RoleDecorator
from threading import Thread
import threading
from copy import deepcopy, copy
import time
import math


class Parameters(Enum):
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY


class Outputs(Enum):
    FITNESS = "dev_fitness"
    DEVIATIONS = "deviations"
    NO_DEV_TOTAL = "no_dev_total"
    NO_CONSTR_TOTAL = 'no_constr_total'
    IS_FIT = "is_fit"



def apply_multi_conformance(con):
    ret = con.apply_conformance()
    conf_case.extend(ret)


def transform_eventlog(input_log: Union[EventLog, pd.DataFrame], case_id_key: str, tCount: int):
    if isinstance(input_log, pd.DataFrame):
        list_events = []
        columns_names = list(input_log.columns)
        columns_corr = []
        log = []
        last_case_key = input_log.iloc[0][case_id_key]
        for c in columns_names:
            columns_corr.append(input_log[c].to_numpy())
        length = columns_corr[-1].size
        for i in range(length):
            event = {}
            for j in range(len(columns_names)):
                event[columns_names[j]] = columns_corr[j][i]
            if last_case_key != event[case_id_key]:
                log.append(list_events)
                list_events = []
            last_case_key = event[case_id_key]
            list_events.append(event)
        log.append(list_events)
        input_log = log

    log = []
    logs = []
    length = len(input_log)
    split = int(math.ceil(length / tCount))
    k = 0
    for i in range(length):
        log.append(input_log[i])
        if k >= split:
            k = -1
            logs.append(log)
            log = []
        else:
            k += 1
    if k > 0:
        logs.append(log)

    return logs


def apply(log: Union[pd.DataFrame, EventLog], graph: Union[DcrGraph, RoledcrGraph],
          parameters: Optional[Dict[Any, Any]] = None):

    global conf_case
    conf_case = []
    if parameters is None:
        parameters = {}

    logs = transform_eventlog(log, exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters,
                                                              constants.CASE_CONCEPT_NAME), 10)

    threads = []


    for clust_log in logs:
        con = RuleBasedConformance(clust_log, deepcopy(graph), parameters)
        threads.append(threading.Thread(target=apply_multi_conformance,
                                        args=(con,)))
        threads[-1].start()

    for thread in threads:
        thread.join()

    return conf_case
