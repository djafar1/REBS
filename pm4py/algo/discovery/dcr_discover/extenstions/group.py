from pm4py.objects.dcr.obj import Relations, dcr_template
from pm4py.algo.discovery.dcr_discover.variants import dcr_discover as alg

from copy import deepcopy


def apply(log, findAdditionalConditions=True, **kwargs):
    event_log = deepcopy(log)
    basic_dcr, la = alg.apply(event_log, findAdditionalConditions=findAdditionalConditions)
    nested_dcr = apply_group(basic_dcr)
    return nested_dcr, log


def apply_group(basic_dcr):
    nesting = Nesting()
    nesting.create_encoding(basic_dcr)
    nesting.nest(basic_dcr['events'])
    nesting.remove_redundant_nestings()
    nested_dcr = nesting.get_nested_dcr_graph()
    return nested_dcr


def encode(G):
    enc = {}
    for e in G['events']:
        enc[e] = set()
    for e in G['events']:
        for e_prime in G['events']:
            for rel in Relations:
                if e in G[rel.value] and e_prime in G[rel.value][e]:
                    if rel in [Relations.C, Relations.M]:
                        enc[e].add((e_prime, rel.value, 'in'))
                    else:
                        enc[e].add((e_prime, rel.value, 'out'))
                if e_prime in G[rel.value] and e in G[rel.value][e_prime]:
                    if rel in [Relations.C, Relations.M]:
                        enc[e].add((e_prime, rel.value, 'out'))
                    else:
                        enc[e].add((e_prime, rel.value, 'in'))
    return enc


def get_opposite_rel_dict_str(relStr, direction, event, nestingId):
    relation_dict_str_del = (event, relStr, "out" if direction == "in" else "in")
    relation_dict_str_add = (nestingId, relStr, "out" if direction == "in" else "in")

    return relation_dict_str_del, relation_dict_str_add


def should_add(rel, direction):
    return direction == 'in' if rel in [Relations.C.value, Relations.M.value] else direction == 'out'


