import os

import numpy as np

from pm4py.objects.petri_net.obj import *
from pm4py.objects.petri_net.utils import petri_utils as pn_utils
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter

from pm4py.objects.conversion.dcr.variants.to_timed_arc_petri_net_submodules import (timed_exceptional_cases,
                                                                                     timed_single_relations,
                                                                                     timed_preoptimizer,
                                                                                     timed_utils)


class Dcr2TimedArcPetri(object):

    def __init__(self, preoptimize=True, postoptimize=True, map_unexecutable_events=False, debug=False) -> None:
        self.in_t_types = ['event', 'init', 'initpend', 'pend']
        self.helper_struct = {}
        self.preoptimize = preoptimize
        self.postoptimize = postoptimize
        self.map_unexecutable_events = map_unexecutable_events
        self.preoptimizer = timed_preoptimizer.TimedPreoptimizer()
        self.transitions = {}
        self.helper_struct['pend_matrix'] = {}
        self.helper_struct['pend_exc_matrix'] = {}
        self.mapping_exceptions = None
        self.reachability_timeout = None
        self.print_steps = debug
        self.debug = debug

    def initialize_helper_struct(self, G) -> None:
        self.helper_struct['transport_index'] = 0
        for event in G['events']:
            self.helper_struct[event] = {}
            self.helper_struct[event]['places'] = {}
            self.helper_struct[event]['places']['included'] = None
            self.helper_struct[event]['places']['pending'] = set()
            self.helper_struct[event]['places']['pending_excluded'] = set()
            self.helper_struct[event]['places']['executed'] = None
            self.helper_struct[event]['transitions'] = []
            self.helper_struct[event]['t_types'] = self.in_t_types
            self.helper_struct[event]['pending_pairs'] = {}
            self.helper_struct[event]['trans_group_index'] = 0

            self.transitions[event] = {}
            self.helper_struct['pend_matrix'][event] = {}
            self.helper_struct['pend_exc_matrix'][event] = {}
            for event_prime in G['events']:
                self.transitions[event][event_prime] = []
                self.helper_struct['pend_matrix'][event][event_prime] = None
                self.helper_struct['pend_exc_matrix'][event][event_prime] = None

    def create_event_pattern_places(self, event, G, tapn, m) -> (PetriNet, Marking):
        default_make_included = True
        default_make_pend = True
        default_make_pend_ex = True
        default_make_exec = True
        if self.preoptimize:
            default_make_included = event in self.preoptimizer.need_included_place
            default_make_pend = event in self.preoptimizer.need_pending_place
            default_make_pend_ex = event in self.preoptimizer.need_pending_excluded_place
            default_make_exec = event in self.preoptimizer.need_executed_place

        if default_make_included:
            inc_place = PetriNet.Place(f'included_{event}')
            tapn.places.add(inc_place)
            self.helper_struct[event]['places']['included'] = inc_place
            # fill the marking
            if event in G['marking']['included']:
                m[inc_place] = 1

        if default_make_pend:
            if event in G['marking']['pendingDeadline']:
                init_pend_place = PetriNet.Place(f'init_pending_{event}')
                init_pend_place.properties['ageinvariant'] = G['marking']['pendingDeadline'][event]
                tapn.places.add(init_pend_place)
                self.helper_struct[event]['places']['pending'].add((init_pend_place, event))
                self.helper_struct['pend_matrix'][event][event] = init_pend_place
                self.helper_struct[event]['pending_pairs'][event] = init_pend_place
                if event in G['marking']['pending'] and event in G['marking']['included']:
                    m[init_pend_place] = 1

        if default_make_pend_ex:
            if event in G['marking']['pendingDeadline']:
                init_pend_excl_place = PetriNet.Place(f'init_pending_excluded_{event}')
                tapn.places.add(init_pend_excl_place)
                self.helper_struct[event]['places']['pending_excluded'].add((init_pend_excl_place, event))
                self.helper_struct['pend_exc_matrix'][event][event] = init_pend_excl_place
                self.helper_struct[event]['pending_pairs'][event] = (
                    self.helper_struct[event]['pending_pairs'][event], init_pend_excl_place)
                if event in G['marking']['pending'] and event not in G['marking']['included']:
                    m[init_pend_excl_place] = 1

        e_prime_pending_by_e = {}
        for k, v1 in G['responseTo'].items():
            for v in v1:
                if v not in e_prime_pending_by_e:
                    e_prime_pending_by_e[v] = set()
                e_prime_pending_by_e[v].add(k)
        if event in e_prime_pending_by_e:
            if default_make_pend:
                for event_prime in e_prime_pending_by_e[event]:
                    pend_by_place = PetriNet.Place(f'pending_{event}_by_{event_prime}')
                    pend_by_place.properties['ageinvariant'] = G['responseToDeadlines'][event_prime][event]
                    tapn.places.add(pend_by_place)
                    self.helper_struct[event]['places']['pending'].add((pend_by_place, event_prime))
                    self.helper_struct['pend_matrix'][event][event_prime] = pend_by_place
                    self.helper_struct[event]['pending_pairs'][event_prime] = pend_by_place

            if default_make_pend_ex:
                for event_prime in e_prime_pending_by_e[event]:
                    pend_excl_by_place = PetriNet.Place(f'pending_excluded_{event}_by_{event_prime}')
                    tapn.places.add(pend_excl_by_place)
                    self.helper_struct[event]['places']['pending_excluded'].add((pend_excl_by_place, event_prime))
                    self.helper_struct['pend_exc_matrix'][event][event_prime] = pend_excl_by_place
                    self.helper_struct[event]['pending_pairs'][event_prime] = (self.helper_struct[event]['pending_pairs'][event_prime], pend_excl_by_place)
        else:
            if default_make_pend:
                pend_place = PetriNet.Place(f'pending_{event}')
                tapn.places.add(pend_place)
                self.helper_struct[event]['places']['pending'] = set([(pend_place,'')])
                # fill the marking
                if event in G['marking']['pending'] and event in G['marking']['included']:
                    m[pend_place] = 1

            if default_make_pend_ex:
                pend_excl_place = PetriNet.Place(f'pending_excluded_{event}')
                tapn.places.add(pend_excl_place)
                self.helper_struct[event]['places']['pending_excluded'] = set([(pend_excl_place,'')])
                # fill the marking
                if event in G['marking']['pending'] and not event in G['marking']['included']:
                    m[pend_excl_place] = 1

        if default_make_exec:
            exec_place = PetriNet.Place(f'executed_{event}')
            tapn.places.add(exec_place)
            self.helper_struct[event]['places']['executed'] = exec_place
            # fill the marking
            if event in G['marking']['executed']:
                m[exec_place] = 1
        if self.preoptimize:
            ts = ['event']
            if default_make_exec and not event in G['marking']['executed'] and not event in self.preoptimizer.no_init_t:
                ts.append('init')
            if default_make_exec and default_make_pend and not event in self.preoptimizer.no_initpend_t:
                ts.append('initpend')
            if default_make_pend:
                ts.append('pend')
            self.helper_struct[event]['t_types'] = ts

        return tapn, m

    def create_event_pattern(self, event, G, tapn, m) -> (PetriNet, Marking):
        tapn, m = self.create_event_pattern_places(event, G, tapn, m)

        tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct,
                                                                         self.mapping_exceptions)
        self.helper_struct[event]['transitions'].extend(ts)
        return tapn, m

    def post_optimize_petri_net_reachability_graph(self, tapn, m, G=None) -> PetriNet:
        from pm4py.objects.petri_net.utils import reachability_graph
        # from pm4py.visualization.transition_system import visualizer as ts_visualizer
        from pm4py.objects.petri_net.transport_invariant import semantics as tapn_semantics
        max_elab_time = 2 * 60 * 60  # 2 hours
        if self.reachability_timeout:
            max_elab_time = self.reachability_timeout
        trans_sys = reachability_graph.construct_reachability_graph(tapn, m, use_trans_name=True,
                                                                    parameters={
                                                                        'petri_semantics': tapn_semantics.TransportInvariantSemantics(),
                                                                        'max_elab_time': max_elab_time})

        fired_transitions = set()

        for transition in trans_sys.transitions:
            fired_transitions.add(transition.name)

        ts_to_remove = set()
        for t in tapn.transitions:
            if t.name not in fired_transitions:
                ts_to_remove.add(t)
        for t in ts_to_remove:
            tapn = pn_utils.remove_transition(tapn, t)

        changed_places = set()
        for state_list in trans_sys.states:
            for state in state_list.name:
                changed_places.add(state)

        parallel_places = set()
        places_to_rename = {}
        ps_to_remove = tapn.places.difference(changed_places)
        if G:
            for event in G['events']:
                for type, event_place in self.helper_struct[event]['places'].items():
                    for type_prime, event_place_prime in self.helper_struct[event]['places'].items():
                        # TODO: if type is (pending or pending_excluded) then event_place is a set
                        # if type_prime is (pending or pending_excluded) then event_place_prime is a set
                        if type in ['pending', 'pending_excluded'] and type_prime in ['pending', 'pending_excluded']:
                            for ep,_ in event_place:
                                for epp,_ in event_place_prime:
                                    self.post_optimize_parallel_places(ep, epp, parallel_places, places_to_rename, type_prime, m)
                        elif type in ['pending', 'pending_excluded']:
                            for ep,_ in event_place:
                                self.post_optimize_parallel_places(ep, event_place_prime, parallel_places, places_to_rename, type_prime, m)
                        elif type_prime in ['pending', 'pending_excluded']:
                            for epp,_ in event_place_prime:
                                self.post_optimize_parallel_places(event_place, epp, parallel_places, places_to_rename, type_prime, m)
                        else:
                            self.post_optimize_parallel_places(event_place, event_place_prime, parallel_places, places_to_rename, type_prime, m)

        ps_to_remove = ps_to_remove.union(parallel_places)
        for p in ps_to_remove:
            tapn = pn_utils.remove_place(tapn, p)

        for p, name in places_to_rename.items():
            p.name = name

        return tapn

    @staticmethod
    def post_optimize_parallel_places(event_place, event_place_prime, parallel_places, places_to_rename, type_prime, m):
        if event_place and event_place_prime and event_place.name != event_place_prime.name and event_place not in parallel_places:
            is_parallel = False
            ep_ins = event_place.in_arcs
            epp_ins = event_place_prime.in_arcs
            ep_outs = event_place.out_arcs
            epp_outs = event_place_prime.out_arcs
            if len(ep_ins) == len(epp_ins) and len(ep_outs) == len(epp_outs):
                ep_sources = set()
                epp_sources = set()
                for ep_in in ep_ins:
                    ep_sources.add(ep_in.source)
                for epp_in in epp_ins:
                    epp_sources.add(epp_in.source)
                ep_targets = set()
                epp_targets = set()
                for ep_out in ep_outs:
                    ep_targets.add(ep_out.target)
                for epp_out in epp_outs:
                    epp_targets.add(epp_out.target)
                if ep_sources == epp_sources and ep_targets == epp_targets:
                    is_parallel = True
            if is_parallel and m[event_place] == m[event_place_prime]:
                parallel_places.add(event_place_prime)
                places_to_rename[event_place] = f'{type_prime}_{event_place.name}'

    def export_debug_net(self, tapn, m, path, step, pn_export_format):
        path_without_extension, extens = os.path.splitext(path)
        debug_save_path = f'{path_without_extension}_{step}{extens}'
        pnml_exporter.apply(tapn, m, debug_save_path, variant=pn_export_format, parameters={'isTimed': self.timed})

    def dcr2tapn(self, G, tapn_path) -> (PetriNet, Marking):
        self.basic = False  # True (basic) = inc,ex,resp,cond | False = basic + no-resp,mil
        self.timed = True  # False = untimed | True = timed cond (delay) and resp (deadline)
        self.transport_idx = 0
        self.initialize_helper_struct(G)
        self.mapping_exceptions = timed_exceptional_cases.TimedExceptionalCases(self.helper_struct)
        self.preoptimizer = timed_preoptimizer.TimedPreoptimizer()
        induction_step = 0
        pn_export_format = pnml_exporter.TAPN
        if tapn_path.endswith("pnml"):
            pn_export_format = pnml_exporter.PNML

        tapn = PetriNet("Dcr2Tapn")
        m = Marking()
        # pre-optimize mapping based on DCR graph behaviour
        if self.preoptimize:
            if self.print_steps:
                print('[i] preoptimizing')
            self.preoptimizer.pre_optimize_based_on_dcr_behaviour(G)
            if not self.map_unexecutable_events:
                G = self.preoptimizer.remove_un_executable_events_from_dcr(G)

        # including the handling of exception cases from the induction step
        G = self.mapping_exceptions.filter_exceptional_cases(G)
        if self.preoptimize:
            if self.print_steps:
                print('[i] finding exceptional behaviour')
            self.preoptimizer.preoptimize_based_on_exceptional_cases(G, self.mapping_exceptions)

        # map events
        if self.print_steps:
            print('[i] mapping events')
        for event in G['events']:
            tapn, m = self.create_event_pattern(event, G, tapn, m)
        if self.debug:
            self.export_debug_net(tapn, m, tapn_path, f'{induction_step}event', pn_export_format)
            induction_step += 1
        # all self exceptions have been mapped at this point

        sr = timed_single_relations.TimedSingleRelations(self.helper_struct, self.mapping_exceptions)
        # map constraining relations
        if self.print_steps:
            print('[i] map constraining relations')
        for event in G['conditionsFor']:
            for event_prime in G['conditionsFor'][event]:
                delay = None
                if event in G['conditionsForDelays'] and event_prime in G['conditionsForDelays'][event]:
                    delay = G['conditionsForDelays'][event][event_prime]
                tapn = sr.create_condition_pattern(event, event_prime, tapn, delay=delay)
                if self.debug:
                    self.export_debug_net(tapn, m, tapn_path, f'{induction_step}conditionsFor', pn_export_format)
                    induction_step += 1
        if not self.basic:
            for event in G['milestonesFor']:
                for event_prime in G['milestonesFor'][event]:
                    tapn = sr.create_milestone_pattern(event, event_prime, tapn)
                    if self.debug:
                        self.export_debug_net(tapn, m, tapn_path, f'{induction_step}milestonesFor', pn_export_format)
                        induction_step += 1

        # map effect relations
        if self.print_steps:
            print('[i] map effect relations')
        for event in G['includesTo']:
            for event_prime in G['includesTo'][event]:
                tapn = sr.create_include_pattern(event, event_prime, tapn)
                if self.debug:
                    self.export_debug_net(tapn, m, tapn_path, f'{induction_step}includesTo', pn_export_format)
                    induction_step += 1
        for event in G['excludesTo']:
            for event_prime in G['excludesTo'][event]:
                tapn = sr.create_exclude_pattern(event, event_prime, tapn)
                if self.debug:
                    self.export_debug_net(tapn, m, tapn_path, f'{induction_step}excludesTo', pn_export_format)
                    induction_step += 1
        for event in G['responseTo']:
            for event_prime in G['responseTo'][event]:
                tapn = sr.create_response_pattern(event, event_prime, tapn)
                if self.debug:
                    self.export_debug_net(tapn, m, tapn_path, f'{induction_step}responseTo', pn_export_format)
                    induction_step += 1
        if not self.basic:
            for event in G['noResponseTo']:
                for event_prime in G['noResponseTo'][event]:
                    tapn = sr.create_no_response_pattern(event, event_prime, tapn)
                    if self.debug:
                        self.export_debug_net(tapn, m, tapn_path, f'{induction_step}noResponseTo', pn_export_format)
                        induction_step += 1

        # handle all relation exceptions
        if self.print_steps:
            print('[i] handle all relation exceptions')
        tapn = self.mapping_exceptions.map_exceptional_cases_between_events(tapn, m)

        # post-optimize based on the petri net reachability graph
        if self.postoptimize:
            if self.print_steps:
                print('[i] post optimizing')
            tapn = self.post_optimize_petri_net_reachability_graph(tapn, m, G)

        if self.print_steps:
            print(f'[i] export to {tapn_path}')

        pnml_exporter.apply(tapn, m, tapn_path, variant=pn_export_format, parameters={'isTimed': self.timed})

        return tapn, m


def run_specific_dcr():
    '''
    here you can write your own graph and run it
    '''
    dcr = {
        'events': {'B'},
        'conditionsFor': {},
        'milestonesFor': {},
        'responseTo': {},
        'noResponseTo': {},
        'includesTo': {},
        'excludesTo': {},
        'conditionsForDelays': {},
        'responseToDeadlines': {},
        'marking': {'executed': set(),
                    'included': {'B'},
                    'pending': {'B'},
                    'pendingDeadline': {'B': 10}
                    }
    }

    d2p = Dcr2TimedArcPetri(preoptimize=True, postoptimize=True, map_unexecutable_events=False)
    print('[i] dcr')
    tapn, m = d2p.dcr2tapn(dcr, tapn_path="/home/vco/Projects/pm4py-dcr/models/one_petri_timed.tapn")


if __name__ == "__main__":
    run_specific_dcr()
