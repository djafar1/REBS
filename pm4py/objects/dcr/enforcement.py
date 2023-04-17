import os
os.chdir('C:/Users/timei/Documents/Datalogi/Semester6/Bachelor/pm4py-dcr')

from copy import deepcopy
from collections import defaultdict
from pm4py.objects.dcr import semantics as dcr_semantics

class IGraph:
    def __init__(self):
        self.graph = defaultdict(list)
        
    def add_edge(self, u, v):
        self.graph[u].append(v)
        
    def from_dcr_to_graph(self, dcr):
        self.graph.clear()
        self.dcr = dcr
        for e in dcr['events']:
         
            if e in dcr['conditionsFor']:
                for e_prime in dcr['conditionsFor'][e]:
                    self.add_edge(e_prime, e)
   
            if e in dcr['conditionsForDelays']:        
                for (e_prime, k) in dcr['conditionsForDelays'][e]:
                    self.add_edge(e_prime, e)
                
            if e in dcr['milestonesFor']:
                for e_prime in dcr['milestonesFor'][e]:
                    self.add_edge(e_prime, e)
    
    # This method is a helper function for is_cyclic used to find cycles
    def is_cyclic_util(self, v, visited, recStack):
        visited[v] = True
        recStack[v] = True
        
        for neighbour in self.graph[v]:
            if visited[neighbour] == False:
                if self.is_cyclic_util(neighbour, visited, recStack) == True:
                    return True
            elif recStack[neighbour] == True:
                return True
        
        recStack[v] = False
        return False
    
    # This method is called when checking for cycles in the directed graph
    def is_cyclic(self):
        visited = {}
        recStack = {}
        for e in self.dcr['events']:
            visited[e] = False
            recStack[e] = False
        for node in visited:
            if visited[node] == False:
                if self.is_cyclic_util(node, visited, recStack) == True:
                    return True
        return False
        
    # This method checks if the inhibitor graph contain responses or include
    # relations in the opposite direction
    def check_for_responses(self):
        for e in self.graph:
            for e_prime in self.graph[e]:
                if e_prime in self.dcr['responseToDeadlines']:
                    if e in self.dcr['responseToDeadlines'][e_prime]:
                        return True
                if e_prime in self.dcr['responseTo']:
                    if e in self.dcr['responseTo'][e_prime]:
                        return True
                if e_prime in self.dcr['includesTo']:
                    if e in self.dcr['includesTo'][e_prime]:
                        return True
        return False
    
    def check_for_delay(self):      
                               

class Enforcement_mechanisme:
    def __init__(self, dcr):
        self.dcr = dcr
        self.i_graph = IGraph()
        self.i_graph.from_dcr_to_graph(dcr)
    
    def is_enforceable(self):
        if i_graph.is_cyclic() or i_graph.check_for_responses() or i_graph.check_for_dekay():
            return False
        return True
            
            
            
            
        
        
        