from typing import Set

from pm4py.objects.dcr.extended.semantics import ExtendedSemantics

class HierarchicalSemantics(ExtendedSemantics):
    @classmethod
    def enabled(cls, graph) -> Set[str]:
        #Reuses the enabled from milestone and dcr
        #Removing the ones with a active condition, and milestone
        print("Included:", graph.marking.included)
        print("Pending:", graph.marking.pending)
        res = super().enabled(graph)   
          
        def nest_checker(nest):
            for e in graph.nestedgroups[nest]:
                if e in graph.nestedgroups:
                    if nest_checker(e):
                        return True
                elif e in graph.marking.included.difference(graph.marking.executed): #Checks if included is not executed
                    return True
            return False 
          
        def recursive_handle_nests(nest):
            for e in graph.nestedgroups[nest]:
                if e in graph.nestedgroups:
                    recursive_handle_nests(e)
                res.discard(e)

        for nest in set(graph.conditions.keys()).intersection(graph.nestedgroups): # N1 OG N3
            for cond in graph.conditions[nest]: #N1 condionted A , N3 conditioned N1
                if cond in graph.nestedgroups:
                    # iF THe condition pointing twoards the nest is a nested group we check if its executed and included
                    # if not it returns true and we discard everything in the nest, as the condition is not done
                    if nest_checker(cond): 
                        recursive_handle_nests(nest)
                elif cond in graph.marking.included.difference(graph.marking.executed): # If the condition is a event and not executed remove all events
                    recursive_handle_nests(nest)      
                                  
        """
        def recursive_handle_nests(graph, nest):
            for e in graph.nestedgroups[nest]:
                if e in graph.nestedgroups:
                    recursive_handle_nests(graph, e)
                else:
                    if e in graph.marking.included.difference(graph.marking.executed):
                        res.discard(e)
        #If a nest has an active condition we remove all the events inside
        for nest in set(graph.conditions.keys()).intersection(graph.nestedgroups):
            condition_nest = graph.conditions[nest] # conditions to the current nest
            for cond in condition_nest:
                if cond not in graph.marking.executed:
                    recursive_handle_nests(graph, nest)
                if cond in graph.nestedgroups:
                    if any()
        """       
        print("Enabled:", res)
        return res
    @classmethod
    def execute(cls, graph, event):
        if event in graph.marking.pending:
            graph.marking.pending.discard(event)
        graph.marking.executed.add(event)

        #Excludes whole nest
        def nest_exclude(nest):
            for event in graph.nestedgroups[nest]:
                if event in graph.nestedgroups:
                    nest_exclude(event)
                else:
                    graph.marking.included.discard(event)      
        #Includes everything in the nest            
        def nest_include(nest):
            for event in graph.nestedgroups[nest]:
                if event in graph.nestedgroups:
                    nest_include(event)
                else:
                    graph.marking.included.add(event)
        #RESPOns the whole nest
        def nest_respons(nest):
            for event in graph.nestedgroups[nest]:
                if event in graph.nestedgroups:
                    nest_respons(event)
                else:
                    graph.marking.pending.add(event)    
                    
        ###Copied from semantics.py in Dcr and just added if to check if the event is a nest        
        if event in graph.excludes:
            for e_prime in graph.excludes[event]:
                if e_prime in graph.nestedgroups:
                    nest_exclude(e_prime)
                else:
                    graph.marking.included.discard(e_prime)
        if event in graph.includes:
            for e_prime in graph.includes[event]:
                if e_prime in graph.nestedgroups:
                    nest_include(e_prime)
                else:
                    graph.marking.included.add(e_prime)
        if event in graph.responses:
            for e_prime in graph.responses[event]:
                if e_prime in graph.nestedgroups:
                    nest_respons(e_prime)
                else:
                    graph.marking.pending.add(e_prime)      
        ###Checks if the event is in the events of a nest and the nest is either exluces, includes, or response, and 
        ###then goes through all of the events in the nest and either excludes, includes and response.   
        for nest, events in graph.nestedgroups.items():
                if event in events and nest in graph.excludes:
                    for e_prime in graph.excludes[nest]:
                        if e_prime in graph.nestedgroups:
                            nest_exclude(e_prime)
                        else:
                            graph.marking.included.discard(e_prime)
                if event in events and nest in graph.includes:
                    for e_prime in graph.includes[nest]:
                        if e_prime in graph.nestedgroups:
                            nest_include(e_prime)
                        else:
                            graph.marking.included.add(e_prime)
                if event in events and nest in graph.responses:
                    for e_prime in graph.responses[nest]:
                        if e_prime in graph.nestedgroups:
                            nest_respons(e_prime)
                        else:
                            graph.marking.pending.add(e_prime)
        return graph