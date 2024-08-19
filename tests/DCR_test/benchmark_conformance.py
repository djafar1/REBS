import time

import pm4py
import os
import pandas as pd
from pm4py.objects.log.util.split_train_test import split
from pm4py.conformance import conformance_dcr
from shutil import rmtree
from zipfile import ZipFile
import math

from Declare4Py.ProcessModels.DeclareModel import DeclareModel
from Declare4Py.ProcessMiningTasks.Discovery.DeclareMiner import DeclareMiner
from Declare4Py.D4PyEventLog import D4PyEventLog
from Declare4Py.ProcessMiningTasks.ConformanceChecking.MPDeclareAnalyzer import MPDeclareAnalyzer
from Declare4Py.ProcessMiningTasks.ConformanceChecking.MPDeclareResultsBrowser import MPDeclareResultsBrowser


def get_files(path, folder):
    extract_path = os.path.join(path, folder)
    with ZipFile(extract_path + ".zip", 'r') as zipObj:
        zipObj.extractall(extract_path)


def remove_files(path, folder):
    extract_path = os.path.join(path, folder)
    rmtree(extract_path)


def export_graph(graph, path, name):
    from pm4py.objects.dcr.exporter.exporter import DCR_JS_PORTAL
    print(os.path.join(path))
    pm4py.write_dcr_xml(dcr_graph=graph, path=os.path.join(path, name + ".xml"), variant=DCR_JS_PORTAL, dcr_title=name)


def import_graph(path, name):
    from pm4py.objects.dcr.importer.importer import XML_DCR_PORTAL
    graph = pm4py.read_dcr_xml(file_path=os.path.join(path, name + ".xml"), variant=XML_DCR_PORTAL)
    return graph


def write_csv(temp, res_file):
    data = pd.DataFrame(temp)
    if os.path.isfile(res_file):
        data.to_csv(res_file, sep=",", mode="a", header=False,
                    index=False)
    else:
        data.to_csv(res_file, sep=";", index=False)


def benchmark_conformance(graph, test_log, res_file, repeat):
    times = []

    # dummy
    conformance_dcr(test_log, graph)
    res = None
    # actual
    print("running conformance:")
    for i in range(repeat):
        print("running round: " + str(i))
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

    dev_ratio = no_dev_traces / no_traces
    temp = {
        "avg_run_time": [(sum(times) / len(times))],
        "no_traces": [no_traces],
        "dev_traces": no_dev_traces,
        "no_cons": no_cons,
        "fitness": "%.2f" % (1 - dev_ratio),
        "dev_ration": "%.2f" % (100 * dev_ratio),
        "conf_ratio": "%.2f" % (100 - 100 * dev_ratio)
    }
    write_csv(temp, "results/" + res_file)


def benchmark_declare_conformance(declare_model, test_log, res_file, repeat):
    times = []
    basic_checker = MPDeclareAnalyzer(log=test_log, declare_model=declare_model, consider_vacuity=False)
    # dummy
    conf_check_res: MPDeclareResultsBrowser = basic_checker.run()

    # actual
    print("running conformance:")
    for i in range(repeat):
        print("running round: " + str(i))
        start = time.perf_counter()
        conf_check_res: MPDeclareResultsBrowser = basic_checker.run()
        end = (time.perf_counter() - start) * 1000
        times.append(end)

    no_traces = test_log.get_length()

    no_cons = len(declare_model.constraints)

    no_dev_traces = 0
    for i in range(no_traces):
        for j in conf_check_res.get_metric(trace_id=i, metric="num_violations"):
            if j != None and j>0:
                no_dev_traces += 1
                break

    dev_ratio = no_dev_traces / no_traces
    temp = {
        "avg_run_time": [(sum(times) / len(times))],
        "no_traces": [no_traces],
        "dev_traces": no_dev_traces,
        "no_cons": no_cons,
        "fitness": "%.2f" % (1 - dev_ratio),
        "dev_ration": "%.2f" % (100 * dev_ratio),
        "conf_ratio": "%.2f" % (100 - 100 * dev_ratio)
    }
    print(temp)
    write_csv(temp, "results/" + res_file)


def run_benchmark(path, input_log, res_file, repeat):
    print("running" + path)
    log = pm4py.read_xes(os.path.join(path, input_log), return_legacy_log_object=True)
    for i in range(repeat):
        print("running " + str(i + 1) + " iteration")
        percentage = 5 * (i + 1)
        graph_log, test_log = split(log, percentage / 100)
        graph, _ = pm4py.discover_dcr(graph_log)

        benchmark_conformance(graph, test_log, res_file, repeat)


def run_declare_benchmark(path, input_log, res_file, repeat):
    print("running " + path)
    log = pm4py.read_xes(os.path.join(path, input_log), return_legacy_log_object=True)
    for i in range(repeat):
        print("running " + str(i + 1) + " iteration")

        percentage = 5 * (i + 1)
        graph_log, test_log = split(log, percentage / 100)
        graph_log = D4PyEventLog(case_name="case:concept:name", log=graph_log)
        discovery = DeclareMiner(log=graph_log, consider_vacuity=False, min_support=0.9, itemsets_support=0.9)
        declare_model: DeclareModel = discovery.run()
        test_log = D4PyEventLog(case_name="case:concept:name", log=test_log)
        benchmark_declare_conformance(declare_model, test_log, res_file, repeat)


if __name__ == "__main__":
    run_benchmark("sepsis", "Sepsis Cases - Event Log.xes.gz", "sepsis_results.csv", 10)
    run_benchmark("traffic_fines", "Road_Traffic_fine_management_Process.xes.gz", "traffic_results.csv", 10)
    run_benchmark("dreyers_fond", "Dreyers Foundation.xes", "dreyers_fond_results.csv", 10)
    run_declare_benchmark("sepsis", "Sepsis Cases - Event Log.xes.gz", "declare_sepsis_results.csv", 10)
    run_declare_benchmark("traffic_fines", "Road_Traffic_fine_management_Process.xes.gz", "declare_traffic_results.csv", 10)
    run_declare_benchmark("dreyers_fond", "Dreyers Foundation.xes", "declare_dreyers_fond_results.csv", 10)
