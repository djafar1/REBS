import tempfile
from enum import Enum

import graphviz
from graphviz import Digraph
from pm4py.util import exec_utils, constants

filename = tempfile.NamedTemporaryFile(suffix=".gv")
filename.close()

class Parameters(Enum):
    FORMAT = "format"
    RANKDIR = "set_rankdir"
    AGGREGATION_MEASURE = "aggregationMeasure"
    FONT_SIZE = "font_size"
    BGCOLOR = "bgcolor"
    DECORATIONS = "decorations"


def create_edge(source, target, relation, viz):
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


def apply(dcr, parameters):
    if parameters is None:
        parameters = {}

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    set_rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, 'LR')
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, "12")
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)

    viz = Digraph("", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor, 'rankdir': set_rankdir},
                  node_attr={'shape': 'Mrecord'}, edge_attr={'arrowsize': '0.5'})

    for event in dcr['events']:
        if event not in dcr['marking']['included']:
            viz.node(event, ' | ' + dcr['labelMap'][event], style='dashed',font_size=font_size)
        else:
            viz.node(event, ' | ' + dcr['labelMap'][event], style='solid',font_size=font_size)

    for event_prime in dcr['conditionsFor']:
        for event in dcr['conditionsFor'][event_prime]:
            create_edge(event, event_prime, 'condition', viz)
    for event in dcr['responseTo']:
        for event_prime in dcr['responseTo'][event]:
            create_edge(event, event_prime, 'response', viz)
    for event in dcr['includesTo']:
        for event_prime in dcr['includesTo'][event]:
            create_edge(event, event_prime, 'include', viz)
    for event in dcr['excludesTo']:
        for event_prime in dcr['excludesTo'][event]:
            create_edge(event, event_prime, 'exclude', viz)

    viz.attr(overlap='false')

    viz.format = image_format.replace("html", "plain-text")

    return viz
