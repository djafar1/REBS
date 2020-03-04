import numpy as np
from scipy.spatial.distance import pdist
from pm4py.algo.discovery.dfg import factory as dfg_factory
from pm4py.algo.filtering.log.attributes import attributes_filter
import pandas as pd
from pm4py.algo.clustering.hierarchical_attribute_based.variant import act_dist_calc


def dfg_dist_calc_act(log1, log2):
    act1 = attributes_filter.get_attribute_values(log1, "concept:name")
    act2 = attributes_filter.get_attribute_values(log2, "concept:name")
    df1_act = act_dist_calc.occu_var_act(act1)
    df2_act = act_dist_calc.occu_var_act(act2)
    df_act = pd.merge(df1_act, df2_act, how='outer', on='var').fillna(0)
    # print(df_act)
    dist_act = pdist(np.array([df_act['freq_x'].values, df_act['freq_y'].values]), 'cosine')[0]
    # print([dist_act, dist_dfg])
    # dist = dist_act * alpha + dist_dfg * (1 - alpha)
    return dist_act


def dfg_dist_calc_suc(log1, log2):
    dfg1 = dfg_factory.apply(log1)
    dfg2 = dfg_factory.apply(log2)
    df1_dfg = act_dist_calc.occu_var_act(dfg1)
    df2_dfg = act_dist_calc.occu_var_act(dfg2)
    df_dfg = pd.merge(df1_dfg, df2_dfg, how='outer', on='var').fillna(0)
    # print(df_dfg)
    dist_dfg = pdist(np.array([df_dfg['freq_x'].values, df_dfg['freq_y'].values]), 'cosine')[0]
    return dist_dfg


def dfg_dist_calc(log1, log2):
    act1 = attributes_filter.get_attribute_values(log1, "concept:name")
    # print("act1", act1)
    act2 = attributes_filter.get_attribute_values(log2, "concept:name")
    # print("act2", act2)
    dfg1 = dfg_factory.apply(log1)
    dfg2 = dfg_factory.apply(log2)
    df1_act = act_dist_calc.occu_var_act(act1)
    # print("dfg1", dfg1)
    df2_act = act_dist_calc.occu_var_act(act2)
    df1_dfg = act_dist_calc.occu_var_act(dfg1)
    df2_dfg = act_dist_calc.occu_var_act(dfg2)
    df_act = pd.merge(df1_act, df2_act, how='outer', on='var').fillna(0)
    # print("df_act", df_act)
    # print(df_act)
    df_dfg = pd.merge(df1_dfg, df2_dfg, how='outer', on='var').fillna(0)
    # print(df_act)
    # print("df_dfg", df_dfg)
    dist_act = pdist(np.array([df_act['freq_x'].values, df_act['freq_y'].values]), 'cosine')[0]
    dist_dfg = pdist(np.array([df_dfg['freq_x'].values, df_dfg['freq_y'].values]), 'cosine')[0]
    if (np.isnan(dist_dfg) == True):
        dist_dfg = 1
    # print([dist_act, dist_dfg])
    # dist = dist_act * alpha + dist_dfg * (1 - alpha)
    return dist_act, dist_dfg


def dfg_dist_calc_minkowski(log1, log2, alpha):
    act1 = attributes_filter.get_attribute_values(log1, "concept:name")
    act2 = attributes_filter.get_attribute_values(log2, "concept:name")
    dfg1 = dfg_factory.apply(log1)
    dfg2 = dfg_factory.apply(log2)
    df1_act = act_dist_calc.occu_var_act(act1)
    df2_act = act_dist_calc.occu_var_act(act2)
    df1_dfg = act_dist_calc.occu_var_act(dfg1)
    df2_dfg = act_dist_calc.occu_var_act(dfg2)
    df_act = pd.merge(df1_act, df2_act, how='outer', on='var').fillna(0)
    # print(df_act)
    df_dfg = pd.merge(df1_dfg, df2_dfg, how='outer', on='var').fillna(0)
    # print(df_dfg)
    dist_act = pdist(np.array([df_act['freq_x'].values / np.sum(df_act['freq_x'].values),
                               df_act['freq_y'].values / np.sum(df_act['freq_y'].values)]), 'minkowski', p=2.)[0]
    dist_dfg = pdist(np.array([df_dfg['freq_x'].values / np.sum(df_dfg['freq_x'].values),
                               df_dfg['freq_y'].values / np.sum(df_dfg['freq_y'].values)]), 'minkowski', p=2.)[0]
    print([dist_act, dist_dfg])
    dist = dist_act * alpha + dist_dfg * (1 - alpha)
    return dist
