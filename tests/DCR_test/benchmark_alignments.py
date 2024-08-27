import os
import time
import pandas as pd
import matplotlib.pyplot as plt
from pm4py.objects.log.util.split_train_test import split
import pm4py
from pm4py.algo.conformance.alignments.dcr.variants import optimal
from pm4py.algo.discovery.dfg.variants import performance as dfg_performance
from pm4py.algo.conformance.alignments.dfg.variants import classic as dfg_alignment
from pm4py.objects.conversion.log import converter as log_converter
from collections import Counter


def read_log(path, input_log):
    log = pm4py.read_xes(os.path.join(path, input_log))
    # Convert DataFrame to EventLog if necessary
    if isinstance(log, pd.DataFrame):
        log = log_converter.apply(log)
    return log


def write_csv(temp, res_file):
    data = pd.DataFrame(temp)
    if os.path.isfile(res_file):
        data.to_csv(res_file, sep=",", mode="a", header=False, index=False)
    else:
        data.to_csv(res_file, sep=";", index=False)


def benchmark_optimal_alignment(graph, test_log, repeat):
    times = []

    # Warm-up run
    optimal.apply(test_log, graph)

    for _ in range(repeat):
        start_time = time.perf_counter()
        optimal.apply(test_log, graph)
        end_time = (time.perf_counter() - start_time) * 1000
        times.append(end_time)

    return sum(times) / len(times)


def benchmark_dfg_alignment(dfg, test_log, start_activities, end_activities, repeat):
    times = []

    # Warm-up run
    dfg_alignment.apply(test_log, dfg, start_activities, end_activities)

    for _ in range(repeat):
        start_time = time.perf_counter()
        dfg_alignment.apply(test_log, dfg, start_activities, end_activities)
        end_time = (time.perf_counter() - start_time) * 1000
        times.append(end_time)

    return sum(times) / len(times)


def run_benchmark(path, input_log, res_file, repeat):
    log = read_log(path, input_log)
    results = []

    for i in range(1, 11):
        percentage = 5 * i
        graph_log, test_log = split(log, percentage / 100)

        # For optimal alignment
        graph, _ = pm4py.discover_dcr(graph_log)

        # For DFG alignment
        params = {}
        dfg = dfg_performance.apply(graph_log, parameters=params)

        start_activities = Counter(trace[0]['concept:name'] for trace in graph_log)
        end_activities = Counter(trace[-1]['concept:name'] for trace in graph_log)
        start_activities = dict(start_activities)
        end_activities = dict(end_activities)

        optimal_time = benchmark_optimal_alignment(graph, test_log, repeat)
        dfg_time = benchmark_dfg_alignment(dfg, test_log, start_activities, end_activities, repeat)

        results.append({
            "percentage": percentage,
            "optimal_time": optimal_time,
            "dfg_time": dfg_time
        })

        print(f"Completed {percentage}% for {path}")

    write_csv(results, f"results/{res_file}")
    return results


def plot_results(all_results):
    plt.figure(figsize=(12, 8))

    for dataset, results in all_results.items():
        percentages = [r['percentage'] for r in results]
        optimal_times = [r['optimal_time'] for r in results]
        dfg_times = [r['dfg_time'] for r in results]

        plt.plot(percentages, optimal_times, marker='o', label=f'{dataset} - Optimal')
        plt.plot(percentages, dfg_times, marker='s', label=f'{dataset} - DFG')

    plt.xlabel('Percentage of Log Used for Training')
    plt.ylabel('Average Runtime (ms)')
    plt.title('Benchmark: Optimal Alignment vs DFG Alignment')
    plt.legend()
    plt.grid(True)
    plt.savefig('benchmark_results.png')
    plt.show()


if __name__ == "__main__":
    datasets = {
        "sepsis": "Sepsis Cases - Event Log.xes.gz",
        "traffic_fines": "Road_Traffic_fine_management_Process.xes.gz",
        "dreyers_fond": "Dreyers Foundation.xes"
    }

    all_results = {}

    for dataset, log_file in datasets.items():
        print(f"Running benchmark for {dataset}")
        results = run_benchmark(dataset, log_file, f"{dataset}_benchmark_results.csv", repeat=5)
        all_results[dataset] = results

    plot_results(all_results)
