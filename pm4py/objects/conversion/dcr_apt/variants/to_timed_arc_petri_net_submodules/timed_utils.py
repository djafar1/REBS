from pm4py.objects.petri_net.timed_arc_net.obj import *
from pm4py.objects.petri_net.utils import petri_utils as pn_utils
from pm4py.objects.dcr.obj import TemplateRelations as Relations
import pandas as pd
import numpy as np

from copy import deepcopy

# Function to copy rows of a specified event key n times
def copy_event_rows(src, trg, master_df, relation_table):
    needed_columns = master_df.loc[src][trg].columns
    needed_cases = relation_table[needed_columns]
    n = len(needed_cases)
    m = len(master_df.loc[src])
    repeated_df = pd.DataFrame(np.tile(master_df.loc[src], (n, 1)), columns=master_df.columns, index=pd.MultiIndex.from_product([[src], [i for i in range(n * m)]]))
    repeated_relation_df = pd.DataFrame(np.repeat(needed_cases, m, axis=0), columns=needed_cases.columns,
                                        index=pd.MultiIndex.from_product([[src], [i for i in range(n * m)]]))

    repeated_df.iloc[:, repeated_df.columns.get_level_values(0) == trg] = repeated_relation_df
    master_df = master_df.drop(src, level=0)
    master_df = pd.concat([master_df, repeated_df])
    return master_df


def prepare_timed_case(event_place, case, case_others, copy_to_all_index, copy_pairwise_index, event_to_deadline):
    pend_others = [f'Re_{v}' for k, v in event_to_deadline.items()]
    pend_excl_others = [f'Rex_{v}' for k, v in event_to_deadline.items()]
    if event_place:
        pend_place = f'Re_{event_place}'
        pend_others.remove(pend_place)
        pend_excl_place = f'Rex_{event_place}'
        pend_excl_others.remove(pend_excl_place)
        case = case.rename({'Re': pend_place, 'Rex': pend_excl_place}, axis='columns')
    else:
        if 'Re' in case.columns:
            case = case.drop(['Re'], axis='columns')
        if 'Rex' in case.columns:
            case = case.drop(['Rex'], axis='columns')

    x = len(pend_others)
    cols = pend_others
    cols.extend(pend_excl_others)
    case_all = pd.DataFrame(np.repeat(case_others.loc[copy_to_all_index], x, axis=1), index=copy_to_all_index, columns=cols)
    mat = case_others.loc[copy_pairwise_index].to_numpy()
    idx = np.repeat(copy_pairwise_index,x)
    ar = np.zeros([s * x for s in mat.shape], mat.dtype)
    for i in range(x):
        ar[i::x, i::x] = mat
    case_pairwise = pd.DataFrame(ar, columns=cols, index=idx)
    case = pd.concat([case, case_all], axis=1).fillna(0)
    case = case.astype(int)
    case = pd.concat([case, case.loc[copy_pairwise_index * (x - 1)]])
    case_pairwise = case_pairwise.sort_index()
    case.loc[copy_pairwise_index, cols] = case_pairwise
    # case = replace_submatrix(case, case_pairwise)
    return case

# def replace_submatrix(case, subcase):
#     return case

