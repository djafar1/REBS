import os
os.chdir('C:/Users/timei/Documents/Datalogi/Semester6/Bachelor/pm4py-dcr')

from copy import deepcopy
from collections import defaultdict
from pm4py.objects.dcr import semantics as dcr_semantics

class IGraph:
    def __init__(self, dcr):
        self.dcr = dcr
        self.graph = {}
        self.from_dcr_to_graph()
        
        self.reachableGraph = {}
        self.create_reachable_graph()
    
    # This function add an edge between u and v in the graph g
    def add_edge(self, u, v, g):
        if u not in g:
            g[u] = []
            
        if v not in g[u]:
            g[u].append(v)
    
    # This function transform self.dcr to a directed graph containing
    # only conditions and milestones as relations
    def from_dcr_to_graph(self):
        self.graph.clear()
        for e in self.dcr['conditionsFor']:
            for e_prime in self.dcr['conditionsFor'][e]:
                self.add_edge(e_prime, e, self.graph)
   
        for e in self.dcr['conditionsForDelays']:        
            for (e_prime, k) in self.dcr['conditionsForDelays'][e]:
                self.add_edge(e_prime, e, self.graph)
                
        for e in self.dcr['milestonesFor']:
            for e_prime in self.dcr['milestonesFor'][e]:
                self.add_edge(e_prime, e, self.graph)
    
    # This method is used in create_reachable_graph such that we can
    # find every reachable event (node) from the corresponding event
    def reachable_nodes(self, v, visited, recStack):
        # Marks the event as visited
        visited[v] = True
        
        # Appends the given event to the recusion stack
        recStack.append(v)
        
        # if v is in the graph then we know it has adjacent nodes
        if v in self.graph:
            for adjacent in self.graph[v]:
                
                # If the current adjacent node is not visited then
                # we add the adjacent node to every node in recStack
                # and recursivly call the function on the adjacent node
                if visited[adjacent] == False:
                    for e in recStack:
                        self.add_edge(e, adjacent, self.reachableGraph)
                    self.reachable_nodes(adjacent, visited, recStack)
                
                # If we have already visited the adjacent node then we add
                # every reachable node from the adjacent node plus it self
                elif visited[adjacent] == True:
                    if adjacent in self.reachableGraph:
                        for e in self.reachableGraph[adjacent]:
                            self.add_edge(v, e, self.reachableGraph)
                    self.add_edge(v, adjacent, self.reachableGraph)
        
        # When we are done looking at the nodes adjacent nodes, 
        # then we need to remove it for the recursive stack
        recStack.remove(v)
        
    # Creates a reachable graph called self.reachableGraph, which is a 
    # dictionary containing every event and for each event is a list of
    # reachable events from the self.graph
    def create_reachable_graph(self):
        if not self.is_cyclic():
            self.reachableGraph.clear()
            visited = {}
            
            # Gives the current nodes on the path
            recStack = []
            
            # Instantiate every visited events as false
            for e in self.dcr['events']:
                visited[e] = False
            
            # Loops through every node in visited (which correnspond to every event in the dcr)
            for node in visited:
                if visited[node] == False:
                    self.reachable_nodes(node, visited, recStack)
  
        else:
            print("Can not create reachable graph because the inhibitor graph contain cycles")
    
    # This method is a helper function for is_cyclic used to find cycles
    def is_cyclic_util(self, v, visited, recStack):
        
        # Mark current node as visited and
        # adds to recursion stack
        visited[v] = True
        recStack[v] = True
        
        # Recur for all neighbours
        # if any neighbour is visited and in
        # recStack then graph is cyclic
        if v in self.graph:
            for adjacent in self.graph[v]:
                if visited[adjacent] == False:
                    if self.is_cyclic_util(adjacent, visited, recStack) == True:
                        return True
                elif recStack[adjacent] == True:
                    return True
        
        # The node needs to be popped from
        # recursion stack before function ends
        recStack[v] = False
        return False
    
    # This function return true if self.graph contains cycles, otherwise false is returned
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
    
    # This function checks if repsonses and includes to relations
    # is reachable in self.reachableGraph, and return false if it holds
    def check_for_responses(self):
        for e in self.dcr['responseToDeadlines']:
            for (e_prime, k) in self.dcr['responseToDeadlines'][e]:
                if e_prime not in self.reachableGraph[e]:
                    return True
        for e in self.dcr['responseTo']:
            for e_prime in self.dcr['responseTo'][e]:
                if e_prime not in self.reachableGraph[e]:
                    return True
        for e in self.dcr['includesTo']:
            for e_prime in self.dcr['includesTo'][e]:
                if e_prime not in self.reachableGraph[e]:
                    return True
        return False
    
    # This function checks if a given node (event) has a deadline
    # and a delay, and return true if so, otherwise false is returned
    def check_for_delays(self):
        for e in self.dcr['conditionsForDelays']:
            for e_prime in self.dcr['responseToDeadlines']:
                for (adjacent, k) in self.dcr['responseToDeadlines'][e_prime]:
                    if adjacent == e:
                        return True
        return False           

class Enforcement_mechanisme:
    def __init__(self, dcr):
        self.dcr = dcr
        self.iGraph = IGraph(dcr)
    
    # This function checks if the dcr graph is enforceable
    # based on definition 60 in Proactive enforcement
    def is_enforceable(self):
        return not (self.iGraph.is_cyclic() or self.iGraph.check_for_responses() or self.iGraph.check_for_delays())
    
    # Ths function either deny or grant 
    def peform_controllable_event(self, event):
        if dcr_semantics.is_enabled(event, self.dcr):
            dcr_semantics.execute(event, self.dcr)
            return "Grant"
        return "Deny"
    
    # This function return a list of urgent events which must be executed
    def check_urgent_deadlines(self):
        urgentDeadlines = []
        for e in self.dcr['marking']['pendingDeadline']:
            if self.dcr['marking']['pendingDeadline'][e] == 0:
                urgentDeadlines.append(e)
        return urgentDeadlines
                    
            
            
            
            
            
        
        
        