class Nesting(object):

    def __init__(self):
        self.nesting_ids = set()
        self.nesting_map = {}
        self.nest_id = 0
        self.enc = None
        self.in_rec_step = 0
        self.out_rec_step = 0
        self.debug = False

    def create_encoding(self, dcr_graph):
        self.enc = encode(dcr_graph)

    def find_largest_nesting(self, events_source, parent_nesting=None):
        cands = {}
        events = deepcopy(events_source)
        for e in events:
            for j in events:
                arrow_s = frozenset(self.enc[e].intersection(self.enc[j]))
                if len(arrow_s) > 0:
                    if not arrow_s in cands:
                        cands[arrow_s] = set([])
                    cands[arrow_s] = cands[arrow_s].union(set([e, j]))

        best_score = 0
        best = None
        for arrow_s in cands.keys():
            cand_score = (len(cands[arrow_s]) - 1) * len(arrow_s)
            if cand_score > best_score:
                best_score = cand_score
                best = arrow_s

        if best and len(cands[best]) > 1 and len(best) >= 1:
            if self.debug:
                print(f'[out]:{self.out_rec_step} [in]:{self.in_rec_step} \n'
                      f'     [events] {events} \n'
                      f'[cands[best]] {cands[best]} \n'  # these are the events inside the nesting
                      f'       [best] {best} \n'
                      f'        [enc] {self.enc} \n '
                      f'      [cands] {cands} \n')

            self.nest_id += 1
            nest_event = f'Group{self.nest_id}'
            self.nesting_ids.add(nest_event)
            self.enc[nest_event] = set(best)

            if parent_nesting:
                parent_nesting['events'] = parent_nesting['events'].difference(cands[best])
                parent_nesting['events'].add(nest_event)
                self.nesting_map[nest_event] = parent_nesting['id']

            for e in cands[best]:
                self.nesting_map[e] = nest_event
                self.enc[e] = self.enc[e].difference(best)
                for (e_prime, rel, direction) in best:
                    op_rel_del, op_rel_add = get_opposite_rel_dict_str(rel, direction, e, nest_event)
                    # TODO: find out why sometimes it tries to remove non-existing encodings
                    self.enc[e_prime].discard(op_rel_del)  # .remove(op_rel_del)
                    self.enc[e_prime].add(op_rel_add)

            retval = [{'nestingEvents': cands[best], 'sharedRels': best}]
            found = True
            while found:
                temp_retval = self.find_largest_nesting(events_source=cands[best], parent_nesting={'id': f'Group{self.nest_id}', 'events': cands[best]})
                if temp_retval and len(temp_retval) > 0:
                    retval.extend(temp_retval)
                    for tmp in temp_retval:
                        events = events.difference(tmp['nestingEvents'])
                else:
                    found = False
                self.in_rec_step += 1
            return retval

    def nest(self, events_source):
        nestings_arr = [{'nestingEvents': set(), 'sharedRels': set()}]
        events = deepcopy(events_source)

        while True:
            temp_retval = self.find_largest_nesting(events)
            if temp_retval and len(temp_retval) > 0:
                nestings_arr.extend(temp_retval)
                for tmp in temp_retval:
                    events = events.difference(tmp['nestingEvents'])
            else:
                break
            self.out_rec_step += 1

        return self.nesting_map, self.nesting_ids

    def remove_redundant_nestings(self):
        nestings = {}
        for n in self.nesting_ids:
            nestings[n] = set()
        for k, v in self.nesting_map.items():
            nestings[v].add(k)

        # Removing redundant nestings
        nests_to_remove = set([])
        for key in nestings:
            val = nestings[key]
            if len(val) == 1:
                nests_to_remove.add(list(val)[0])

        for nest_to_remove in nests_to_remove:
            parent = self.nesting_map[nest_to_remove]
            for k, v in list(self.nesting_map.items()):
                if v == nest_to_remove:
                    self.nesting_map[k] = parent
            print("Deleting: ", nest_to_remove)
            del self.nesting_map[nest_to_remove]
            self.nesting_ids.remove(nest_to_remove)

            for e, v in deepcopy(list(self.enc.items())):
                for r in v:
                    (e_prime, rel, direction) = r
                    if e_prime == nest_to_remove:
                        self.enc[e].remove(r)
                        self.enc[e].add((parent, rel, direction))
                if e == nest_to_remove:
                    self.enc[parent] = self.enc[parent].union(self.enc[e])
                    del self.enc[e]

    def get_nested_dcr_graph(self, existing_nestings=None):
        res_dcr = deepcopy(dcr_template)
        events = set(self.enc.keys())
        res_dcr['events'] = events
        res_dcr['marking']['included'] = events

        for n in self.nesting_ids:
            res_dcr['nestings'][n] = set()
        for k, v in self.nesting_map.items():
            res_dcr['nestings'][v].add(k)

        for e, v in self.enc.items():
            for e_prime, rel, direction in v:
                if should_add(rel, direction):
                    if e not in res_dcr[rel]:
                        res_dcr[rel][e] = set()
                    res_dcr[rel][e].add(e_prime)

        if existing_nestings:
            for me, me_events in existing_nestings.items():
                if me not in res_dcr['nestings']:
                    res_dcr['nestings'][me] = set()
                for me_event in me_events:
                    if me_event in self.nesting_map:
                        highest_nesting = self.nesting_map[me_event]
                        while True:
                            if highest_nesting in self.nesting_map:
                                highest_nesting = self.nesting_map[highest_nesting]
                            else:
                                break
                        if highest_nesting not in res_dcr['nestings'][me]:
                            res_dcr['nestings'][me].add(highest_nesting)
                    else:
                        res_dcr['nestings'][me].add(me_event)
                    self.nesting_map[me_event] = me
                if self.debug:
                    print(self.nesting_map[me])
                    print(self.nesting_map)
                    print(res_dcr['nestings'])

        res_dcr['nestingsMap'] = deepcopy(self.nesting_map)

        return res_dcr
