import sys
sys.path.insert(1, '/Users/timei/Documents/Datalogi/Semester6/Bachelor/pm4py-dcr')

from copy import deepcopy
from collections import defaultdict
from pm4py.objects.dcr import semantics as dcr_semantics

class IGraph:
    def __init__(self, dcr):
        self.dcr = dcr
        self.graph = {}
        self.from_dcr_to_graph()
        
        self.reachableGraph = {}
        self.create_reachable_graph(self.graph, self.reachableGraph)
        
        self.oppGraph = {}
        self.create_opp_graph()
        
        self.executeGraph = {}
        self.create_reachable_graph(self.oppGraph, self.executeGraph)
        self.topological_sort()
        
        # This list contain all the nodes related to a reponse deadline
        self.responseList = []
        self.create_list_deadlines()
        
    # This function add an edge between u and v in the graph g
    def add_edge(self, u, v, g):
        if u not in g:
            g[u] = []
            
        if v not in g[u]:
            g[u].append(v)
    
    # This function gives the list of events with potential deadline
    def create_list_deadlines(self):
        self.responseList.clear()
        for e in self.dcr['responseToDeadlines']:
            for (e_prime, k) in self.dcr['responseToDeadlines'][e]:
                self.responseList.append(e_prime)
            self.responseList.append(e)
    
    # This function creates the opposite relations in the self.dcr
    def create_opp_graph(self):
        self.oppGraph.clear()
        for e in self.graph:
            for e_prime in self.graph[e]:
                self.add_edge(e_prime, e, self.oppGraph)
    
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
    def reachable_nodes(self, v, recStack, graph, reachableGraph):
        # Appends the given event to the recusion stack
        recStack.append(v)
        
        # if v is in the graph then we know it has adjacent nodes
        if v in graph:
            for adjacent in graph[v]:
                for e in recStack:
                    self.add_edge(e, adjacent, reachableGraph)
                self.reachable_nodes(adjacent, recStack, graph, reachableGraph)
        
        # When we are done looking at the nodes adjacent nodes, 
        # then we need to remove it for the recursive stack
        recStack.remove(v)
        
    # Creates a reachable graph called self.reachableGraph, which is a 
    # dictionary containing every event and for each event is a list of
    # reachable events from the self.graph
    def create_reachable_graph(self, graph, reachableGraph):
        if not self.is_cyclic():
            reachableGraph.clear()
            
            # Gives the current nodes on the path
            recStack = []
            
            # Loops through every node in visited (which correnspond to every event in the dcr)
            for node in self.dcr['events']:
                self.reachable_nodes(node, recStack, graph, reachableGraph)
  
        else:
            print("Can not create reachable graph because the inhibitor graph contain cycles")
    
    # A recursive function used by topologicalSort
    def topological_sort_util(self, v, visited, stack):
 
        # Mark the current node as visited.
        visited[v] = True
 
        # Recur for all the vertices adjacent to this vertex
        if v in self.executeGraph:
            for i in self.executeGraph[v]:
                if visited[i] == False:
                    self.topological_sort_util(i, visited, stack)
        stack.append(v)
 
    # The function to do Topological Sort. It uses recursive
    # topologicalSortUtil()
    def topological_sort(self):
        for e in self.executeGraph:
            # Mark all the vertices as not visited
            visited = {}
            stack = []
            for e_prime in self.executeGraph[e]:
                visited[e_prime] = False
 
            # Call the recursive helper function to store Topological
            # Sort starting from all vertices one by one
            for i in visited:
                if visited[i] == False:
                    self.topological_sort_util(i, visited, stack)

            self.executeGraph[e] = stack
    
    
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
    
    def check_for_responses(self):
        for e in self.dcr['responseToDeadlines']:
            for (e_prime, k) in self.dcr['responseToDeadlines'][e]:
                if e_prime not in self.reachableGraph[e]:
                    return False
        for e in self.dcr['responseTo']:
            for e_prime in self.dcr['responseTo'][e]:
                if e_prime not in self.reachableGraph[e]:
                    return False
        for e in self.dcr['includesTo']:
            for e_prime in self.dcr['includesTo'][e]:
                if e_prime not in self.reachableGraph[e]:
                    return False
        return True
    
    def check_for_delays(self):
        for r in self.responseList:
            if r in self.executeGraph:
                for e in self.dcr['conditionsForDelays']:
                    if e in self.executeGraph[r] or e == r:
                        return False 
        return True

        
class Enforcement_mechanisme:
    def __init__(self, dcr):
        self.dcr = dcr
        self.iGraph = IGraph(dcr)
    
    # This function checks if the dcr graph is enforceable
    # based on definition 60 in Proactive enforcement
    def is_enforceable(self):
        return not self.iGraph.is_cyclic() and self.iGraph.check_for_responses() and self.iGraph.check_for_delays()
    
    # The function either deny or grant 
    def peform_controllable_event(self, event):
        if dcr_semantics.is_enabled(event, self.dcr):
            dcr_semantics.execute(event, self.dcr)
            return "Grant"
        return "Deny"
    
    def get_urgent_deadlines(self):
        urgentDeadlines = []
        for e in self.dcr['marking']['pendingDeadline']:
            if self.dcr['marking']['pendingDeadline'][e] == 0:
                urgentDeadlines.append(e)
        return urgentDeadlines
    
    # This function return a list of events which must be executed
    def check_urgent_deadlines(self):
        urgentDeadlines = self.get_urgent_deadlines()
        executeList = []
        if len(urgentDeadlines) > 0:
            for e in urgentDeadlines:
                if e not in executeList:
                    #print("e: " + e)
                    print(e + " " + str(dcr_semantics.is_enabled(e, self.dcr)))
                    if dcr_semantics.is_enabled(e, self.dcr):
                        dcr_semantics.execute(e, self.dcr)
                        executeList.append(e)
                        print("the urgent event " + e + " is now executed")
                    else:
                        for e_prime in self.iGraph.executeGraph[e]:
                            print("e_prime: " + e_prime)
                            #print("Im here with e: " + e)
                            if e_prime in self.dcr['marking']['pending'] or e_prime not in self.dcr['marking']['executed']:
                                dcr_semantics.execute(e_prime, self.dcr)
                                executeList.append(e_prime)
                                print(e_prime, "is now executed")
                        dcr_semantics.execute(e, self.dcr)
                        executeList.append(e)
                        print("the urgent event " + e + " is now executed")
        return executeList
                    
            
            
            
            
            
        
        
        