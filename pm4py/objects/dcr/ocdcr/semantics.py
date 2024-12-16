from typing import Set
from datetime import datetime

from pm4py.objects.dcr.ocdcr.obj import DcrGraph, DcrElement, DcrNesting, DcrSubProcess, DcrActivity, DcrRelation, DcrSpawn, RelationType, DcrExpression, DcrEvent


class DcrSemantics:

    @classmethod
    def getEffects(cls, element: DcrElement, graph: DcrGraph) -> Set[DcrRelation]:
        res = set()
        for r in graph.relations:
            if r.source == element and r.relationType in RelationType.EFFECTS:
                res.add(r)
        return sorted(res, key=lambda x: x.relationType)

    @classmethod
    def getConstraints(cls, element: DcrElement, graph: DcrGraph) -> Set[DcrRelation]:
        res = set()
        for rel in graph.relations:
            if rel.target == element and rel.relationType in RelationType.CONSTRAINTS:
                res.add(rel)
        return res
    
    @classmethod
    def isEnabled(cls, element: DcrActivity | DcrSubProcess, graph: DcrGraph) -> bool:
        if not element.included:
            return False
        if isinstance(element, DcrSubProcess) and element.childrenPending:
            return False
        constraints = cls.getConstraints(element, graph)
        for r in constraints:
            if r.guard is None or cls.evaluateExpression(r.guard, graph, r.source, element):
                if not cls.constraintPasses(r.source, r.relationType):
                    return False
        return True
    
    @classmethod
    def constraintPasses(cls, element: DcrElement, relationType: RelationType) -> bool:
        if type(element) is DcrNesting:
            res = True
            for child in element.children:
                res = res and cls.constraintPasses(child, relationType)
            return res
        if relationType == RelationType.C and not element.executed:
            return False
        if relationType == RelationType.M and element.pending:
            return False
        return True

    @classmethod
    def getRelations(cls, element: DcrElement, graph: DcrGraph) -> Set[DcrRelation]:
        incoming = set()
        outgoing = set()
        for rel in graph.relations:
            if rel.target == element:
                incoming.add(rel)
            elif rel.source == element:
                outgoing.add(rel)
        return incoming, outgoing

    @classmethod
    def getParents(cls, element: DcrElement, graph: DcrGraph) -> Set[DcrNesting | DcrSubProcess]:
        parents = set()
        for e in graph.elements:
            if element in e.children:
                parents.add(e)
        return parents
    
    @classmethod
    def parseAttribute(cls, element: DcrElement, attribute, graph: DcrGraph) -> any:
        if element:
            match attribute:
                case "included":
                    return element.included
                case "pending":
                    return element.pending
                case "executed":
                    if isinstance(element, DcrActivity):
                        return element.executed
                case "enabled":
                    if isinstance(element, DcrActivity):
                        return cls.isEnabled(element, graph)
                case "expression":
                    if isinstance(element, DcrActivity):
                        return element.expression
                case "data":
                    if isinstance(element, DcrActivity):
                        return element.data
                case "children":
                    if isinstance(element, DcrNesting):
                        return element.children
        return None
    
    @classmethod
    def evaluateExpression(cls, expression: DcrExpression, graph: DcrGraph, source: DcrElement=None, target: DcrElement=None) -> any:
        match expression.reference:
            case None:
                value = expression.attribute
            case "source":
                if source is not None:
                    value = cls.parseAttribute(source, expression.attribute, graph)
            case "target":
                if target is not None:
                    value = cls.parseAttribute(target, expression.attribute, graph)
            case id:
                value = cls.parseAttribute(graph.getActivityFromID(id), expression.attribute, graph)

        if value is not None and expression.operator is not None:
            match expression.operator:
                case "+":
                    return value + cls.evaluateExpression(expression.additional, graph, source, target)
                case "-":
                    return value - cls.evaluateExpression(expression.additional, graph, source, target)
                case "*":
                    return value * cls.evaluateExpression(expression.additional, graph, source, target)
                case "/":
                    return value / cls.evaluateExpression(expression.additional, graph, source, target)
                case "==":
                    return value == cls.evaluateExpression(expression.additional, graph, source, target)
                case "<":
                    return value < cls.evaluateExpression(expression.additional, graph, source, target)
                case ">":
                    return value > cls.evaluateExpression(expression.additional, graph, source, target)
                case "<=":
                    return value <= cls.evaluateExpression(expression.additional, graph, source, target)
                case ">=":
                    return value >= cls.evaluateExpression(expression.additional, graph, source, target)
                case "and":
                    return value and cls.evaluateExpression(expression.additional, graph, source, target)
                case "or":
                    return value or cls.evaluateExpression(expression.additional, graph, source, target)
                case "count":
                    return len(value)

        return value
    
    @classmethod
    def updateIncluded(cls, value: bool, element: DcrElement, graph: DcrGraph):
        element.included = value
        if isinstance(element, DcrNesting):
          for child in element.children:
              if not value:
                  child.parentsIncluded = False
              else:
                  child.parentsIncluded = True
                  parents = cls.getParents(child, graph)
                  for parent in parents:
                      child.parentsIncluded = child.parentsIncluded and parent.included
    
    @classmethod
    def updatePending(cls, value: bool, element: DcrElement, graph: DcrGraph):
        element.pending = value
        parents = cls.getParents(element, graph)
        for parent in parents:
            if value:
                parent.childrenPending = True
            else:
                parent.childrenPending = False
                for child in parent.children:
                    parent.childrenPending = parent.childrenPending or child.pending

    @classmethod
    def executeEvent(cls, event: DcrEvent, graph: DcrGraph):
        activity = graph.getActivity(event.ID)
        cls.execute(activity, graph, event.input)
    
    @classmethod
    def execute(cls, element: DcrActivity | DcrSubProcess, graph: DcrGraph, input=None):
        if element.takesInput:
            element.data = input
        elif element.expression is not None:
            element.data = cls.evaluateExpression(element.expression, graph)
        cls.updatePending(False, element, graph)
        element.executed = datetime.now()

        effects = cls.getEffects(element, graph)
        for r in effects:
            if r.guard is None or cls.evaluateExpression(r.guard, graph, element, r.target):
                cls.relateToTarget(r.target, r, graph)

        for parent in element.parents:
            if isinstance(parent, DcrSubProcess) and cls.isEnabled(parent, graph):
                cls.execute(parent, graph)
                break

    @classmethod
    def relateToTarget(cls, element: DcrElement, relation: DcrRelation, graph: DcrGraph):
        if isinstance(relation, DcrSpawn):
            relation.spawned += 1
            cls.spawn(element, graph, relation.spawned)

        elif type(element) is DcrNesting:
            for child in element.children:
                cls.relateToTarget(child, relation, graph)
        
        else:
            match relation.relationType:
                case RelationType.I:
                    cls.updateIncluded(True, element, graph)
                case RelationType.E:
                    cls.updateIncluded(False, element, graph)
                case RelationType.R:
                    cls.updatePending(True, element, graph)
                case RelationType.N:
                    cls.updatePending(False, element, graph)
                case RelationType.V:
                    element.data = relation.source.data
    
    @classmethod
    def spawn(cls, element: DcrElement, graph: DcrGraph, spawnNumber: int):
        elementDict = cls.spawnElements(element, graph, spawnNumber)

        for key in elementDict:
            incoming, outgoing = cls.getRelations(key, graph)
            for i in incoming:
                source = elementDict[i.source] if i.source in elementDict else i.source
                if i.relationType == RelationType.S:
                    graph.relations.add(DcrSpawn(source, elementDict[key], i.guard))
                    cls.makeTemplate(elementDict[key], graph)
                else:
                    graph.relations.add(DcrRelation(i.relationType, source, elementDict[key], i.guard))
            for o in outgoing:
                if o.target in elementDict:
                    continue
                graph.relations.add(DcrRelation(o.relationType, elementDict[key], o.target, o.guard))
        
        graph.elements.update(elementDict.values())

    @classmethod
    def spawnElements(cls, element: DcrElement, graph: DcrGraph, spawnNumber: int):
        spawns = {}

        if isinstance(element, DcrNesting):
            children = set()
            for child in element.children:
                spawns.update(cls.spawnElements(child, graph, spawnNumber))
                children.add(spawns[child])
            if type(element) is DcrNesting:
                spawns[element] = DcrNesting(element.ID + "S" + str(spawnNumber), children)
            elif type(element) is DcrSubProcess:
                spawns[element] = DcrSubProcess(element.ID + "S" + str(spawnNumber), set(children.values), template=element)
        else:
            spawns[element] = DcrActivity(element.ID + "S" + str(spawnNumber), template=element)

        return spawns
    
    @classmethod
    def makeTemplate(cls, element: DcrElement):
        element.isTemplate = True
        if isinstance(element, DcrNesting):
          for child in element.children:
              cls.makeTemplate(child)

    @classmethod
    def isAccepting(cls, graph: DcrGraph) -> bool:
        for e in graph.elements:
            if isinstance(e, DcrActivity) and e.included and not e.isTemplate and e.pending:
                return False
        return True