from pm4py.models.petri import semantics
from copy import deepcopy,copy
import time
from threading import Thread
from pm4py.log.util import variants as variants_module

MAX_REC_DEPTH = 50
MAX_IT_FINAL = 10
MAX_REC_DEPTH_HIDTRANSENABL = 5

class NoConceptNameException(Exception):
    def __init__(self, message):
        self.message = message

def add_missingTokens(t, net, marking, trace, traceIndex):
    """
    Adds missing tokens needed to activate a transition

    Parameters
    ----------
    t
        Transition that should be enabled
    net
        Petri net
    marking
        Current marking
    trace
        Examined trace
    traceIndex
        Trace index
    """
    missing = 0
    tokensAdded = {}
    for a in t.in_arcs:
        if marking[a.source] < a.weight:
            missing = missing + (a.weight - marking[a.source])
            marking[a.source] = marking[a.source] + a.weight
            tokensAdded[a.source] = a.weight - marking[a.source]
    return [missing, tokensAdded]

def get_consumedTokens(t, net):
    """
    Get tokens consumed firing a transition

    Parameters
    ----------
    t
        Transition that should be enabled
    net
        Petri net
    """
    consumed = 0
    for a in t.in_arcs:
        consumed = consumed + a.weight
    return consumed

def get_producedTokens(t, net):
    """
    Get tokens produced firing a transition

    Parameters
    ----------
    t
        Transition that should be enabled
    net
        Petri net
    """
    produced = 0
    for a in t.out_arcs:
        produced = produced + a.weight
    return produced

def merge_dicts(x, y):
    """
    Merge two dictionaries

    Parameters
    ----------
    x
        First map (string, integer)
    y
        Second map (string, integer)
    """
    for key in y:
        if not key in x:
            x[key] = y[key]
        else:
            if y[key] < x[key]:
                x[key] = y[key]

def get_hiddenTrans_ReachTrans(t, net, recDepth):
    """
    Get visible transitions reachable by enabling a hidden transition

    Parameters
    ----------
    t
        Transition that should be enabled
    net
        Petri net
    recDepth
        Current recursion depth
    """
    reachTrans = {}
    if recDepth > MAX_REC_DEPTH:
        return reachTrans
    for a1 in t.out_arcs:
        place = a1.target
        for a2 in place.out_arcs:
            t2 = a2.target
            if t2.label is not None:
                reachTrans[t2.label] = recDepth
            if t2.label is None:
                merge_dicts(reachTrans, get_hiddenTrans_ReachTrans(t2, net, recDepth + 1))
    return reachTrans

def get_placesWithMissingTokens(t, net, marking):
    """
    Get places with missing tokens

    Parameters
    ----------
    t
        Transition to enable
    net
        Petri net
    marking
        Current marking
    """
    placesWithMissing = set()
    for a in t.in_arcs:
        if marking[a.source] < a.weight:
            placesWithMissing.add(a.source)
    return placesWithMissing

def get_placesShortestPath(net, placeToPopulate, currentPlace, placesShortestPath, actualList, recDepth):
    """
    Get shortest path between places lead by hidden transitions

    Parameters
    ----------
    net
        Petri net
    placeToPopulate
        Place that we are populating the shortest map of
    currentPlace
        Current visited place (must explore its transitions)
    placesShortestPath
        Current dictionary
    actualList
        Actual list of transitions to enable
    recDepth
        Recursion depth
    """
    if recDepth > MAX_REC_DEPTH:
        return placesShortestPath
    if not placeToPopulate in placesShortestPath:
        placesShortestPath[placeToPopulate] = {}
    for t in currentPlace.out_arcs:
        if t.target.label is None:
            for p2 in t.target.out_arcs:
                if not p2.target in placesShortestPath[placeToPopulate] or len(actualList)+1 < len(placesShortestPath[placeToPopulate][p2.target]):
                    newActualList = copy(actualList)
                    newActualList.append(t.target)
                    placesShortestPath[placeToPopulate][p2.target] = copy(newActualList)
                    placesShortestPath = get_placesShortestPath(net, placeToPopulate, p2.target, placesShortestPath, newActualList, recDepth+1)
    return placesShortestPath

def get_placesShortestPathByHidden(net):
    """
    Get shortest path between places lead by hidden transitions

    Parameters
    ----------
    net
        Petri net
    """
    placesShortestPath = {}
    for p in net.places:
        placesShortestPath = get_placesShortestPath(net,p,p,placesShortestPath,[],0)
    return placesShortestPath

