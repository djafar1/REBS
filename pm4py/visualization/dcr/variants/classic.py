import tempfile

import graphviz
from graphviz import Digraph

filename = tempfile.NamedTemporaryFile(suffix=".gv")
filename.close()

viz = Digraph("", filename=filename.name, engine='dot', graph_attr={'bgcolor': 'white', 'rankdir': 'LR'},
              node_attr={'shape': 'Mrecord'}, edge_attr={'arrowsize': '0.5'})


def create_edge(source, target, relation):
    viz.edge_attr['labeldistance'] = '0.0'
    match relation:
        case 'condition':
            viz.edge(source, target, color='#FFA500', arrowhead='dotnormal')
        case 'exclude':
            viz.edge(source, target, color='#FC0C1B', arrowhead='normal', arrowtail='none', headlabel='%', labelfontcolor='#FC0C1B', labelfontsize='8')
        case 'include':
            viz.edge(source, target, color='#30A627', arrowhead='normal', arrowtail='none', headlabel='+', labelfontcolor='#30A627', labelfontsize='10')
        case 'response':
            viz.edge(source, target, color='#2993FC', arrowhead='normal', arrowtail='dot', dir='both')
    return


def apply(dcr):
    for event in dcr['events']:
        if event not in dcr['marking']['included']:
            viz.node(event, ' | ' + dcr['labelMap'][event], style='dashed')
        else:
            viz.node(event, ' | ' + dcr['labelMap'][event], style='solid')

        for event_prime in dcr['events']:
            if event_prime in dcr['conditionsFor'] and event in dcr['conditionsFor'][event_prime]:
                create_edge(event, event_prime, 'condition')
            if event in dcr['responseTo'] and event_prime in dcr['responseTo'][event]:
                create_edge(event, event_prime, 'response')
            if event in dcr['includesTo'] and event_prime in dcr['includesTo'][event]:
                create_edge(event, event_prime, 'include')
            if event in dcr['excludesTo'] and event_prime in dcr['excludesTo'][event]:
                create_edge(event, event_prime, 'exclude')

    viz.view()

    return
