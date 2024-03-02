from pm4py.objects.dcr.obj import Relations, dcr_template
from copy import deepcopy

I = Relations.I.value
E = Relations.E.value
R = Relations.R.value
N = Relations.N.value
C = Relations.C.value
M = Relations.M.value


def clean_input(dcr, white_space_replacement=None):
    if white_space_replacement is None:
        white_space_replacement = ' '
    # remove all space characters and put conditions and milestones in the correct order (according to the actual arrows)
    for k, v in deepcopy(dcr).items():
        if k in [I, E, C, R, M, N]:
            v_new = {}
            for k2, v2 in v.items():
                v_new[k2.strip().replace(' ', white_space_replacement)] = set(
                    [v3.strip().replace(' ', white_space_replacement) for v3 in v2])
            dcr[k] = v_new
        elif k in ['conditionsForDelays', 'responseToDeadlines']:
            v_new = {}
            for k2, v2 in v.items():
                v_new[k2.strip().replace(' ', white_space_replacement)] = {
                    v3.strip().replace(' ', white_space_replacement): d for v3, d in v2.items()}
            dcr[k] = v_new
        elif k == 'marking':
            for k2 in ['executed', 'included', 'pending']:
                new_v = set([v2.strip().replace(' ', white_space_replacement) for v2 in dcr[k][k2]])
                dcr[k][k2] = new_v
        elif k in ['subprocesses', 'nestings', 'roleAssignments', 'readRoleAssignments']:
            v_new = {}
            for k2, v2 in v.items():
                v_new[k2.strip().replace(' ', white_space_replacement)] = set(
                    [v3.strip().replace(' ', white_space_replacement) for v3 in v2])
            dcr[k] = v_new
        elif k in ['labelMapping']:
            v_new = {}
            for k2, v2 in v.items():
                v_new[k2.strip().replace(' ', white_space_replacement)] = v2.strip().replace(' ', white_space_replacement)
            dcr[k] = v_new
        else:
            new_v = set([v2.strip().replace(' ', white_space_replacement) for v2 in dcr[k]])
            dcr[k] = new_v
    return dcr


def map_labels_to_ids(dcr):
    id_to_label = dcr['labelMapping']
    dcr_res = deepcopy(dcr_template)
    for k, v in dcr.items():
        if k in id_to_label:
            k = id_to_label[k]
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if k2 in id_to_label:
                    k2 = id_to_label[k2]
                if isinstance(v2, dict):
                    for k22, v22 in v2.items():
                        if k22 in id_to_label:
                            k22 = id_to_label[k22]
                        if isinstance(v22, dict):
                            for k3, v3 in v22.items():
                                if k3 in id_to_label:
                                    k3 = id_to_label[k3]
                                dcr_res[k][k2][k3] = v3
                        elif k in ['conditionsForDelays', 'responseToDeadlines']:
                            dcr_res[k][k2] = {id_to_label[i0]: i1 for i0, i1 in v2.items()}
                        else:
                            dcr_res[k][k2][k22] = set([id_to_label[i] for i in v22])

                elif k not in ['labelMapping']:
                    dcr_res[k][k2] = set([id_to_label[i] for i in v2])

        else:
            if k not in ['labels', 'roles']:
                dcr_res[k] = set([id_to_label[i] for i in v])
    return dcr_res


def get_reverse_nesting(graph):
    reverse_nesting = {}
    for k, v in graph.nestedgroupsmap.items():
        if v not in reverse_nesting:
            reverse_nesting[v] = set()
        reverse_nesting[v].add(k)
    return reverse_nesting


def nested_groups_and_sps_to_flat_dcr(graph):
    graph.nestedgroups = {**graph.nestedgroups, **graph.subprocesses}
    for group, events in graph.subprocesses.items():
        for e in events:
            graph.nestedgroupsmap[e] = group
    graph.subprocesses = {}

    if len(graph.nestedgroups) == 0:
        return

    reverse_nesting = get_reverse_nesting(graph)
    all_atomic_events = set()
    nesting_top = {}
    for event in graph.events:
        atomic_events = set()

        def find_lowest(e):
            if e in reverse_nesting:
                for nested_event in reverse_nesting[e]:
                    if nested_event in reverse_nesting:
                        find_lowest(nested_event)
                    else:
                        atomic_events.add(nested_event)
            else:
                atomic_events.add(e)

        find_lowest(event)
        all_atomic_events = all_atomic_events.union(atomic_events)
        if event in graph.nestedgroups.keys():
            nesting_top[event] = atomic_events

    for nest, atomic_events in nesting_top.items():
        for r in Relations:
            rel = r.value
            if nest in graph[rel]:
                for ae in atomic_events:
                    if ae not in graph[rel]:
                        graph[rel][ae] = set()
                    graph[rel][ae] = graph[rel][ae].union(graph[rel][nest])
                graph[rel].pop(nest)
            for k, v in graph[rel].items():
                if nest in v:
                    graph[rel][k] = graph[rel][k].union(atomic_events)
                    graph[rel][k].remove(nest)
        for rel in ['timedconditions', 'timedresponses']:
            if nest in graph[rel]:
                for ae in atomic_events:
                    graph[rel][ae] = {**graph[rel][ae], **graph[rel][nest]}
                graph[rel].pop(nest)
            for k, v in graph[rel].items():
                for kv0, vv0 in v.items():
                    if nest == kv0:
                        for ae in atomic_events:
                            graph[rel][k][ae] = vv0
                        graph[rel][k].pop(nest)

    graph.events = all_atomic_events
    graph.marking.included = graph.marking.included.intersection(all_atomic_events)
    graph.nestedgroups = {}
    graph.nestedgroupsmap = {}
    return graph.obj_to_template()