def apply_hiddenTrans(t, net, marking, placesShortestPathByHidden, activatedTransitions, recDepth, visitedTransitions):
    if recDepth >= MAX_REC_DEPTH_HIDTRANSENABL or t in visitedTransitions:
        return [net, marking, activatedTransitions]

    visitedTransitions.add(t)

    markingAtStart = copy(marking)

    placesWithMissing = get_placesWithMissingTokens(t, net, marking)
    hiddenTransitionsToEnable = []
    for p1 in marking:
        for p2 in placesWithMissing:
            if p2 in placesShortestPathByHidden[p1]:
                hiddenTransitionsToEnable.append(placesShortestPathByHidden[p1][p2])
    if hiddenTransitionsToEnable:
        somethingChanged = True
        jIndexes = [0 for x in hiddenTransitionsToEnable]
        z = 0
        while somethingChanged:
            somethingChanged = False
            while jIndexes[z % len(hiddenTransitionsToEnable)] < len(
                    hiddenTransitionsToEnable[z % len(hiddenTransitionsToEnable)]):
                enabledTransitions = semantics.enabled_transitions(net, marking)
                t3 = hiddenTransitionsToEnable[z % len(hiddenTransitionsToEnable)][
                    jIndexes[z % len(hiddenTransitionsToEnable)]]
                if not t3 == t:
                    if t3 in enabledTransitions and semantics.is_enabled(t3, net, marking):
                        if not t3 in visitedTransitions:
                            marking = semantics.execute(t3, net, marking)
                            activatedTransitions.append(t3)
                            visitedTransitions.add(t3)
                            enabledTransitions = semantics.enabled_transitions(net, marking)
                            somethingChanged = True
                jIndexes[z % len(hiddenTransitionsToEnable)] = jIndexes[z % len(hiddenTransitionsToEnable)] + 1
                if semantics.is_enabled(t, net, marking):
                    break
            if semantics.is_enabled(t, net, marking):
                break
            z = z + 1

        if not semantics.is_enabled(t, net, marking):
            hiddenTransitionsToEnable = []
            for p1 in marking:
                for p2 in placesWithMissing:
                    if p2 in placesShortestPathByHidden[p1]:
                        hiddenTransitionsToEnable.append(placesShortestPathByHidden[p1][p2])
            z = 0
            while z < len(hiddenTransitionsToEnable):
                k = 0
                while k < len(hiddenTransitionsToEnable[z]):
                    t4 = hiddenTransitionsToEnable[z][k]
                    if not t4 == t:
                        if not t4 in visitedTransitions:
                            if not semantics.is_enabled(t4, net, marking):
                                [net, marking, activatedTransitions] = apply_hiddenTrans(t4, net, marking, placesShortestPathByHidden, activatedTransitions, recDepth+1, visitedTransitions)
                            if semantics.is_enabled(t4, net, marking):
                                marking = semantics.execute(t4, net, marking)
                                activatedTransitions.append(t4)
                                visitedTransitions.add(t4)
                    k = k + 1
                z = z + 1

        if not semantics.is_enabled(t, net, marking):
            if not(markingAtStart == marking):
                [net, marking, activatedTransitions] = apply_hiddenTrans(t, net, marking, placesShortestPathByHidden,
                                                                         activatedTransitions, recDepth + 1, visitedTransitions)

    return [net, marking, activatedTransitions]

def get_visible_transitions_eventually_enabled_by_marking(net, marking):
    """
    Get visible transitions eventually enabled by marking (passing possibly through hidden transitions)

    Parameters
    ----------
    net
        Petri net
    marking
        Current marking
    """
    allEnabledTransitions = list(semantics.enabled_transitions(net, marking))
    visibleTransitions = set()
    visitedTransitions = set()

    i = 0
    while i < len(allEnabledTransitions):
        t = allEnabledTransitions[i]
        if not t in visitedTransitions:
            if t.label is not None:
                visibleTransitions.add(t)
            else:
                markingCopy = copy(marking)
                if semantics.is_enabled(t, net, markingCopy):
                    newMarking = semantics.execute(t, net, markingCopy)
                    newEnabledTransitions = list(semantics.enabled_transitions(net, newMarking))
                    allEnabledTransitions = allEnabledTransitions + newEnabledTransitions
            visitedTransitions.add(t)
        i = i + 1

    return visibleTransitions

