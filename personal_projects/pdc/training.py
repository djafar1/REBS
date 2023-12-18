import numpy as np
import pandas as pd
from pathlib import Path
import pm4py
from scipy.stats import norm
import numpy as np
import matplotlib.pyplot as plt
from pm4py.algo.evaluation.dcr import algorithm as eval_dcr_on_pdc

from os import listdir
from os.path import isfile, join
from scipy.stats import ks_2samp, kstest, combine_pvalues

from pm4py.algo.conformance.alignments.edit_distance import algorithm as ed_align
from pm4py.algo.conformance.antialignments import algorithm as aa_align

def hist_for_log(pdc_log):
    events = pdc_log['concept:name'].unique()
    pdc_log['case:int'] = pdc_log['case:concept:name'].str.split(' ').apply(lambda x: int(f'{x[1]}{x[2]}'))
    pdc_log['event:order'] = pdc_log.groupby('case:int').cumcount()
    group_size = pdc_log.groupby('case:int').size()
    group_size = group_size.reset_index()
    group_size.columns = ['case:int', 'case:size']
    group_size['case:size'] = group_size['case:size'] - 1
    new_df = pd.merge(pdc_log, group_size, on='case:int', how='left')
    new_df['event:rel'] = new_df['event:order'] / new_df['case:size']
    pdc_log = new_df
    hist_for_event = {}
    for event in events:
        hist_for_event[event] = pdc_log[pdc_log['concept:name'] == event][
            'event:rel'].to_list()  # .value_counts().to_dict()
    return pdc_log  # hist_for_event


def hist_for_five_train_logs(pdc_logs):
    events = pdc_logs[0]['concept:name'].unique()
    hist_for_event = {}
    for pdc_log in pdc_logs:
        pdc_log['case:int'] = pdc_log['case:concept:name'].str.split(' ').apply(lambda x: int(x[1]))
        pdc_log['event:order'] = pdc_log.groupby('case:int').cumcount()
        group_size = pdc_log.groupby('case:int').size()
        group_size = group_size.reset_index()
        group_size.columns = ['case:int', 'case:size']
        group_size['case:size'] = group_size['case:size'] - 1
        new_df = pd.merge(pdc_log, group_size, on='case:int', how='left')
        new_df['event:rel'] = new_df['event:order'] / new_df['case:size']
        pdc_log = new_df
        # hist_for_event = {}
        for event in events:
            if event not in hist_for_event:
                hist_for_event[event] = pdc_log[pdc_log['concept:name'] == event][
                    'event:rel'].to_list()  # .value_counts().to_dict()
            else:
                hist_for_event[event].extend(pdc_log[pdc_log['concept:name'] == event]['event:rel'].to_list())
        # x = res
        # y = hist_for_event
        # res = {j:{k: x.get(j,{}).get(k, 0) + y.get(j,{}).get(k, 0) for k in set(x.get(j,{})) | set(y.get(j,{}))} for j in set(x) | set(y)}
    return hist_for_event


def case_from_gt(case_to_test, ground_truths):
    case_is_pos = ground_truths[ground_truths['case:concept:name'] == case_to_test]['case:pdc:isPos'].item()
    if case_is_pos:
        # print(f'[i] gt says: {case_to_test} training wins!')
        return True
    else:
        # print(f'[i] gt says: {case_to_test} base wins!')
        return False
