import time

import pm4py
import os
import pandas as pd
from pm4py.discovery import discover_dcr, discover_declare
from pm4py.algo.conformance.dcr.variants.multi import apply as conformance_multi_dcr
from pm4py.objects.log.obj import EventLog, Event, Trace
from tests.DCR_test.benchmark_util.conformance_sepsis import benchmark_conformance_sepsis_declare
from pm4py.conformance import conformance_dcr
from shutil import rmtree
from zipfile import ZipFile
import math
from collections import Counter

import zipfile
import tempfile


import matplotlib.pyplot as plt

def get_files(path, folder):
    extract_path = os.path.join(path,folder)
    with ZipFile(extract_path+".zip", 'r') as zipObj:
        zipObj.extractall(extract_path)

def remove_files(path, folder):
    extract_path = os.path.join(path, folder)
    rmtree(extract_path)

def export_graph(graph, path, name):
    from pm4py.objects.dcr.exporter.exporter import DCR_JS_PORTAL
    print(os.path.join(path))
    pm4py.write_dcr_xml(dcr_graph=graph,path=os.path.join(path,name+".xml"),variant=DCR_JS_PORTAL,dcr_title=name)

def import_graph(path,name):
    from pm4py.objects.dcr.importer.importer import XML_DCR_PORTAL
    graph = pm4py.read_dcr_xml(file_path=os.path.join(path,name+".xml"),variant=XML_DCR_PORTAL)
    return graph


def write_csv(temp, res_file):
    data = pd.DataFrame(temp)
    if os.path.isfile(res_file):
        data.to_csv(res_file, sep=",", mode="a", header=False,
                    index=False)
    else:
        data.to_csv(res_file, sep=";", index=False)

def benchmark_declare():
    pass

def getPercent(eventLog, percent):
    return int(math.ceil(len(eventLog) * percent / 100))


def benchmark_conformance(graph, test_log, res_file, repeat):
    times = []
    res = None
    for i in range(repeat):
        start = time.perf_counter()
        res = conformance_dcr(test_log, graph)
        end = (time.perf_counter() - start) * 1000
        times.append(end)


    no_traces = len(res)
    no_cons = res[0]['no_constr_total']

    no_dev_traces = 0
    for i in res:
        if i['dev_fitness'] != 1:
            no_dev_traces += 1

    dev_ratio = no_dev_traces/no_traces
    temp = {
        "avg_run_time": [(sum(times) / len(times))],
        "no_traces": [no_traces],
        "dev_traces": no_dev_traces,
        "no_cons": no_cons,
        "fitness": "%.2f" % (1-dev_ratio),
        "dev_ration": "%.2f" % (100 * dev_ratio),
        "conf_ratio": "%.2f" % (100 - 100 * dev_ratio)
    }
    write_csv(temp, res_file)

def benchmark_multi_conformance(graph, test_log, res_file, repeat):
    times = []
    res = None
    for i in range(repeat):
        start = time.perf_counter()
        res = conformance_multi_dcr(test_log, graph)
        end = (time.perf_counter() - start) * 1000
        times.append(end)


    no_traces = len(res)
    no_cons = res[0]['no_constr_total']

    no_dev_traces = 0
    for i in res:
        if i['dev_fitness'] != 1:
            no_dev_traces += 1

    dev_ratio = no_dev_traces/no_traces
    temp = {
        "avg_run_time": [(sum(times) / len(times))],
        "no_traces": [no_traces],
        "dev_traces": no_dev_traces,
        "no_cons": no_cons,
        "fitness": "%.2f" % (1-dev_ratio),
        "dev_ration": "%.2f" % (100 * dev_ratio),
        "conf_ratio": "%.2f" % (100 - 100 * dev_ratio)
    }
    write_csv(temp, res_file)

def run_benchmark(path,input_log, res_file, repeat, multi=False):
    print("running" + path)
    log = pm4py.read_xes(os.path.join(path, input_log), return_legacy_log_object=True)
    for i in range(repeat):
        print("running " + str(i+1) +" iteration")
        percentage = 5*(i+1)
        index = getPercent(log,percentage)
        graph_log = EventLog(log[:index])
        graph, _ = pm4py.discover_dcr(graph_log)

        test_log = EventLog(log[index:])
        if not multi:
            benchmark_conformance(graph, test_log, res_file, repeat)
        else:
            benchmark_multi_conformance(graph,test_log,("multi_" + res_file),repeat)


def run_dummy(path, input_log, multi=False):
    log = pm4py.read_xes(os.path.join(path, input_log), return_legacy_log_object=True)
    index = getPercent(log, 10)
    graph_log = EventLog(log[:index])
    graph, _ = pm4py.discover_dcr(graph_log)
    test_log = EventLog(log[index:])
    if not multi:
        res = conformance_dcr(test_log, graph)
    else:
        res = conformance_multi_dcr(test_log, graph)
def open_pdc_zip_files():
    pass

if __name__ == "__main__":
    multi = False
    run_dummy("sepsis","Sepsis Cases - Event Log.xes.gz", multi=multi)
    run_benchmark("sepsis","Sepsis Cases - Event Log.xes.gz", "sepsis_results.csv",10, multi=multi)
    run_benchmark("traffic_fines", "Road_Traffic_fine_management_Process.xes.gz", "traffic_results.csv", 10, multi=multi)
    run_benchmark("dreyers_fond", "Dreyers Foundation.xes", "dreyers_fond_results.csv", 10, multi=multi)
    #sepsis("new test")
    #sepsis_declare()
    #traffic_management()