def apply_trace(trace, net, initialMarking, finalMarking, transMap, enable_placeFitness, place_fitness, placesShortestPathByHidden, consider_remaining_in_fitness, activity_key="concept:name", tryToReachFinalMarkingThroughHidden=True, stopImmediatelyWhenUnfit=False, useHiddenTransitionsToEnableCorrespondingTransitions=True):
    """
    Apply the token replaying algorithm to a trace

    Parameters
    ----------
    trace
        Trace in the event log
    net
        Petri net
    initialMarking
        Initial marking
    finalMarking
        Final marking
    transMap
        Map between transitions labels and transitions
    enable_placeFitness
        Enable fitness calculation at place level
    """
    is_fit = False
    trace_fitness = 0.0
    activatedTransitions = []
    activatedHiddenTransitions = []
    marking = copy(initialMarking)
    missing = 0
    consumed = 0
    produced = 0
    remaining = 0
    i = 0
    while i < len(trace):
        if trace[i][activity_key] in transMap:
            t = transMap[trace[i][activity_key]]
            if useHiddenTransitionsToEnableCorrespondingTransitions and not semantics.is_enabled(t, net, marking):
                visitedTransitions = 0
                visitedTransitions = set()
                [net, marking, activatedTransitions] = apply_hiddenTrans(t, net, marking, placesShortestPathByHidden, activatedTransitions, 0, visitedTransitions)

            if not semantics.is_enabled(t, net, marking):
                if stopImmediatelyWhenUnfit:
                    missing = missing + 1
                    break
                [m, tokensAdded] = add_missingTokens(t, net, marking, trace, i)
                missing = missing + m
                if enable_placeFitness:
                    for place in tokensAdded.keys():
                        if place in place_fitness:
                            place_fitness[place]["underfedTraces"].add(trace)
            else:
                m = 0
            c = get_consumedTokens(t, net)
            p = get_producedTokens(t, net)
            consumed = consumed + c
            produced = produced + p
            activatedTransitions.append(t)
            if semantics.is_enabled(t, net, marking):
                marking = semantics.execute(t, net, marking)
        i = i + 1

    oldActivatedTransitions = copy(activatedTransitions)
    oldMarking = copy(marking)

    if tryToReachFinalMarkingThroughHidden:
        i = 0
        while i < MAX_IT_FINAL:
            visitedTransitions = 0
            visitedTransitions = set()
            if not dict(marking) == dict(finalMarking):
                markingCopy = copy(marking)
                for p in markingCopy:
                    for p2 in finalMarking:
                        if p in placesShortestPathByHidden and p2 in placesShortestPathByHidden[p]:
                            reqTransitions = placesShortestPathByHidden[p][p2]
                            for t in reqTransitions:
                                if useHiddenTransitionsToEnableCorrespondingTransitions and not semantics.is_enabled(t, net, marking):
                                    [net, marking, activatedTransitions] = apply_hiddenTrans(t, net, marking,
                                                                                             placesShortestPathByHidden,
                                                                                             activatedTransitions, 0, visitedTransitions)
                                    if semantics.is_enabled(t, net, marking):
                                        marking = semantics.execute(t, net, marking)
                                        activatedTransitions.append(t)
                                elif semantics.is_enabled(t, net, marking):
                                    marking = semantics.execute(t, net, marking)
                                    activatedTransitions.append(t)
            else:
                break
            i = i + 1

    markingBeforeCleaning = copy(marking)

    remaining = 0
    for p in marking:
        if p in finalMarking:
            marking[p] = max(0, marking[p] - finalMarking[p])
            if enable_placeFitness:
                if marking[p] > 0:
                    if p in place_fitness:
                        if not trace in place_fitness[p]["underfedTraces"]:
                            place_fitness[p]["overfedTraces"].add(trace)
        remaining = remaining + marking[p]
    if consider_remaining_in_fitness:
        is_fit = (missing == 0) and (remaining == 0)
    else:
        is_fit = (missing == 0)

    if consumed > 0 and produced > 0:
        trace_fitness = (1.0 - float(missing)/float(consumed)) * (1.0 - float(remaining)/float(produced))
    else:
        trace_fitness = 1.0

    return [is_fit, trace_fitness, activatedTransitions, markingBeforeCleaning, get_visible_transitions_eventually_enabled_by_marking(net, markingBeforeCleaning)]

