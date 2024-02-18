import math
import pandas as pd
import pm4py
import matplotlib.pyplot as plt
from fitter import Fitter, get_common_distributions, get_distributions
from pm4py.util.external_functions import *
import networkx as nx

r = np.random  # Random generator
r.seed(1)
import numpy as np
import causalicp as icp
from sklearn.linear_model import LogisticRegression
from copy import deepcopy


def show_graph_with_labels(adjacency_matrix, mylabels=None):
    rows, cols = np.where(adjacency_matrix == 1)
    edges = zip(rows.tolist(), cols.tolist())
    gr = nx.DiGraph()
    gr.add_edges_from(edges)
    for layer, nodes in enumerate(nx.topological_generations(gr)):
        # `multipartite_layout` expects the layer as a node attribute, so add the
        # numeric layer value as a node attribute
        for node in nodes:
            gr.nodes[node]["layer"] = layer
    plt.figure(figsize=(10, 10))
    pos = nx.multipartite_layout(gr, subset_key="layer")
    if mylabels:
        nx.draw(gr, pos=pos, node_size=500, labels=mylabels, with_labels=True, font_size=15,
                             horizontalalignment='center', verticalalignment='bottom', clip_on=False)
    else:
        nx.draw(gr, node_size=100, with_labels=False, font_size=8)
    plt.show()


def fit_and_plot_fine_list(fine_list):
    xmin = 0
    xmax = 100
    density = False
    Nbins, binwidth = freedman_diaconis_rule(fine_list)
    size_of_data = len(fine_list)
    counts, bin_edges = np.histogram(fine_list, bins=Nbins, range=(xmin, xmax), density=density)
    x = (bin_edges[1:][counts > 0] + bin_edges[:-1][counts > 0]) / 2
    y = counts[counts > 0]
    sy = np.sqrt(counts[counts > 0])
    fig, ax = plt.subplots(figsize=(16, 5))
    counts, bins, bars = ax.hist(fine_list, bins=Nbins, range=(xmin, xmax), histtype='step',
                                 density=density, alpha=1, color='g',
                                 label='Binned Data')
    ax.errorbar(x, y, yerr=sy, xerr=0.0, label='Data, with Poisson errors', fmt='.k', ecolor='k', elinewidth=1, capsize=1, capthick=1)
    f = Fitter(fine_list, distributions=get_common_distributions(), xmax=None, timeout=2 * 60, bins=Nbins, density=density)
    f.fit()
    # here you get the rss fit scores
    res = f.summary(plot=False)
    residual_sumssquare_error = res.iloc[0].sumsquare_error
    aic = res.iloc[0].aic
    kl_div = res.iloc[0].kl_div
    best_dist, fitted_params = f.get_best().popitem()

    size = 1000
    dist_func = getattr(stats, best_dist)
    start = dist_func.ppf(0.01, **fitted_params)
    end = dist_func.ppf(0.99, **fitted_params)
    x = np.linspace(start, end, size)
    y = dist_func.pdf(x, **fitted_params)
    if not density:
        y = y * size_of_data
    pdf = pd.Series(y, x)
    pdf.plot(lw=2, label=f'PDF of {best_dist}', color='r', legend=True)

    # ax.plot(f.fitted_pdf[best_dist],label=f'Best fit {best_dist}')
    d = {'Fitter best': f'{best_dist}',
         **fitted_params}
    text = nice_string_output(d, extra_spacing=2, decimals=3)
    add_text_to_ax(0.7, 0.6, text, ax, fontsize=14)
    ax.set_xlabel('Duration (Days)')
    ax.set_ylabel('Binned count')
    ax.set_xlim([xmin - 10, xmax])
    # ax.set_ylim([0,0.5])

    ax.set_title(f'Plot of Create Fine amount')
    ax.legend()
    fig.tight_layout()
    return dist_func ,best_dist, fitted_params

def box_plot_fine_amount(road_traffic_train):
    fine_amount = road_traffic_train[road_traffic_train['concept:name']=='Create Fine']['amount']
    fine_list = fine_amount#[fine_amount.lt(600)]
    fig, ax = plt.subplots(figsize=(16, 5))
    ax.set_xlim(xmin=0, xmax=100)
    res = ax.boxplot(fine_list, vert=False)
    print([item.get_xdata()[1] for item in res['whiskers']])
    return fine_list


