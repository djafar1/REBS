from pm4py.objects.dcr.obj import Relations


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
