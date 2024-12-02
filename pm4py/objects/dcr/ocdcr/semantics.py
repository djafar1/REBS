from typing import Set

from pm4py.objects.dcr.ocdcr.obj import DcrGraph, DcrElement, DcrNesting, DcrSubProcess, DcrActivity, DcrRelation, RelationType


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

    # Doesn't catch included activities with an excluded subprocess parent more than one level up -- make recursive
    # Also doesn't catch subprocesses with excluded parents
    @classmethod
    def included(cls, graph: DcrGraph) -> Set[DcrElement]:
        inc = set()
        exSub = set()
        for s in graph.subprocesses:
            if s.included: inc.add(s)
            else: exSub.add(s)
        for a in graph.activities:
            if a.included and len(a.parents.intersection(exSub)) == 0:
                inc.add(a)
        return inc

    @classmethod
    def enabled(cls, graph: DcrGraph) -> Set[DcrElement]:
        inc = cls.included(graph)
        res = inc.copy()
        for e in res:
            constraints = cls.getConstraints(graph, e)
            for r in constraints:
                if r.source in inc and r.relationType == RelationType.C and not r.source.executed:
                    res.discard(e)
                elif r.source in inc and r.relationType == RelationType.M and r.pending:
                    res.discard(e)
        return res
    
    @classmethod
    def is_enabled(cls, event, graph: DcrGraph) -> bool:
        return event in cls.enabled(graph)
    
    """
    @classmethod
    def spawnTarget(cls, element: DcrElement, graph: DcrGraph, parents=None, source=None, target=None):
        relationsTo = set()
        for r in element.relationsTo:
            relationsTo.add(cls.spawnTarget(r, graph))
        relationedBy = set()
        for r in element.relationedBy:
            relationedBy.add(cls.spawnTarget(r, graph))
        if isinstance(element, DcrRelation):
            spawn = DcrRelation(source, target, guard, deadline)
        if isinstance(element, DcrNesting):
            children = set()
            for c in element.children:
                children.add(cls.spawnTarget(c, graph, parents=[element]))
            spawn = DcrNesting(ID, parents, relationsTo, relationedBy, children)
        elif isinstance(element, DcrSubProcess):
            spawn = DcrSubProcess(ID, parents, relationsTo, relationedBy, children, template=element)
        else:
            spawn = DcrActivity(ID, parents, relationsTo, relationedBy, template=element)

        return spawn
    """

    @classmethod
    def relateToTarget(cls, element: DcrElement, relation: DcrRelation, graph: DcrGraph):
        if isinstance(element, DcrNesting):
            for child in element.children:
                cls.relateToTarget(child, relation)
        else:
            match relation.relationType:
                case RelationType.I:
                    element.included = True
                case RelationType.E:
                    element.included = False
                case RelationType.R:
                    element.pending = True
                case RelationType.N:
                    element.pending = False
                case RelationType.S:
                    cls.spawnTarget(element, graph)
                case RelationType.V:
                    element.data = relation.source.data

    @classmethod
    def execute(cls, graph: DcrGraph, event):
        activity = graph.get_activity(event)

        activity.pending = False
        activity.executed = True

        effects = cls.getEffects(graph, activity)
        for r in effects:
            cls.relateToTarget(r.target, r)

    @classmethod
    def is_accepting(cls, graph: DcrGraph) -> bool:
        inc = cls.included(graph)
        for e in inc:
            if e.pending:
                return False
        return True