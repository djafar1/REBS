import numpy as np
import pandas as pd
from pathlib import Path
import pm4py
from scipy.stats import norm
from scipy.stats import combine_pvalues
import numpy as np
import random

from os.path import join

log_types = ['Training Logs', 'Test Logs', 'Base Logs', 'Ground Truth Logs']

class UniformDistribution(object):
    '''
    https://levelup.gitconnected.com/understanding-uniform-distribution-and-cracking-the-data-science-interview-a8404166330d
    '''
    def __init__(self, a, b) -> None:
        super().__init__()
        self.a = a
        self.b = b

    def sample(self, x):
        if self.a <= x <= self.b:
            return 1
        else:
            return 0

    def pdf(self, x):
        if self.a <= x <= self.b:
            return 1/(self.b - self.a)
        else:
            return 0

    def pdf_indicator(self, x):
        return (self.indicator_a(x)*self.indicator_b(x))/(self.b-self.a)

    def cdf(self, x):
        if x < self.a:
            return 0
        elif self.a <= x <= self.b:
            return (x - self.a)/(self.b - self.a)

    def indicator_a(self, x):
        if x < self.a:
            return 0
        else:
            return 1

    def indicator_b(self, x):
        if x > self.b:
            return 0
        else:
            return 1

    def likelihood(self, X):
        n = len(X)
        return (1/(self.b - self.a)**n)*np.prod([self.indicator_a(x)*self.indicator_b(x) for x in X])

    def mle(self, X):
        self.a = np.min(X)
        self.b = np.max(X)
        return self.a, self.b

def hist_for_log_exact(pdc_log):
    events = pdc_log['concept:name'].unique()
    pdc_log['case:int'] = pdc_log['case:concept:name'].str.split(' ').apply(
        lambda x: int(f'{x[1]}{x[2] if len(x) > 2 else ""}'))
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
            'event:order'].to_list()  # .value_counts().to_dict()
    return pdc_log  # hist_for_event


def hist_for_log(pdc_log):
    events = pdc_log['concept:name'].unique()
    pdc_log['case:int'] = pdc_log['case:concept:name'].str.split(' ').apply(
        lambda x: int(f'{x[1]}{x[2] if len(x) > 2 else ""}'))
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


def enrich_log(pdc_log):
    pdc_log['case:int'] = pdc_log['case:concept:name'].str.split(' ').apply(
        lambda x: int(f'{x[1]}{x[2] if len(x) > 2 else ""}'))
    pdc_log['event:order'] = pdc_log.groupby('case:int').cumcount()
    group_size = pdc_log.groupby('case:int').size()
    group_size = group_size.reset_index()
    group_size.columns = ['case:int', 'case:size']
    group_size['case:size'] = group_size['case:size'] - 1
    new_df = pd.merge(pdc_log, group_size, on='case:int', how='left')
    new_df['event:rel'] = new_df['event:order'] / new_df['case:size']
    return new_df


def hist_for_five_train_logs(pdc_logs, use_order=False):
    binning_column = 'event:rel'
    if use_order:
        binning_column = 'event:order'
    hist_for_event = {}
    for pdc_log in pdc_logs:
        pdc_log = enrich_log(pdc_log)
        for event in pdc_log['concept:name'].unique():
            if event not in hist_for_event:
                hist_for_event[event] = pdc_log[pdc_log['concept:name'] == event][
                    binning_column].to_list()  # .value_counts().to_dict()
            else:
                hist_for_event[event].extend(pdc_log[pdc_log['concept:name'] == event][binning_column].to_list())
        # x = res
        # y = hist_for_event
        # this is a fancy way to merge dictionaries
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


def classification_result(trace_to_test, only_file, base_log, test_log, logs_hists_for_events):
    # 0.772 f1 score
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    sum_of_test = 0
    sum_of_base = 0
    for event in test_case['concept:name'].unique():
        # print(event)
        train_pos = logs_hists_for_events[only_file][log_types[0]][event]
        train_pos = np.array(train_pos)
        mu, sigma = norm.fit(train_pos[~np.isnan(train_pos)])
        test_pos = test_case[test_case['concept:name'] == event]['event:rel'].mean()
        # print(f'[i] z-score: {(test_pos-mu)/sigma}')
        base_pos = base_case[base_case['concept:name'] == event]['event:rel'].mean()
        sum_of_test += abs(test_pos - mu)
        sum_of_base += abs(test_pos - base_pos)
    if sum_of_test >= sum_of_base:
        # print('[!] This stupid alg says: base wins!')
        return False
    else:
        # print('[!] This stupid alg says: training wins!')
        return True
    # cdf_value = norm.cdf(test_pos,loc=mu,scale=sigma)
    # significance_level = 0.05
    # # Check if the CDF value is within the range [significance_level/2, 1 - significance_level/2]
    # if significance_level / 2 < cdf_value < 1 - significance_level / 2:
    #     print(f"[!] Event {event} - I predict the training fits better {cdf_value}")
    # else:
    #     print(f"[!] Event {event} - I predict the base fits better {cdf_value}")