class ApplyTraceTokenReplay(Thread):
    def __init__(self, trace, net, initialMarking, finalMarking, transMap, enable_placeFitness, place_fitness, placesShortestPathByHidden, consider_remaining_in_fitness, activity_key="concept:name", tryToReachFinalMarkingThroughHidden=True, stopImmediatelyWhenUnfit=False, useHiddenTransitionsToEnableCorrespondingTransitions=True):
        """
        Constructor
        """
        self.trace = trace
        self.net = net
        self.initialMarking = initialMarking
        self.finalMarking = finalMarking
        self.transMap = transMap
        self.enable_placeFitness = enable_placeFitness
        self.place_fitness = place_fitness
        self.placesShortestPathByHidden = placesShortestPathByHidden
        self.consider_remaining_in_fitness = consider_remaining_in_fitness
        self.activity_key = activity_key
        self.tryToReachFinalMarkingThroughHidden = tryToReachFinalMarkingThroughHidden
        self.stopImmediatelyWhenUnfit = stopImmediatelyWhenUnfit
        self.useHiddenTransitionsToEnableCorrespondingTransitions = useHiddenTransitionsToEnableCorrespondingTransitions
        Thread.__init__(self)

    def run(self):
        """
        Runs the thread and stores the results
        """
        self.tFit, self.tValue, self.actTrans, self.reachedMarking, self.enabledTransitionsInMarking =\
            apply_trace(self.trace, self.net, self.initialMarking, self.finalMarking, self.transMap,
                                                           self.enable_placeFitness, self.place_fitness,
                                                           self.placesShortestPathByHidden, self.consider_remaining_in_fitness, activity_key=self.activity_key,
                                                                                          tryToReachFinalMarkingThroughHidden=self.tryToReachFinalMarkingThroughHidden,
                                                                                          stopImmediatelyWhenUnfit=self.stopImmediatelyWhenUnfit,
                                                                                          useHiddenTransitionsToEnableCorrespondingTransitions=self.useHiddenTransitionsToEnableCorrespondingTransitions)
        #print("thread finished")

def apply_log(log, net, initialMarking, finalMarking, enable_placeFitness=False, consider_remaining_in_fitness=False, activity_key="concept:name", tryToReachFinalMarkingThroughHidden=True, stopImmediatelyWhenUnfit=False, useHiddenTransitionsToEnableCorrespondingTransitions=True, placesShortestPathByHidden=None):
    """
    Apply token-based replay to a log

    Parameters
    ----------
    log
        Trace log
    net
        Petri net
    initialMarking
        Initial marking
    finalMarking
        Final marking
    enable_placeFitness
        Enable fitness calculation at place level
    """
    if placesShortestPathByHidden is None:
        placesShortestPathByHidden = get_placesShortestPathByHidden(net)
    traceIsFit = []
    traceFitnessValue = []
    activatedTransitions = []
    placeFitnessPerTrace = {}
    reachedMarkings = []
    enabledTransitionsInMarkings = []
    if enable_placeFitness:
        for place in net.places:
            placeFitnessPerTrace[place] = {"underfedTraces": set(), "overfedTraces": set()}
    transMap = {}
    for t in net.transitions:
        transMap[t.label] = t
    if len(log) > 0:
        if len(log[0]) > 0:
            if activity_key in log[0][0]:
                variants = variants_module.get_variants_from_log(log, activity_key=activity_key)
                threads = {}
                for variant in variants:
                    threads[variant] = ApplyTraceTokenReplay(variants[variant][0], net, initialMarking, finalMarking, transMap, enable_placeFitness, placeFitnessPerTrace, placesShortestPathByHidden, consider_remaining_in_fitness, activity_key=activity_key, tryToReachFinalMarkingThroughHidden=tryToReachFinalMarkingThroughHidden, stopImmediatelyWhenUnfit=stopImmediatelyWhenUnfit, useHiddenTransitionsToEnableCorrespondingTransitions=useHiddenTransitionsToEnableCorrespondingTransitions)
                    threads[variant].start()
                for variant in threads:
                    threads[variant].join()
                for trace in log:
                    traceVariant =  ",".join([x[activity_key] for x in trace])
                    t = threads[traceVariant]
                    traceIsFit.append(t.tFit)
                    traceFitnessValue.append(t.tValue)
                    activatedTransitions.append(t.actTrans)
                    reachedMarkings.append(t.reachedMarking)
                    enabledTransitionsInMarkings.append(t.enabledTransitionsInMarking)
            else:
                raise NoConceptNameException("at least an event is without " + activity_key)
    return [traceIsFit, traceFitnessValue, activatedTransitions, placeFitnessPerTrace, reachedMarkings,
            enabledTransitionsInMarkings]