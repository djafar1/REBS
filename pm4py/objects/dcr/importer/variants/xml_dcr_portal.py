import copy

import isodate

from pm4py.util import constants
from copy import deepcopy
from pm4py.objects.dcr.obj import Relations, dcr_template, DcrGraph
from pm4py.objects.dcr.roles.obj import RoleDcrGraph
from pm4py.objects.dcr.group_subprocess.obj import GroupSubprocessDcrGraph
from pm4py.objects.dcr.milestone_noresponse.obj import MilestoneNoResponseDcrGraph
from pm4py.objects.dcr.timed.obj import TimedDcrGraph

I = Relations.I.value
E = Relations.E.value
R = Relations.R.value
N = Relations.N.value
C = Relations.C.value
M = Relations.M.value


def parse_element(curr_el, parent, dcr):
    # Create the DCR graph
    tag = curr_el.tag.lower()
    match tag:
        case 'event':
            id = curr_el.get('id')
            if id:
                dcr['events'].add(id)
                event_type = curr_el.get('type')
                match event_type:
                    case 'subprocess':
                        dcr['subprocesses'][id] = set()
                    case 'nesting':
                        dcr['nestings'][id] = set()
                        pass
                    case _:
                        pass
                match parent.get('type'):
                    case 'subprocess':
                        dcr['subprocesses'][parent.get('id')].add(id)
                    case 'nesting':
                        dcr['nestings'][parent.get('id')].add(id)
                        pass
                    case _:
                        pass
                match parent.tag:
                    case 'included' | 'executed':
                        dcr['marking'][parent.tag].add(id)
                    case 'pendingResponses':
                        dcr['marking']['pending'].add(id)
                    case _:
                        pass
                for role in curr_el.findall('.//role'):
                    if role.text:
                        if role.text not in dcr['roleAssignments']:
                            dcr['roleAssignments'][role.text] = set([id])
                        else:
                            dcr['roleAssignments'][role.text].add(id)
                for role in curr_el.findall('.//readRole'):
                    if role.text:
                        if role.text not in dcr['readRoleAssignments']:
                            dcr['readRoleAssignments'][role.text] = set([id])
                        else:
                            dcr['readRoleAssignments'][role.text].add(id)
        case 'label':
            id = curr_el.get('id')
            dcr['labels'].add(id)
        case 'labelmapping':
            eventId = curr_el.get('eventId')
            labelId = curr_el.get('labelId')
            if eventId not in dcr['labelMapping']:
                dcr['labelMapping'][eventId] = labelId
        case 'condition':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            delay = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr['conditionsFor'].__contains__(event_prime):
                dcr['conditionsFor'][event_prime] = set()
            dcr['conditionsFor'][event_prime].add(event)

            if delay:
                if not dcr['conditionsForDelays'].__contains__(event_prime):
                    dcr['conditionsForDelays'][event_prime] = {}
                if delay.isdecimal():
                    delay_days = int(delay)
                else:
                    delay_days = isodate.parse_duration(delay).days
                dcr['conditionsForDelays'][event_prime][event] = delay_days

        case 'response':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            deadline = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr['responseTo'].__contains__(event):
                dcr['responseTo'][event] = set()
            dcr['responseTo'][event].add(event_prime)

            if deadline:
                if not dcr['responseToDeadlines'].__contains__(event):
                    dcr['responseToDeadlines'][event] = {}
                if deadline.isdecimal():
                    deadline_days = int(deadline)
                else:
                    deadline_days = isodate.parse_duration(deadline).days
                dcr['responseToDeadlines'][event][event_prime] = deadline_days
        case 'role':
            if curr_el.text:
                dcr['roles'].add(curr_el.text)
                if curr_el.text not in dcr['roleAssignments']:
                    dcr['roleAssignments'][curr_el.text] = set()
                if curr_el.text not in dcr['readRoleAssignments']:
                    dcr['readRoleAssignments'][curr_el.text] = set()
        case 'include' | 'exclude':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            deadline = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr[f'{tag}sTo'].__contains__(event):
                dcr[f'{tag}sTo'][event] = set()
            dcr[f'{tag}sTo'][event].add(event_prime)
        case 'coresponse' | 'noresponse':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            deadline = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr[f'noResponseTo'].__contains__(event):
                dcr[f'noResponseTo'][event] = set()
            dcr[f'noResponseTo'][event].add(event_prime)
        case 'milestone':
            event = curr_el.get('sourceId')
            event_prime = curr_el.get('targetId')
            filter_level = curr_el.get('filterLevel')
            iso_description = curr_el.get('description')  # might have an ISO format duration
            description = None
            if iso_description:
                description = iso_description.strip()  # might have an ISO format duration
            deadline = curr_el.get('time')
            groups = curr_el.get('groups')
            if not dcr[f'{tag}sFor'].__contains__(event_prime):
                dcr[f'{tag}sFor'][event_prime] = set()
            dcr[f'{tag}sFor'][event_prime].add(event)
        case _:
            pass
    for child in curr_el:
        dcr = parse_element(child, curr_el, dcr)

    return dcr


def import_xml_tree_from_root(root, white_space_replacement='', as_dcr_object=False, labels_as_ids=True):
    dcr = copy.deepcopy(dcr_template)
    dcr = parse_element(root, None, dcr)
    dcr = clean_input(dcr, white_space_replacement=white_space_replacement)

    if labels_as_ids:
        dcr = map_labels_to_ids(dcr)
    '''
    Transform the dictionary into a DCR_Graph object
    '''
    if as_dcr_object:
        if len(dcr['conditionsForDelays']) > 0 or len(dcr['responseToDeadlines']) > 0:
            return TimedDcrGraph(dcr)
        elif len(dcr['subprocesses']) > 0 or len(dcr['nestings']) > 0:
            return GroupSubprocessDcrGraph(dcr)
        elif len(dcr['roles']) > 0:
            return RoleDcrGraph(dcr)
        else:
            return DcrGraph(dcr)
    else:
        return dcr


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


def apply(path, parameters = None):
    '''
    Reads a DCR graph from an XML file

    Parameters
    ----------
    path
        Path to the XML file

    Returns
    -------
    dcr
        DCR graph object
    '''
    if parameters is None:
        parameters = {}

    from lxml import etree, objectify

    parser = etree.XMLParser(remove_comments=True)
    xml_tree = objectify.parse(path, parser=parser)

    return import_xml_tree_from_root(xml_tree.getroot(), **parameters)


def import_from_string(dcr_string, parameters=None):
    if parameters is None:
        parameters = {}

    if type(dcr_string) is str:
        dcr_string = dcr_string.encode(constants.DEFAULT_ENCODING)

    from lxml import etree, objectify

    parser = etree.XMLParser(remove_comments=True)
    root = objectify.fromstring(dcr_string, parser=parser)

    return import_xml_tree_from_root(root)