# def map_existing_transitions_of_copy_0(delta, copy_0, t, tapn) -> (TimedArcNet, TimedArcNet.Transition):
#     trans = copy_0[delta]
#     # if trans in tapn.transitions: # since this is a copy this cannot be checked here. trust me bro
#     # TODO: t is a new transition so, although not nice, it is safe to copy the transport index
#     #       if this is not true than I need to update the transport index in the converter after each call of this method
#     in_arcs = trans.in_arcs
#     for arc in in_arcs:
#         source = arc.source
#         type = arc.properties['arctype'] if 'arctype' in arc.properties else None
#         s_to_t = pn_utils.add_arc_from_to(source, t, tapn, type=type, with_check=True)
#         s_to_t.properties['agemin'] = arc.properties['agemin'] if 'agemin' in arc.properties else 0
#         s_to_t.properties['transportindex'] = arc.properties['transportindex'] if 'transportindex' in arc.properties else None
#     out_arcs = trans.out_arcs
#     for arc in out_arcs:
#         target = arc.target
#         type = arc.properties['arctype'] if 'arctype' in arc.properties else None
#         t_to_t = pn_utils.add_arc_from_to(t, target, tapn, type=type, with_check=True)
#         t_to_t.properties['agemin'] = arc.properties['agemin'] if 'agemin' in arc.properties else 0
#         t_to_t.properties['transportindex'] = arc.properties['transportindex'] if 'transportindex' in arc.properties else None
#     return tapn, t
#
#
# def create_event_pattern_transitions_and_arcs(tapn, event, helper_struct, mapping_exceptions):
#     inc_place = helper_struct[event]['places']['included']
#     exec_place = helper_struct[event]['places']['executed']
#     pend_places = helper_struct[event]['places']['pending']
#     pend_exc_places = helper_struct[event]['places']['pending_excluded']
#     i_copy = helper_struct[event]['trans_group_index']
#     ts = []
#     for t_name in set(helper_struct[event]['t_types']).intersection(set(['event','init'])):  # ['event','init'] - copy arcs:
#         t = TimedArcNet.Transition(f'{t_name}_{event}{i_copy}', f'{t_name}_{event}{i_copy}_label')
#         tapn.transitions.add(t)
#         # this if statement handles self response exclude
#         if event in mapping_exceptions.self_exceptions[frozenset([Relations.E.value, Relations.R.value])]:
#             for pend_exc_place, _ in pend_exc_places:
#                 pn_utils.add_arc_from_to(t, pend_exc_place, tapn)
#
#         pn_utils.add_arc_from_to(inc_place, t, tapn)
#         # this if statement handles self exclude and self response exclude
#         if not ((event in mapping_exceptions.self_exceptions[Relations.E.value]) or (
#                 event in mapping_exceptions.self_exceptions[frozenset([Relations.E.value, Relations.R.value])])):
#             pn_utils.add_arc_from_to(t, inc_place, tapn)
#
#         # this if statement handles self response
#         if event in mapping_exceptions.self_exceptions[Relations.R.value]:
#             for pend_place, _ in pend_places:
#                 pn_utils.add_arc_from_to(t, pend_place, tapn)
#
#         if t_name.__contains__('init'):
#             pn_utils.add_arc_from_to(t, exec_place, tapn)
#             pn_utils.add_arc_from_to(exec_place, t, tapn, type='inhibitor')
#         else:
#             pn_utils.add_arc_from_to(t, exec_place, tapn)
#             pn_utils.add_arc_from_to(exec_place, t, tapn)
#
#         if t_name.__contains__('pend'):
#             for pend_place, _ in pend_places:
#                 pn_utils.add_arc_from_to(pend_place, t, tapn)
#         else:
#             for pend_place, _ in pend_places:
#                 pn_utils.add_arc_from_to(pend_place, t, tapn, type='inhibitor')
#         ts.append(t)
#     for t_name in set(helper_struct[event]['t_types']).intersection(set(['initpend', 'pend'])):  # ['initpend','pend'] - copy transitions:
#         for k in range(len(pend_places)):
#             pend_place, e_prime = list(pend_places)[k]
#             name = f'{t_name}_{event}_by_{e_prime}{i_copy}' if len(e_prime) > 0 else f'{t_name}_{event}{i_copy}'
#             t = PetriNet.Transition(name, f'{name}_label')
#             tapn.transitions.add(t)
#             # this if statement handles self response exclude
#             # TODO: test this mf
#             if event in mapping_exceptions.self_exceptions[frozenset([Relations.E.value, Relations.R.value])]:
#                 pend_exc_place, _ = list(pend_exc_places)[k]
#                 pn_utils.add_arc_from_to(t, pend_exc_place, tapn)
#
#             pn_utils.add_arc_from_to(inc_place, t, tapn)
#             # this if statement handles self exclude and self response exclude
#             if not ((event in mapping_exceptions.self_exceptions[Relations.E.value]) or (
#                     event in mapping_exceptions.self_exceptions[frozenset([Relations.E.value, Relations.R.value])])):
#                 pn_utils.add_arc_from_to(t, inc_place, tapn)
#
#             # this if statement handles self response
#             if event in mapping_exceptions.self_exceptions[Relations.R.value]:
#                 pn_utils.add_arc_from_to(t, pend_place, tapn)
#
#             if t_name.__contains__('init'):
#                 pn_utils.add_arc_from_to(t, exec_place, tapn)
#                 pn_utils.add_arc_from_to(exec_place, t, tapn, type='inhibitor')
#             else:
#                 pn_utils.add_arc_from_to(t, exec_place, tapn)
#                 pn_utils.add_arc_from_to(exec_place, t, tapn)
#
#             if t_name.__contains__('pend'):
#                 pn_utils.add_arc_from_to(pend_place, t, tapn)
#             else:
#                 pn_utils.add_arc_from_to(pend_place, t, tapn, type='inhibitor')
#             ts.append(t)
#     helper_struct[event]['trans_group_index'] += 1
#     return tapn, ts
#
#
# def get_expected_places_transitions_arcs(G):
#     # 3^(conditions + milestones) * 2^((inc+exc)+(resp+no_resp))*2 for each event in relations
#     expected_transitions = 0
#     # 3*no of events
#     expected_places = 4 * len(G['events'])
#     # arcs:
#     #   - events * 12
#     #   - conditions * 9
#     #   - milestones * 8
#     #   - responses * 2
#     #   - noResponses * 2
#     #   - includes * 2
#     #   - exludes * 2
#     expected_arcs = 0
#
#     for event in G['events']:
#         expected_transitions += ((3 ** (len(G['conditionsFor'][event]) if event in G['conditionsFor'] else 0 +
#                                                                                                            len(G[
#                                                                                                                    'milestonesFor'][
#                                                                                                                    event]) if event in
#                                                                                                                               G[
#                                                                                                                                   'milestonesFor'] else 0)) *
#                                  (3 ** ((len(G['includesTo'][event]) if event in G['includesTo'] else 0 +
#                                                                                                       len(G[
#                                                                                                               'excludesTo'][
#                                                                                                               event]) if event in
#                                                                                                                          G[
#                                                                                                                              'excludesTo'] else 0)) *
#                                   (4 ** (len(G['responseTo'][event]) if event in G['responseTo'] else 0 +
#                                                                                                       len(G[
#                                                                                                               'noResponseTo'][
#                                                                                                               event]) if event in
#                                                                                                                          G[
#                                                                                                                              'noResponseTo'] else 0)))) * 4
#
#         expected_arcs += 2 ^ ((3 ^ (len(set(G['includesTo'][event] if event in G['includesTo'] else set()).union(
#             set(G['excludesTo'][event] if event in G['excludesTo'] else set()))))) *
#                               (4 ^ (len(set(G['responseTo'][event] if event in G['responseTo'] else set()).union(
#                                   set(G['noResponseTo'][event] if event in G['noResponseTo'] else set()))))) *
#                               (3 ^ ((len(set(G['conditionsFor'][event])) if event in G['conditionsFor'] else 0))) *
#                               (3 ^ ((len(set(G['milestonesFor'][event])) if event in G['milestonesFor'] else 0))))
#
#     expected_arcs += len(G['events']) * 24
#     return expected_places, expected_transitions, expected_arcs
