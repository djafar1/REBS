from typing import Set

from pm4py.objects.dcr.ocdcr.obj import DcrGraph, DcrElement, DcrNesting, DcrSubProcess, DcrActivity, DcrRelation, Spawn, RelationType


class DcrSemantics:

    @classmethod
    def getEffects(cls, graph: DcrGraph, element: DcrElement) -> Set[DcrRelation]:
        res = set()
        for rel in graph.relations:
            if rel.source == element and rel.relationType in RelationType.EFFECTS:
                res.add(rel)
        return res

    @classmethod
    def getConstraints(cls, graph: DcrGraph, element: DcrElement) -> Set[DcrRelation]:
        res = set()
        for rel in graph.relations:
            if rel.target == element and rel.relationType in RelationType.CONSTRAINTS:
                res.add(rel)
        return res

    @classmethod
    def getChildren(cls, element: DcrNesting | DcrSubProcess, graph: DcrGraph) -> Set[DcrElement]:
        children = set()
        for e in graph.elements:
            if element in e.parents:
                children.add(e)
        return children

    @classmethod
    def included(cls, graph: DcrGraph) -> Set[DcrElement]:
        inc = set()
        for e in graph.elements:
            if isinstance(e, DcrActivity) and e.included and not e.isTemplate:
                inc.add(e)
        return inc

    @classmethod
    def enabled(cls, graph: DcrGraph) -> Set[DcrElement]:
        res = cls.included(graph)
        for e in res:
            if isinstance(e, DcrSubProcess) and e.childrenPending:
                res.discard(e)
            constraints = cls.getConstraints(graph, e)
            for r in constraints:
                if r.source.effectiveIncluded:
                    if r.relationType == RelationType.C and not r.source.executed:
                        res.discard(e)
                    elif r.relationType == RelationType.M and r.pending:
                        res.discard(e)
                
        return res
    
    @classmethod
    def isEnabled(cls, element: DcrActivity | DcrSubProcess, graph: DcrGraph) -> bool:
        return element in cls.enabled(graph)
    
    @classmethod
    def updateIncluded(cls, element: DcrElement, graph: DcrGraph):
        element.parentsIncluded = True
        for parent in element.parents:
            element.parentsIncluded = element.parentsIncluded and parent.included
    
    @classmethod
    def updatePending(cls, element: DcrNesting | DcrSubProcess, graph: DcrGraph):
        element.childrenPending = False
        children = cls.getChildren(element, graph)
        for child in children:
            element.childrenPending = element.childrenPending or child.pending

    @classmethod
    def executeEvent(cls, event, graph: DcrGraph):
        activity = graph.getActivity(event)

        cls.execute(activity, graph)
    
    @classmethod
    def execute(cls, element: DcrActivity | DcrSubProcess, graph: DcrGraph):
        element.pending = False
        for parent in element.parents:
            cls.updatePending(parent, graph)
        element.executed = True

        effects = cls.getEffects(graph, element)
        for r in effects:
            cls.relateToTarget(r.target, r)

        for p in element.parents:
            if isinstance(p, DcrSubProcess) and cls.isEnabled(p, graph):
                cls.execute(p, graph)

    @classmethod
    def relateToTarget(cls, element: DcrElement, relation: DcrRelation, graph: DcrGraph):
        if isinstance(element, DcrNesting):
            children = cls.getChildren(element, graph)
            for child in children:
                cls.relateToTarget(child, relation)
        
        else:
            match relation.relationType:
                case RelationType.I:
                    element.included = True
                    element.effectiveIncluded = True
                    for p in element.parents:
                        element.effectiveIncluded = element.effectiveIncluded and p.effectiveIncluded
                case RelationType.E:
                    element.included = False
                case RelationType.R:
                    element.pending = True
                case RelationType.N:
                    element.pending = False
                case RelationType.S:
                    relation.spawned += 1
                    cls.spawnTarget(element, graph, relation.spawned)
                case RelationType.V:
                    element.data = relation.source.data
    
    @classmethod
    def spawn(cls, element: DcrElement, graph: DcrGraph, spawnNumber: int):
        elementDict = cls.spawnElement(element, element.parents, graph, spawnNumber)
        relations = set()

        for key in elementDict:
            effects = cls.getEffects(graph, key)
            for e in effects:
                target = elementDict[e.target] if e.target in elementDict else e.target
                if e.relationType == RelationType.S:
                    relations.add(Spawn(elementDict[key], target, e.guard))
                else:
                    relations.add(DcrRelation(e.relationType, elementDict[key], target, e.guard))
            constraints = cls.getConstraints
            for c in constraints:
                source = elementDict[c.source] if c.source in elementDict else c.source
                relations.add(DcrRelation(c.relationType, source, elementDict[key], c.guard))
        
        graph.elements.update(elementDict.values())
        graph.relations.update(relations)

    @classmethod
    def spawnElement(cls, element: DcrElement, parents: list[DcrElement], graph: DcrGraph, spawnNumber: int):
        spawns = {}
        children = None

        if isinstance(element, DcrNesting):
            spawns[element] = DcrNesting(element.ID + str(spawnNumber), parents)
            children = cls.getChildren(element, graph)
        elif isinstance(element, DcrSubProcess):
            spawns[element] = DcrSubProcess(element.ID + str(spawnNumber), parents)
            children = cls.getChildren(element, graph)
        else:
            spawns[element] = DcrActivity(element.ID + str(spawnNumber), parents)

        if children:
            for c in children:
                childSpawns = cls.spawnElement(c, element)
                for s in childSpawns:
                    if s in spawns:   
                        spawns[s].parents.update(childSpawns[s].parents)
                    else: spawns[s] = childSpawns[s]

        return spawns

    @classmethod
    def isAccepting(cls, graph: DcrGraph) -> bool:
        inc = cls.included(graph)
        for e in inc:
            if e.pending:
                return False
        return True