def case_to_data_entry(case_df, events, attribute_data_type):
    '''
    Take all events and record 1 or 0 if they are observed in the trace.
    If events are unfolded, each repetition is a new event with an index.
    Take all data attributes and record their value.
    If all values are not the same, take the one that on average is more likely to occur.
    '''
    data_dict = {}
    for event in events:
        data_dict[event] = 1 if event in case_df['concept:name'].to_list() else 0
    for attr, data_type in attribute_data_type.items():
        if data_type == 'categorical':
            cats = case_df[case_df[attr].notna()][attr].value_counts().index
            if len(cats) > 0:
                data_dict[attr] = cats[0]  # now it is only the most likely value
        if data_type == 'numerical' and len(case_df[case_df[attr].notna()][attr]) > 0:
            data_dict[attr] = case_df[case_df[attr].notna()][attr].mean()
    return data_dict


always_executed_events = set()


def get_always_executed_events():
    return always_executed_events


def extract_event_binomial(event, log, unfolded=False, group_threshold=1):
    # return the probability of observation as a binomial distribution
    events = [event]
    has_unfolded = False
    if unfolded:
        res, new_events = extract_event_unfolded(event, deepcopy(log))
        if res is not None and len(new_events) > 0:
            log = res
            has_unfolded = True
            events.append(new_events)
    e_func_dict = {}
    merge_instances = []
    merge_probs = False
    probs = []
    for e in events:
        no_cases = len(log['case:concept:name'].unique())
        event_cases = len(log[log['concept:name'] == e]['case:concept:name'].unique())
        prob = event_cases / no_cases
        if prob == 1:
            always_executed_events.add(e)
            print(f'[i] Event {e} prob of success: {prob:.2f}')
            e_func_dict[e] = (lambda: r.choice([1, 0], p=[prob, (1 - prob)]), prob)
        elif has_unfolded and prob < group_threshold:
            merge_probs = True
            merge_instances += e
        else:
            probs.append(prob)
            print(f'[i] Event {e} prob of success: {prob:.2f}')
            e_func_dict[e] = (lambda: r.choice([1, 0], p=[prob, (1 - prob)]), prob)
    if has_unfolded and merge_probs:
        remaining_prob = 1 - sum(probs)
        merge_name = ''.join(merge_instances)
        print(f'[i] Merged event {merge_name} prob of success: {remaining_prob:.2f}')
        e_func_dict[merge_name] = (lambda: r.choice([1, 0], p=[remaining_prob, (1 - remaining_prob)]), remaining_prob)
    return e_func_dict


def extract_event_unfolded(event, log):
    # unfold the event (each subsequent execution after the first one is a new binomial variable)
    i = 1
    new_events = []
    while (True):
        log['case:concept:name:d'] = log['case:concept:name'].shift(i)
        mask = log['case:concept:name'] == log['case:concept:name:d']
        if any(mask):
            new_event_name = f"{event}{i}"
            log.loc[mask, 'concept:name'] = new_event_name
            new_events.append(new_event_name)
            i += 1
        else:
            break
    log = log.drop(['case:concept:name:d'], axis=1)
    if i == 1:
        return None, new_events
    else:
        return log, new_events


def extract_event_multinomial(event, log):
    # each of the n observed event executions is part of a multinomial distribution
    pass


def extract_categorical_data_attribute(events, data_attribute, log, data_instances_to_ignore=[], group_threshold=0.1):
    # fit a multinomial distribution
    all_instances = log[(log['concept:name'].isin(events)) & ~(log[data_attribute].isin(data_instances_to_ignore))].groupby(data_attribute, dropna=False).count()[
        'concept:name'].sort_values(ascending=False)
    all_sum = all_instances.sum()
    pvals = []
    pdict = {}
    print(f'[i] For categorical data attribute: {data_attribute}')
    merge_instances = []
    merge_probs = False
    for k, v in all_instances.to_dict().items():
        prob = v / all_sum
        if prob < group_threshold:
            merge_instances.append(k)
            merge_probs = True
        else:
            pvals.append(prob)
            pdict[k] = prob
            print(f'[i] Data instance {k} prob of success {prob:.2f}')

    if merge_probs:
        inst_str = ''.join(merge_instances)
        remaining_prob = 1 - sum(pvals)
        print(f'[i] Merged instance {inst_str} prob of success {remaining_prob:.2f}')
        pvals.append(remaining_prob)
        pdict[inst_str] = remaining_prob

    return lambda: r.multinomial(1, pvals=pvals), pdict


