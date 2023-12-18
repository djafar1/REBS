from pm4py.objects.dcr.group_subprocess.obj import GroupSubprocessDcrGraph
from pm4py.objects.dcr.obj import Relations


def get_reverse_nesting(graph):
    reverse_nesting = {}
    for k, v in graph.nested_groups_map.items():
        if v not in reverse_nesting:
            reverse_nesting[v] = set()
        reverse_nesting[v].add(k)
    return reverse_nesting


def nested_groups_and_sps_to_flat_dcr(graph: GroupSubprocessDcrGraph):
    graph.nested_groups = {**graph.nested_groups, **graph.subprocesses}
    for group, events in graph.subprocesses.items():
        for e in events:
            graph.nested_groups_map[e] = group
    graph.subprocesses = {}

    if len(graph.nested_groups) == 0:
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
        if event in graph.nested_groups.keys():
            nesting_top[event] = atomic_events

    for nest, atomic_events in nesting_top.items():
        for r in Relations:
            rel = r.value
            if nest in graph[rel]:
                for ae in atomic_events:
                    graph[rel][ae] = graph[rel][nest]
                graph[rel].pop(nest)
            for k, v in graph[rel].items():
                if nest in v:
                    graph[rel][k] = graph[rel][k].union(atomic_events)
                    graph[rel][k].remove(nest)

    graph.events = all_atomic_events
    graph.marking.included = all_atomic_events
    graph.nested_groups = {}
    graph.nested_groups_map = {}
    return graph
