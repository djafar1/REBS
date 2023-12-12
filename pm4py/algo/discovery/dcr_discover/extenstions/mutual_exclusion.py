import pm4py
import pandas as pd
import networkx as nx

from copy import deepcopy
from pm4py.algo.discovery.dcr_discover.variants import dcr_discover as alg
from pm4py.objects.dcr.obj import dcr_template, Relations


def apply(log, findAdditionalConditions=True, inBetweenRels=True, **kwargs):
    event_log = log
    basic_dcr, la = alg.apply(event_log, findAdditionalConditions=findAdditionalConditions)
    # get subprocesses based on mutual exclusion
    me_nestings = get_mutual_exclusions(basic_dcr)
    # create a projected log based on the subprocess events
    # subprocess_log = get_abstracted_log(event_log, subprocesses)
    # now run the dcr graph with the subprocess events replaced as the subprocess
    # subprocess_dcr, la = alg.apply(subprocess_log, findAdditionalConditions=findAdditionalConditions)

    # final_dcr = get_final_dcr(basic_dcr, subprocess_dcr, subprocesses, inBetweenRels=inBetweenRels)
    # return final_dcr, subprocess_log
    for name, me_events in me_nestings.items():
        basic_dcr['events'].add(name)
        basic_dcr['marking']['included'].add(name)
        basic_dcr['nestings'][name] = set(me_events)
        for me_event in me_events:
            basic_dcr['nestingsMap'][me_event] = name
            for me_prime in me_events:
                basic_dcr[Relations.E.value][me_event].discard(me_prime)
                basic_dcr[Relations.E.value][me_prime].discard(me_event)
        basic_dcr[Relations.E.value][name] = set([name])

    for name, me_events in me_nestings.items():
        external_events_to_check = basic_dcr['events'].difference(me_events.union(set(name)))
        for r in Relations:
            rel = r.value
            for e in external_events_to_check:
                all_internal_same_relation = True
                for internal_event in me_events:
                    all_internal_same_relation &= internal_event in basic_dcr[rel] and e in basic_dcr[rel][internal_event]
                if all_internal_same_relation:
                    if name not in basic_dcr[rel]:
                        basic_dcr[rel][name] = set()
                    basic_dcr[rel][name].add(e)
                    for internal_event in me_events:
                        basic_dcr[rel][internal_event].remove(e)
            for e in external_events_to_check:
                all_internal_same_relation = True
                for internal_event in me_events:
                    all_internal_same_relation &= e in basic_dcr[rel] and internal_event in basic_dcr[rel][e]
                if all_internal_same_relation:
                    if name not in basic_dcr[rel]:
                        basic_dcr[rel][e] = set()
                    basic_dcr[rel][e].add(name)
                    basic_dcr[rel][e] = basic_dcr[rel][e].difference(me_events)

    return basic_dcr, la

def get_mutual_exclusions(dcr, i=0):
    """
    Get subprocesses based on cliques. Now we naively get the largest clique.
    TODO: Get cliques smartly by taking the cliques that jointly use the highest number of events.
    It should be solved as a search space problem.
    Parameters
    ----------
    dcr
    i

    Returns
    -------

    """

    graph = get_mutually_excluding_graph(dcr)
    cliques = list(frozenset(s) for s in nx.enumerate_all_cliques(graph) if len(s) > 1)
    cliques = sorted(cliques, key=len, reverse=True)
    sps = {}
    used_cliques = {}
    for c in cliques:
        used_cliques[c] = False

    used_events = set()
    for clique in cliques:
        if not used_cliques[clique]:
            if len(clique.intersection(used_events)) == 0:
                # any new mutually exclusive subprocess must be disjoint from all existing ones
                i += 1
                sps[f'Choice{i}'] = clique
                used_cliques[clique] = True
                used_events = used_events.union(clique)
    return sps


def get_mutually_excluding_graph(dcr):
    rel_matrices = {}
    for rel in ['excludesTo']:
        ind = pd.Index(sorted(dcr['events']), dtype=str)
        rel_matrix = pd.DataFrame(0, columns=ind, index=ind, dtype=int)
        for e in dcr['events']:
            for e_prime in dcr['events']:
                if e in dcr[rel] and e_prime in dcr[rel][e]:
                    rel_matrix.at[e, e_prime] = 1
        rel_matrices[rel] = rel_matrix

    self_excluding = set()
    for e in dcr['events']:
        if rel_matrices['excludesTo'].at[e, e] == 1:
            self_excluding.add(e)
    mutually_excluding = []
    for e in self_excluding:
        for e_prime in self_excluding:
            if e != e_prime and \
                    rel_matrices['excludesTo'].at[e, e_prime] == 1 and \
                    rel_matrices['excludesTo'].at[e_prime, e] == 1:
                if (e, e_prime) not in mutually_excluding and (e_prime, e) not in mutually_excluding:
                    mutually_excluding.append((e, e_prime))

    return nx.from_edgelist(mutually_excluding)


