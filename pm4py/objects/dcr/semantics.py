from copy import deepcopy

rels = ['conditionsFor', 'responseTo', 'includesTo', 'excludesTo']

#TODO: add subprocess and timed execution semantics


def execute(e, dcr, cmd_print=False):
    if e in dcr['events']:
        if is_enabled(e, dcr):
            weak_execute(e, dcr)
            return True
        else:
            print(f'[!] Event {e} not enabled!') if cmd_print else None
            return False
    else:
        print(f'[!] Event {e} does not exist!') if cmd_print else None
        return False

def time_step(time, dcr, dict_exe):
    deadline = find_next_deadline(dcr)
    if deadline == None or deadline - time >= 0:
        for e in dcr['marking']['pendingDeadline']:
            dcr['marking']['pendingDeadline'][e] =  max(dcr['marking']['pendingDeadline'][e] - time, 0)
        for e in dcr['marking']['executed']:
            dcr['marking']['executedTime'] = min(dcr['marking']['executedTime'][e_prime] + time, dict_exe[e_prime])
    else:
        print('The time step is not allowed, you are gonna miss a deadline')
    
def find_next_deadline(dcr):
    next_deadline = None
    for e in dcr['marking']['pendingDeadline']:
        if (next_deadline == None and e in dcr['marking']['included']) or (dcr['marking']['pendingDeadline'][e] < next_deadline and e in dcr['marking']['included']):
            next_deadline = dcr['marking']['pendingDeadline'][e]
    return next_deadline

def find_next_delay(dcr):
    next_delay = None
    for e in dcr['conditionsForDelays']:
        for (e_prime, k) in dcr['conditionsForDelays'][e]:
            if e_prime in dcr['marking']['executed'] and e_prime in dcr['marking']['included']:
                if next_delay == None or k - dcr['marking']['executedTime'][e_prime] < next_delay:
                    next_delay = k - dcr['marking']['executedTime'][e_prime]
    return next_delay

def create_max_executed_time_dict(dcr):
    d = {}
    for e in dcr['events']:
        d[e] = max_executed_time(e, dcr)
    d

def max_executed_time(event, dcr):
    max_delay = None
    for e in dcr['conditionsForDelays']:
        for (e_prime, k) in dcr['conditionsForDelays'][e]:
            if e_prime == event:
                if max_delay == None or k > max_delay:
                    max_delay = k
    return max_delay
        
def is_accepting(dcr):
    pend_incl = dcr['marking']['pending'].intersection(dcr['marking']['included'])
    return len(pend_incl) == 0


def is_enabled(e, dcr):
    return e in enabled(dcr)

def enabled(dcr):
    res = deepcopy(dcr['marking']['included'])
    for e in dcr['conditionsFor']:
        if e in res:
            for e_prime in dcr['conditionsFor'][e]:
                if e_prime in dcr['marking']['included'] and e_prime not in dcr['marking']['executed']:
                    res.discard(e)
                    
    for e in dcr['conditionsForDelays']:
        if e in res:
            for (e_prime, k) in dcr['conditionsForDelays'][e]:
                if e_prime in dcr['marking']['included'] and e_prime not in dcr['marking']['executed']:
                    res.discard(e)
                elif e_prime in dcr['marking']['included'] and e_prime in dcr['marking']['executed']:
                    if dcr['marking']['executedTime'][e_prime] < k:
                        res.discard(e)
                        
    # TODO: extend with milestones
    for e in dcr['milestonesFor']:
        if e in res:
            for e_prime in dcr['milestonesFor'][e]:
                if e_prime in dcr['marking']['included'] and e_prime in dcr['marking']['pending']:
                    res.discard(e)
    return res

def weak_execute(e, dcr):
    '''
    Executes events even if not enabled. This will break the condition (TODO: in the future the milestone) constraint.
    :param e:
    :param dcr:
    :return:
    '''
    dcr['marking']['pending'].discard(e)
    dcr['marking']['executed'].add(e)
    dcr['marking']['executedTime'][e] = 0
    if e in dcr['excludesTo']:
        for e_prime in dcr['excludesTo'][e]:
            dcr['marking']['included'].discard(e_prime)
    if e in dcr['includesTo']:
        for e_prime in dcr['includesTo'][e]:
            dcr['marking']['included'].add(e_prime)
    if e in dcr['responseTo']:
        for e_prime in dcr['responseTo'][e]:
            dcr['marking']['pending'].add(e_prime)
    if e in dcr['responseToDeadlines']:
        for (e_prime, k) in dcr['responseToDeadlines'][e]:
            dcr['marking']['pendingDeadline'][e_prime] = k
            dcr['marking']['pending'].add(e_prime)
    # TODO: extend with milestones