def classification_result_1(trace_to_test, only_file, base_log, test_log, logs_hists_for_events):
    # 0.83 F1 score
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    base_set = set(base_case['concept:name'])
    test_set = set(test_case['concept:name'])
    if len(base_set.difference(test_set)) > 0:
        return False
    elif len(test_set.difference(base_set)) > 0:
        return True
    else:
        return bool(random.getrandbits(1))  # classification_result_5(trace_to_test, only_file)


def classification_result_1_2(trace_to_test, only_file, base_log, test_log, logs_hists_for_events):
    # 0.83 F1 score
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    base_set = set(base_case['concept:name'])
    test_set = set(test_case['concept:name'])
    base_len = len(base_case['concept:name'])
    test_len = len(test_case['concept:name'])
    if len(base_set.difference(test_set)) > 0:
        return False
    elif len(test_set.difference(base_set)) > 0:
        return True
    elif base_len <= test_len:
        return False
    else:
        return True


def classification_result_1_3(trace_to_test, only_file, base_log, test_log, logs_hists_for_events):
    # 0.83 F1 score
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    base_set = set(base_case['concept:name'])
    test_set = set(test_case['concept:name'])
    base_len = len(base_case['concept:name'])
    test_len = len(test_case['concept:name'])
    if len(base_set.difference(test_set)) > 0:
        return False
    else:
        return True


def classification_result_2(trace_to_test, only_file, base_log, test_log, logs_hists_for_events):
    # 0.69 F1 score
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    sum_of_test = 0
    sum_of_base = 0
    for event in set(test_case['concept:name']).intersection(set(base_case['concept:name'])).intersection(
            set(logs_hists_for_events[only_file][log_types[0]])):  # test_case['concept:name'].unique():
        # print(event)
        train_pos = logs_hists_for_events[only_file][log_types[0]][event]
        train_pos = np.array(train_pos)
        mu, sigma = norm.fit(train_pos[~np.isnan(train_pos)])
        test_pos = test_case[test_case['concept:name'] == event]['event:rel'].mean()
        # print(f'[i] z-score: {(test_pos-mu)/sigma}')
        base_pos = base_case[base_case['concept:name'] == event]['event:rel'].mean()
        if sigma > 0:
            sum_of_test += abs((test_pos - mu) / sigma)
            sum_of_base += abs((base_pos - mu) / sigma)
        else:
            if abs(test_pos - mu) > 0.1:
                sum_of_test += 1
            if abs(base_pos - mu) > 0.1:
                sum_of_base += 1
    if sum_of_test >= sum_of_base:
        # print('[!] This stupid alg says: base wins!')
        return False
    else:
        # print('[!] This stupid alg says: training wins!')
        return True


def classification_result_3(trace_to_test, only_file, base_log, test_log, logs_hists_for_events):
    #
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    p_test = []
    p_base = []
    for event in test_case['concept:name'].unique():
        train_pos = logs_hists_for_events[only_file][log_types[0]][event]
        train_pos = np.array(train_pos)
        mu, sigma = norm.fit(train_pos[~np.isnan(train_pos)])
        test_pos = test_case[test_case['concept:name'] == event]['event:rel'].mean()
        base_pos = base_case[base_case['concept:name'] == event]['event:rel'].mean()
        if sigma > 0:
            p_test.append(norm.sf(abs((test_pos - mu) / sigma)) * 2)
            p_base.append(norm.sf(abs((base_pos - mu) / sigma)) * 2)
        else:
            pass
    sum_of_test = combine_pvalues(np.array(p_test), method='mudholkar_george')
    sum_of_base = combine_pvalues(np.array(p_base), method='mudholkar_george')
    if sum_of_test.pvalue >= sum_of_base.pvalue:
        # print('[!] This stupid alg says: base wins!')
        return False
    else:
        # print('[!] This stupid alg says: training wins!')
        return True


def classification_result_4(trace_to_test, only_file, base_log, test_log, logs_hists_for_events):
    #
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    score_test = 0
    score_base = 0
    for event in test_case['concept:name'].unique():
        train_pos = logs_hists_for_events[only_file][log_types[0]][event]
        train_pos = np.array(train_pos)
        mu, sigma = norm.fit(train_pos[~np.isnan(train_pos)])
        train_pos_min = mu - sigma
        train_pos_max = mu + sigma
        test_pos_min = test_case[test_case['concept:name'] == event]['event:rel'].min()
        test_pos_max = test_case[test_case['concept:name'] == event]['event:rel'].max()
        base_pos_min = base_case[base_case['concept:name'] == event]['event:rel'].min()
        base_pos_max = base_case[base_case['concept:name'] == event]['event:rel'].max()
        if train_pos_min < 0:
            train_pos_min = 0
        if test_pos_min >= train_pos_min:
            score_test += 1
        if test_pos_max <= train_pos_max:
            score_test += 1
        if base_pos_min >= train_pos_min:
            score_base += 1
        if base_pos_max <= train_pos_max:
            score_base += 1

    if score_test <= score_base:
        # print('[!] This stupid alg says: base wins!')
        return False
    else:
        # print('[!] This stupid alg says: training wins!')
        return True