def get_abstracted_log(event_log, mutual_exclusions):
    subprocess_log = pm4py.objects.log.obj.EventLog()
    trace: pm4py.objects.log.obj.Trace
    event: pm4py.objects.log.obj.Event
    for trace in event_log:
        sp_trace = pm4py.objects.log.obj.Trace(attributes=trace.attributes, properties=trace.properties)
        for event in trace:
            sp_event = None
            for name, sp in mutual_exclusions.items():
                if event['concept:name'] in sp:
                    # if the event is in the subprocess then replace it with the subprocess name
                    event['concept:name'] = name
                    sp_event = event
            if not sp_event:
                sp_event = event
            sp_trace.append(sp_event)
        subprocess_log.append(sp_trace)
    return subprocess_log


def get_final_dcr(basic_dcr, n_dcr, nestings, inBetweenRels=True):
    final_dcr = deepcopy(dcr_template)
    for k in n_dcr.keys():
        if k in basic_dcr.keys():
            match k:
                case 'events':
                    final_dcr[k] = n_dcr[k].union(basic_dcr[k])
                case 'marking':
                    final_dcr[k]['executed'] = n_dcr[k]['executed'].union(basic_dcr[k]['executed'])
                    final_dcr[k]['included'] = n_dcr[k]['included'].union(basic_dcr[k]['included'])
                    final_dcr[k]['pending'] = n_dcr[k]['pending'].union(basic_dcr[k]['pending'])
                case 'conditionsFor' | 'responseTo' | 'includesTo' | 'excludesTo':
                    # comment this if debugging the i2e and e2i relations
                    final_dcr[k] = deepcopy(n_dcr[k])
                    # in between the internal to external and external to internal
                    if inBetweenRels:
                        event_subprocesses = {}
                        for m, n in nestings.items():
                            for l in n:
                                event_subprocesses[l] = m
                        for sp_name, internal_events in nestings.items():
                            external_events = basic_dcr['events'].difference(internal_events)
                            for external_event in external_events:
                                if external_event in basic_dcr[k] and external_event in n_dcr[k]:
                                    e2i = basic_dcr[k][external_event].intersection(internal_events)
                                    # TODO: if e2i has internal events of another subprocess and that subprocess has the same relation to the subprocess then we remove that external event from e2i
                                    e2i_to_remove = set()
                                    for e in e2i:
                                        if e in event_subprocesses.keys() and event_subprocesses[e] in n_dcr[k]:
                                            e2i_to_remove.add(e)
                                    e2i = e2i.difference(e2i_to_remove)
                                    e2_sp = n_dcr[k][external_event].intersection({sp_name})
                                    if len(e2_sp) == 0 and len(e2i) > 0:
                                        # print(f'{k} {external_event}')
                                        # print(e2i)
                                        if external_event not in final_dcr[k]:
                                            final_dcr[k][external_event] = set()
                                        final_dcr[k][external_event] = final_dcr[k][external_event].union(e2i)
                            # print('i2e')
                            for internal_event in internal_events:
                                if internal_event in basic_dcr[k] and sp_name in n_dcr[k]:
                                    i2e = basic_dcr[k][internal_event].intersection(external_events)
                                    # TODO: if i2e has internal events of another subprocess and that subprocess has the same relation to the subprocess then we remove that external event from i2e
                                    i2e_to_remove = set()
                                    for e in i2e:
                                        if e in event_subprocesses.keys() and event_subprocesses[e] in n_dcr[k]:
                                            i2e_to_remove.add(e)
                                    i2e = i2e.difference(i2e_to_remove)
                                    sp2e = n_dcr[k][sp_name].intersection(external_events)
                                    i2e_not_sp2e = i2e.difference(sp2e)
                                    if len(i2e_not_sp2e) > 0:
                                        if internal_event not in final_dcr[k]:
                                            final_dcr[k][internal_event] = set()
                                        final_dcr[k][internal_event] = final_dcr[k][internal_event].union(i2e_not_sp2e)

    for name, sp_events in nestings.items():
        final_dcr['nestings'][name] = set(sp_events)
        for spe in sp_events:
            final_dcr['nestingsMap'][spe] = name
    return final_dcr