def classification_result(trace_to_test, only_file, logs_hists_for_events, base_log, test_log, ground_truths):
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    case_is_pos = ground_truths[ground_truths['case:concept:name'] == trace_to_test]['case:pdc:isPos'].item()
    sum_base = 0
    sum_test = 0
    for event in test_case['concept:name'].unique():
        train_pos = logs_hists_for_events[only_file][log_types[0]][event]
        train_pos = np.array(train_pos)
        train_pos = train_pos[~np.isnan(train_pos)]
        mu, sigma = norm.fit(train_pos)
        test_arr = np.array(test_case[test_case['concept:name'] == event]['event:rel'].to_list())
        test_arr = test_arr[~np.isnan(test_arr)]
        base_arr = np.array(base_case[base_case['concept:name'] == event]['event:rel'].to_list())
        base_arr = base_arr[~np.isnan(base_arr)]
        if len(test_arr) > 0 and len(base_arr) > 0:
            test_pos = test_case[test_case['concept:name'] == event]['event:rel'].mean()
            base_pos = base_case[base_case['concept:name'] == event]['event:rel'].mean()
            if test_pos != base_pos:
                sum_test += np.sqrt(abs(mu**2-test_pos**2))
                sum_base += np.sqrt(abs(mu**2-base_pos**2))
    gt_training_wins = False
    gt_base_wins = False
    if case_is_pos:
        # print(f'[i] gt says: {trace_to_test} training wins!')
        gt_training_wins = True
    else:
        # print(f'[i] gt says: {trace_to_test} base wins!')
        gt_base_wins = True
    if sum_test >= sum_base:
        # print(f'[!] This stupid alg says: base wins! The alg is {gt_base_wins}')
        return False
    else:
        # print(f'[!] This stupid alg says: training wins! The alg is {gt_training_wins}')
        return True


def score_one_file(only_file, logs_hists_for_events):
    status = Path(only_file).stem.split('_')[1]
    five_train_logs = []
    for i in range(5):
        train_log = pm4py.read_xes(
            join('/home/vco/Datasets/PDC22/', log_types[0], f'{only_file[:-4]}{i}{only_file[-4:]}'))
        five_train_logs.append(train_log)
    test_log = pm4py.read_xes(join('/home/vco/Datasets/PDC22/', log_types[1], only_file))
    base_log = pm4py.read_xes(join('/home/vco/Datasets/PDC22/', log_types[2], only_file))
    gt_log = pm4py.read_xes(join('/home/vco/Datasets/PDC22/', log_types[3], only_file))

    logs_hists_for_events[only_file] = {
        log_types[0]: hist_for_five_train_logs(five_train_logs),
        # log_types[1]: hist_for_log(test_log),
        # log_types[2]: hist_for_log(base_log),
        # log_types[3]: hist_for_log(gt_log)
    }
    test_log = hist_for_log(test_log)
    cases_to_test = set(test_log['case:concept:name'].unique())
    base_log = hist_for_log(base_log)
    gt_log = hist_for_log(gt_log)
    ground_truths = gt_log[['case:concept:name', 'case:pdc:isPos']].drop_duplicates()

    confusion_matrix = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}
    for case_to_test in cases_to_test:
        gt_says = case_from_gt(case_to_test, ground_truths)
        training_says = classification_result(case_to_test, only_file, logs_hists_for_events, base_log, test_log,ground_truths)
        if gt_says == training_says and training_says:
            confusion_matrix['TP'] += 1
        elif gt_says == training_says and not training_says:
            confusion_matrix['TN'] += 1
        elif gt_says and not training_says:
            confusion_matrix['FN'] += 1
        elif not gt_says and training_says:
            confusion_matrix['FP'] += 1
    # print(confusion_matrix)
    score = eval_dcr_on_pdc.pdcFscore(confusion_matrix['TP'], confusion_matrix['FP'], confusion_matrix['TN'],
                                      confusion_matrix['FN'])
    print(f'[i] For file {only_file} PDC F1 Score: {score}')
    return score, confusion_matrix


if __name__ == "__main__":
    log_types = ['Training Logs', 'Test Logs', 'Base Logs', 'Ground Truth Logs']
    mypath = '/home/vco/Datasets/PDC22/Base Logs/'
    only_files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    logs_hists_for_events = {}

    # only_file = 'pdc2022_100110.xes'
    # pdcf1, cm = score_one_file(only_file, logs_hists_for_events)
    # print(f'[i] PDC F1 {pdcf1} Confusion Matrix: {cm}')

    list_of_f1s = []
    min_score_file = ''
    min_score = 1
    for only_file in only_files:
        score, confusion_matrix = score_one_file(only_file, logs_hists_for_events)
        if score < min_score:
            min_score = score
            min_score_file = only_file
        list_of_f1s.append(score)
    print(f'[i] Average PDC F1 Score {np.mean(list_of_f1s)}')
    print(f'[i] Lowest score event log {min_score_file} with PDC F1 {min_score}')
