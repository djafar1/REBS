import pandas as pd
import networkx as nx

from pm4py.algo.discovery.dcr_discover.variants import dcr_discover as alg
from pm4py.objects.dcr.obj import Relations


def apply(log, findAdditionalConditions=True, **kwargs):
    event_log = log
    basic_dcr, la = alg.apply(event_log, findAdditionalConditions=findAdditionalConditions)
    me_nestings = get_mutual_exclusions(basic_dcr)

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


def apply_choice(basic_dcr):
    return get_mutual_exclusions(basic_dcr)


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
