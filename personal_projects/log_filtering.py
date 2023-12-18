from pm4py.objects.log.importer.xes import importer
from pm4py.objects.log.exporter.xes import exporter
from pm4py.objects.log.obj import EventLog, Trace

from math import exp
import os, sys


def filterLog(trainingLogPath, PF, DT, AT, filterThreshold=100):
    alpha = 0.5
    GNF = 0.02
    C1 = 4
    C2 = 4

    # Parsing log
    log = importer.apply(trainingLogPath)

    # Generating auxilliary sets for detemining dPre and dSuc
    preSets = {}
    sucSets = {}
    DFDs = {}
    eventIds = set()

    for trace in log:
        lastEvent = None
        for event in trace:
            eventId = event["concept:name"]
            eventIds.add(eventId)
            if not eventId in preSets:
                preSets[eventId] = set()
                sucSets[eventId] = set()
                DFDs[eventId] = {}
            if lastEvent is not None:
                # Add this event to the successors of the previos element
                sucSets[lastEvent].add(eventId)
                # Increment the DFD from last element to this element
                if not eventId in DFDs[lastEvent]:
                    DFDs[lastEvent][eventId] = 1
                else:
                    DFDs[lastEvent][eventId] += 1
                # Add the last element to the predecessors of this element
                preSets[eventId].add(lastEvent)
            lastEvent = eventId

    # Generating dPre and dSuc
    # dPre[eventId] = nPre[eventId] / preSet[eventId].length
    # dSuc[eventId] = nSuc[eventId] / sucSet[eventId].length
    dPre = {}
    dSuc = {}

    for eventId in eventIds:
        nPre = 0
        for preEvent in preSets[eventId]:
            nPre += DFDs[preEvent][eventId]
        if (len(preSets[eventId]) != 0):
            dPre[eventId] = nPre / len(preSets[eventId])
        nSuc = 0
        for sucEvent in sucSets[eventId]:
            nSuc += DFDs[eventId][sucEvent]
        if (len(sucSets[eventId]) != 0):
            dSuc[eventId] = nSuc / len(sucSets[eventId])

    # Constructing mixed dependency matrix
    # constructing theta
    dfdSum = 0
    for e1 in DFDs:
        for e2 in DFDs[e1]:
            dfdSum += DFDs[e1][e2]
    theta = 0
    for e1 in DFDs:
        for e2 in DFDs[e1]:
            tmp = DFDs[e1][e2]
            if tmp > theta and tmp / dfdSum < GNF:
                theta = tmp

    mdMatrix = {}
    for ei in DFDs:
        mdMatrix[ei] = {}
        for ej in DFDs[ei]:
            # if ei has no sucessor or ej has no predecessor, their dependency is meaningless
            # if (len(sucSets[ei]) == 0 or len(preSets[ej]) == 0):
            #    mdMatrix[ei][ej] = 0
            #    continue
            # local dependency
            sucExp = (DFDs[ei][ej] - dSuc[ei]) * (C1 / dSuc[ei])
            preExp = (DFDs[ei][ej] - dPre[ej]) * (C2 / dPre[ej])
            dLocal = 1 - (1 / ((1 + exp(sucExp)) * 2)) - (1 / ((1 + exp(preExp)) * 2))
            # global dependency
            dGlobal = 1 / (1 + exp(1 - DFDs[ei][ej] / theta))
            # mixed dependency
            mdMatrix[ei][ej] = alpha * dLocal + (1 - alpha) * dGlobal

    filteredLog = EventLog()

    # Data for filtering threshold
    eventCount = 0
    filterCount = 0

    for trace in log:
        # Init an empty trace
        filteredTrace = Trace()
        filteredTrace._set_attributes(trace._get_attributes())
        # Abandon factor for trace
        AF = 1
        ei = None
        eventFiltered = False
        for event in trace:
            eventCount += 1
            ej = event["concept:name"]
            if ei == None:
                ei = ej
                # Always add start event
                filteredTrace.append(event)
            else:
                # If no entry exists for [ei][ej] then ej was never a sucessor to ei, and therefore it should be filtered
                # This will only occur due to filtering an event that was previously between them.
                try:
                    dependency = mdMatrix[ei][ej]
                except:
                    dependency = 0
                if dependency >= DT:
                    # High dependency, not noise
                    filteredTrace.append(event)
                    ei = ej
                else:
                    # Event filtered
                    filterCount += 1
                    AF = AF * PF * (1 + 2 * (1 / PF - 1) * dependency)

        # if abandon factor is still above abandon threshold, the trace is not filtered
        if (AF > AT):
            filteredLog.append(filteredTrace)

    filteredEventPercent = 100 * filterCount / eventCount

    if filteredEventPercent > filterThreshold:
        return log

    return filteredLog


# OPTIMAL PARAMETERS FOR PDC2020
PF = 0.05
AT = 0.9
DT = 0.2

if (len(sys.argv) != 3):
    print("Please provide only the path of the log to be filtered and the path to export the filtered log.")
else:
    logPath = sys.argv[1]
    exportPath = sys.argv[2]
    filteredLog = filterLog(logPath, PF, DT, AT, filterThreshold=50)
    exporter.apply(filteredLog, exportPath)