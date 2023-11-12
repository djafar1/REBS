import pm4py
import os
import pandas as pd
import time
from pm4py.discovery import discover_dcr, discover_declare
from pm4py.conformance import conformance_dcr, conformance_declare
from pm4py.algo.conformance.dcr.variants.classic import apply
import random
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


def benchmark_conformance_run_time_pdc(test_path, training_logs, gt_truth_log):
    training_log_path = os.path.join(test_path, training_logs)

    box_times = {}
    box_deviations = {}
    box_fitness = {}

    # import training log and mine dcr
    # limit to a few files such that it is not overwhelming to look at
    i = 0

    for file in os.listdir(training_log_path):
        training_log = pm4py.read_xes(os.path.join(training_log_path, file))
        # pm4py needs a timestamp, so a assign random values
        add = pd.date_range('2018-04-09', periods=len(training_log), freq='20min')
        training_log['time:timestamp'] = add
        # we use ten logs, as it can go one forever and produce a lot of data
        #discover model
        graph ,_ = discover_dcr(training_log)
        #collect for box plots
        size = graph.get_constraints()


        if i < 15:
            box_times[size] = []
            box_deviations[size] = []
            box_fitness[size] = []

        #create list to collect data
        #file path to test logs
        gt_path = os.path.join(test_path, gt_truth_log)
        #iterate through all test in folder
        for gt_file in os.listdir(gt_path):
            #import training log
            test_log = pm4py.read_xes(os.path.join(gt_path, gt_file))
            add = pd.date_range('2018-04-09', periods=len(test_log), freq='20min')
            test_log['time:timestamp'] = add

            start = time.perf_counter()
            res = apply(test_log,graph)
            end = (time.perf_counter() - start)*1000
            box_times[size].append(end)
            collect = set()
            for j in res:
                if j['deviations'] != []:
                    collect = collect.union({tuple(x) for x in j['deviations']})
            box_fitness[size].append((1 - len(collect)/graph.get_constraints()))
            box_deviations[size].append(len(collect))
        i += 1

    # Plot the dataframe
    #sort values
    box_times = dict(sorted(box_times.items()))
    box_deviations = dict(sorted(box_deviations.items()))
    box_fitness = dict(sorted(box_fitness.items()))

    generate_box_plot(box_times,box_deviations,box_fitness)


def benchmark_conformance_run_time_sepsis(test_path):
    times = []
    deviations = []
    fitness = []
    test_log_size = []
    training_log = pm4py.read_xes(os.path.join(test_path,'Sepsis Cases - Event Log.xes'))

    #discover model
    graph , _ = discover_dcr(training_log)

    for file in os.listdir(test_path):
        print(file)
        test_log = pm4py.read_xes(os.path.join(test_path, file))
        if file != 'Sepsis Cases - Event Log.xes':
            os.remove(os.path.join(test_path,file))
        start = time.perf_counter()
        res = apply(test_log,graph)
        end = (time.perf_counter() - start) * 1000
        times.append(end)

        collect = []
        for j in res:
            if j['deviations'] != []:
                collect = collect + [tuple(x) for x in j['deviations']]
        test_log_size.append(len(test_log))
        deviations.append(len(collect))

        #
        temp = pm4py.convert_to_event_log(test_log)
        avg_trace_len = 0
        for i in temp:
            avg_trace_len += len(i)
        avg_trace_len = str(avg_trace_len/len(temp)).replace(".",",")

        temp={"file": str(file),"total_deviations": [len(collect)], "time": [str(end).replace(".",",")], "avg_trace": [avg_trace_len], "log_size": [len(test_log)]}
        print(temp)
        write_csv(temp, "sepsis")

    # Plot the dataframe
    print(test_log_size)
    xs, ys = zip(*sorted(zip(test_log_size, times)))

    plt.title("times vs deviation deviations")
    plt.plot(xs,ys,'bo')
    plt.show()

def write_csv(temp, test_path):
    data = pd.DataFrame(temp)
    if os.path.isfile("results/" + str(test_path) + " sepsis dcr run time.csv"):
        data.to_csv("results/" + str(test_path) + " sepsis dcr run time.csv", sep=";", mode="a", header=False,
                    index=False)
    else:
        data.to_csv("results/" + str(test_path) + " sepsis dcr run time.csv", sep=";", index=False)


def generate_box_plot(box_times,box_deviations,box_fitness):
    size, times = box_times.keys(), box_times.values()

    plt.boxplot(times)
    plt.title("different times in ms given by graph size")
    plt.xticks(range(1, len(size) + 1), size)
    plt.show()


    size, deviations = box_deviations.keys(), box_deviations.values()

    plt.boxplot(deviations)
    plt.title("number of deviation for the given graphs")
    plt.xticks(range(1, len(size) + 1), size)
    plt.show()

    size, fitness = box_fitness.keys(), box_fitness.values()

    print(fitness)
    print(range(1, len(size) + 1))
    print(len(fitness))
    plt.boxplot(fitness)
    plt.title("fitness given by the different size")
    plt.xticks(range(1, len(size) + 1), size)
    plt.show()



def initiate_conformance_test(test_path: str):
    training_logs = "Training Logs"
    ground_truth_log = "Ground Truth Logs"
    ground_truth_log = "Ground Truth Logs"

    get_files(test_path, training_logs)
    get_files(test_path, ground_truth_log)

    benchmark_conformance_run_time_pdc(test_path, training_logs, ground_truth_log)

    remove_files(test_path, training_logs)
    remove_files(test_path, ground_truth_log)

def generate_sepsis_log_using_petri_net(no_traces, configuration):
    # petri met to produce synthetic log for
    from pm4py.algo.simulation.playout.petri_net.variants.basic_playout import apply_playout
    log = pm4py.read_xes(os.path.join("sepsis","Sepsis Cases - Event Log.xes"))
    net, im, fm = pm4py.discover_petri_net_alpha(log)
    for i in range(len(configuration)):
        log = apply_playout(net, im, no_traces, configuration[i])
        path = os.path.join("sepsis","sepsis max trace len "+str(i)+".xes")
        pm4py.write_xes(log,path)


if __name__ == "__main__":
    enabled_testing = ["sepsis"]
    #generate log

    if "pdc_2022" in enabled_testing:
        print("running pdc")
        #the test to run
        pdc_test = "pdc_2022"
        initiate_conformance_test(pdc_test)


    if "sepsis" in enabled_testing:
        print("running sepsis with synthetic logs")

        configuration_trace_len = [5,10,15,20,25,30]
        max_trace = 1050
        generate_sepsis_log_using_petri_net(max_trace, configuration_trace_len)
        benchmark_conformance_run_time_sepsis("sepsis")