def classification_result_5(trace_to_test, only_file, base_log, test_log, logs_hists_for_events):
    #
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    score_test = 0
    score_base = 0
    for event in test_case['concept:name'].unique():
        train_pos = logs_hists_for_events[only_file][log_types[0]][event]
        train_pos = np.array(train_pos)
        # mu, sigma = norm.fit(train_pos[~np.isnan(train_pos)])
        # sigma_scale = 1
        train_pos_min = train_pos[~np.isnan(train_pos)].min()  # mu-sigma_scale*sigma
        train_pos_max = train_pos[~np.isnan(train_pos)].max()  # mu+sigma_scale*sigma
        if train_pos_min < 0:
            train_pos_min = 0
        # train_uniform = UniformDistribution(train_pos_min, train_pos_max)
        test_pos_min = test_case[test_case['concept:name'] == event]['event:rel'].min()
        test_pos_max = test_case[test_case['concept:name'] == event]['event:rel'].max()
        # test_uniform = UniformDistribution(test_pos_min,test_pos_max)
        base_pos_min = base_case[base_case['concept:name'] == event]['event:rel'].min()
        base_pos_max = base_case[base_case['concept:name'] == event]['event:rel'].max()
        # base_uniform = UniformDistribution(base_pos_min,base_pos_max)
        # print(f'{trace_to_test} {event}: Train:[{train_pos_min},{train_pos_max}] Test: [{test_pos_min},{test_pos_max}] Base: [{base_pos_min},{base_pos_max}]')
        if test_pos_min >= train_pos_min:
            score_test += 1
        if test_pos_max <= train_pos_max:
            score_test += 1
        if base_pos_min >= train_pos_min:
            score_base += 1
        if base_pos_max <= train_pos_max:
            score_base += 1

    if score_test <= score_base:
        # print('[!] This stupid alg says: base wins!')
        return False
    else:
        # print('[!] This stupid alg says: training wins!')
        return True


def classification_result_6(trace_to_test, only_file, base_log, test_log, logs_hists_for_events):
    #
    base_case = base_log[base_log['case:concept:name'] == trace_to_test]
    test_case = test_log[test_log['case:concept:name'] == trace_to_test]
    score_test = 0
    score_base = 0
    for event in test_case['concept:name'].unique():
        if event in base_case['concept:name'].unique():
            train_pos = logs_hists_for_events[only_file][log_types[0]][event]
            train_pos = np.array(train_pos)
            mu, sigma = norm.fit(train_pos[~np.isnan(train_pos)])
            sigma_scale = 1
            train_pos_min = mu - sigma_scale * sigma
            train_pos_max = mu + sigma_scale * sigma
            if train_pos_min < 0:
                train_pos_min = 0
            train_pdf = 1 / (train_pos_max - train_pos_min)
            test_pos_mean = test_case[test_case['concept:name'] == event]['event:rel'].mean()
            base_pos_mean = base_case[base_case['concept:name'] == event]['event:rel'].mean()
            if test_pos_mean != base_pos_mean:
                # print(f'{trace_to_test} {event}: Train:[{train_pos_min},{train_pos_max}] Test: [{test_pos_mean}] Base: [{base_pos_mean}]')
                u = UniformDistribution(train_pos_min, train_pos_max)
                score_test += u.sample(test_pos_mean)
                score_base += u.sample(base_pos_mean)
    if score_test <= score_base:
        # print('[!] This stupid alg says: base wins!')
        return False
    else:
        # print('[!] This stupid alg says: training wins!')
        return True


def get_one_log_train_test_base_gt(only_file):
    status = Path(only_file).stem.split('_')[1]
    five_train_logs = []
    for i in range(5):
        train_log = pm4py.read_xes(
            join('/home/vco/Datasets/PDC22/', log_types[0], f'{only_file[:-4]}{i}{only_file[-4:]}'))
        five_train_logs.append(train_log)
    test_log = pm4py.read_xes(join('/home/vco/Datasets/PDC22/', log_types[1], only_file))
    base_log = pm4py.read_xes(join('/home/vco/Datasets/PDC22/', log_types[2], only_file))
    gt_log = pm4py.read_xes(join('/home/vco/Datasets/PDC22/', log_types[3], only_file))

    logs_hists_for_events = {
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

    return logs_hists_for_events, test_log, base_log, gt_log, ground_truths
