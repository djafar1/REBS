from typing import Set

from pm4py.objects.dcr.extended.semantics import ExtendedSemantics

class HierarchicalSemantics(ExtendedSemantics):
    @classmethod
    def enabled(cls, graph) -> Set[str]:
        #Reuses the enabled from milestone and dcr
        #Removing the ones with a active condition, and milestone
        res = super().enabled(graph)
        print
        
        return res

    
    @classmethod
    def execute(cls, graph, event):
    
        
        return graph