def extract_numerical_data_attribute(events, data_attribute, log):
    '''

    Parameters
    ----------
    events
    data_attribute
    log

    Returns
    -------
    A lambda function with x as a parameter. x is the range of the data attribute, it returns the pdf over the range of x
    To use the result you can:
    x = np.linspace(start, end, size)
    y = extract_numerical_data_attribute().__call__(x)
    pdf = pd.Series(y, x)
    pdf.plot(lw=2, label=f'PDF of {best_dist}', color='r', legend=True)
    '''
    data = log[log['concept:name'].isin(events)][data_attribute]
    Nbins, binwidth = freedman_diaconis_rule(data)
    f = Fitter(data, distributions=get_common_distributions(), timeout=2 * 60, bins=Nbins, density=True)
    f.fit()
    # here you get the rss fit scores
    res = f.summary(plot=False)
    residual_sumssquare_error = res.iloc[0].sumsquare_error
    aic = res.iloc[0].aic
    kl_div = res.iloc[0].kl_div
    best_dist, fitted_params = f.get_best().popitem()

    dist_func = getattr(stats, best_dist)
    print(f'[i] For numerical data attribute: {data_attribute} dist:{best_dist} params:{fitted_params}')
    return lambda x: dist_func.pdf(x, **fitted_params)


def extract_categorical_data_attribute_per_event(event, data_attribute, log, data_instances_to_ignore=[]):
    # fit a multinomial distribution
    all_instances = log[(log['concept:name'] == event) & ~(log[data_attribute].isin(data_instances_to_ignore))].groupby(data_attribute, dropna=False).count()[
        'concept:name'].sort_values(ascending=False)
    all_sum = all_instances.sum()
    pvals = []
    pdict = {}
    print(f'[i] For data attribute: {data_attribute}')
    for k, v in all_instances.to_dict().items():
        prob = v / all_sum
        pvals.append(prob)
        pdict[k] = prob
        print(f'[i] Data instance {k} prob of success {prob:.2f}')
    return lambda: r.multinomial(1, pvals=pvals), pdict


def extract_numerical_data_attribute_per_event(event, data_attribute, log):
    '''

    Parameters
    ----------
    events
    data_attribute
    log

    Returns
    -------
    A lambda function with x as a parameter. x is the range of the data attribute, it returns the pdf over the range of x
    To use the result you can:
    x = np.linspace(start, end, size)
    y = extract_numerical_data_attribute().__call__(x)
    pdf = pd.Series(y, x)
    pdf.plot(lw=2, label=f'PDF of {best_dist}', color='r', legend=True)
    '''
    data = log[log['concept:name'] == event][data_attribute]
    Nbins, binwidth = freedman_diaconis_rule(data)
    f = Fitter(data, distributions=get_common_distributions(), timeout=2 * 60, bins=Nbins, density=True)
    f.fit()
    # here you get the rss fit scores
    res = f.summary(plot=False)
    residual_sumssquare_error = res.iloc[0].sumsquare_error
    aic = res.iloc[0].aic
    kl_div = res.iloc[0].kl_div
    best_dist, fitted_params = f.get_best().popitem()

    dist_func = getattr(stats, best_dist)
    return lambda x: dist_func.pdf(x, **fitted_params)


def temporal_split(log, test_size):
    log = log.sort_values(['case:concept:name', 'time:timestamp'])
    cases = list(log['case:concept:name'].unique())
    no_cases = len(cases)
    _, test_size = math.modf(no_cases * test_size)
    test_size = int(test_size)
    test_cases = cases[(no_cases - test_size):]
    test_log = log[log['case:concept:name'].isin(test_cases)]
    train_log = log[~log['case:concept:name'].isin(test_cases)]
    return train_log, test_log


def extract_event_data_attributes(log, event, candidate_attributes):
    event_attributes = set()
    for cand_attr in candidate_attributes:
        if not log[log['concept:name'] == event][cand_attr].isnull().values.all():
            some_nulls = log[log['concept:name'] == event][cand_attr].isnull().values.any()
            event_attributes.add((cand_attr, some_nulls))
            # print(f'{event}[{cand_attr}] some_nulls {some_nulls}')
    return event_attributes
