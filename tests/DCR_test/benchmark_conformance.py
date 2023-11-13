import pm4py
import os
import pandas as pd
from pm4py.discovery import discover_dcr, discover_declare
from pm4py.objects.log.obj import EventLog, Event, Trace
from tests.DCR_test.benchmark_util.conformance_sepsis import benchmark_conformance_sepsis, benchmark_conformance_sepsis_declare
from tests.DCR_test.benchmark_util.conformance_ground_truth import conformance_ground_truth
from shutil import rmtree
from zipfile import ZipFile


import matplotlib.pyplot as plt

def get_files(path, folder):
    extract_path = os.path.join(path,folder)
    with ZipFile(extract_path+".zip", 'r') as zipObj:
        zipObj.extractall(extract_path)

def remove_files(path, folder):
    extract_path = os.path.join(path, folder)
    rmtree(extract_path)


def generate_log_using_petri_net(path, log, log_configuration, trace_configuration):
    # petri met to produce synthetic log for
    from pm4py.algo.simulation.playout.petri_net.variants.basic_playout import apply_playout
    print(os.path.join(path,log))
    log = pm4py.read_xes(os.path.join(path,log))
    net, im, fm = pm4py.discover_petri_net_alpha(log)
    for i in log_configuration:
        for j in trace_configuration:
            log = apply_playout(net, im, i, j)
            path = os.path.join(path,path+"_"+str(i)+"_"+str(j)+".xes")
            pm4py.write_xes(log,path)

if __name__ == "__main__":
    enabled_testing = ["loan application"]

    if "loan application" in enabled_testing:
        configuration_trace_len = [10]
        max_trace = [20]
        path = "loan_application"
        import_log = "BPI_Challenge_2012.xes.gz"
        log = pm4py.read_xes(os.path.join(path,import_log))
        ex = pm4py.convert_to_event_log(log)
        graph, _ = pm4py.discover_dcr(log)
        generate_log_using_petri_net(path, log, max_trace, configuration_trace_len)
        log = pm4py.read_xes(os.path.join(path,path+"_"+str(max_trace[0])+"_"+str(configuration_trace_len[0])+".xes"))
        res = pm4py.conformance_dcr(graph, )
        print(graph)

        #conformance_ground_truth(graph,gt_log)

    if "sepsis" in enabled_testing:
        print("running sepsis with synthetic logs")
        #to generate synthetic sepsis logs
        configuration_trace_len = [10,20,30,40,50]
        max_trace = [25000,50000,75000,100000]
        path = "sepsis"
        import_log = "Sepsis Cases - Event Log.xes"
        generate_log_using_petri_net(path, import_log, max_trace, configuration_trace_len)

        #specify test files
        res_file = "results/sepsis_run_times.csv"
        training_log_path = "Sepsis Cases - Event Log.xes"
        training_log = pm4py.read_xes(os.path.join("sepsis",training_log_path))
        graph, _ = discover_dcr(training_log)
        for test_file in os.listdir("sepsis"):
            if test_file == training_log_path:
                continue
            test_log = pm4py.read_xes(os.path.join("sepsis",test_file), return_legacy_log_object=True)
            benchmark_conformance_sepsis(graph, test_log, res_file, 10)


    if "declare" in enabled_testing:
        print("running sepsis with synthetic logs for declare")

        #specify test files
        res_file = "results/sepsis_run_times_declare.csv"
        training_log_path = "Sepsis Cases - Event Log.xes"
        training_log = pm4py.read_xes(os.path.join("sepsis",training_log_path))
        model = discover_declare(training_log)
        no = 0
        for test_file in os.listdir("sepsis"):
            if test_file == training_log_path:
                continue
            test_log = pm4py.read_xes(os.path.join("sepsis",test_file), return_legacy_log_object=True)
            benchmark_conformance_sepsis_declare(model, test_log, res_file, 10)
