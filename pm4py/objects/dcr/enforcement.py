import sys
sys.path.insert(1, '/Users/timei/Documents/Datalogi/Semester6/Bachelor/pm4py-dcr')

from copy import deepcopy
from collections import defaultdict
from pm4py.objects.dcr import semantics as dcr_semantics

class IGraph:
    def __init__(self, dcr):
        self.dcr = dcr
        self.graph = self.from_dcr_to_graph()
        self.oppGraph = self.create_opp_graph(self.graph)

        self.graph = self.from_graph_to_igraph()
        #print("Igraph: " + str(self.graph))
        self.eventsInIgraph = self.find_events_in_graph(self.graph)
        #print("eventsInIgraph: " + str(self.eventsInIgraph))

        self.reachableGraph = self.create_reachable_graph(self.graph)
        #print("reachableGraph: " + str(self.reachableGraph))

        self.oppGraph = self.create_opp_graph(self.graph)
        self.executeGraph = self.create_reachable_graph(self.oppGraph)
        self.topological_sort()
        #print("executeGraph: " + str(self.executeGraph))
        #print("oppGrapg: " + str(self.oppGraph))
        
    # This function add an edge between u and v in the graph g
    # if the edge does not exist in the graph
    def add_edge(self, u, v, g):
        if u not in g:
            g[u] = []
            
        if v not in g[u]:
            g[u].append(v)
    
    # This function returns a graph with the opposite relations
    def create_opp_graph(self, graph):
        oppGraph = {}
        for e in graph:
            for e_prime in graph[e]:
                self.add_edge(e_prime, e, oppGraph)
        return oppGraph
    
    # This function transform self.dcr to a directed graph containing
    # only conditions and milestones relations and return the graph
    def from_dcr_to_graph(self):
        graph = {}
        for e in self.dcr['conditionsFor']:
            for e_prime in self.dcr['conditionsFor'][e]:
                self.add_edge(e_prime, e, graph)
   
        for e in self.dcr['conditionsForDelays']:        
            for (e_prime, k) in self.dcr['conditionsForDelays'][e]:
                self.add_edge(e_prime, e, graph)
                
        for e in self.dcr['milestonesFor']:
            for e_prime in self.dcr['milestonesFor'][e]:
                self.add_edge(e_prime, e, graph)
        
        return graph

    # This function is a helper function for from_graph_to_igraph
    def from_graph_to_igraph_util(self, v, graph):
        if v in self.oppGraph:
            for e in self.oppGraph[v]:
                self.add_edge(e, v, graph)
                self.from_graph_to_igraph_util(e, graph)

    # This function uses self.graph to create an inhibitor graph
    # if the inhibitor graph does not contain cycles the inhibitor graph is returned
    # otherwise the condition and milestone graph are returned to show it violates enforceable
    def from_graph_to_igraph(self):
        if not self.is_cyclic():
            busyEvents = self.find_busy_events()
            newGraph = {}

            for e in busyEvents:
                self.from_graph_to_igraph_util(e, newGraph)

            return newGraph
        return self.graph
    
    # This function returns a list with all the events in the graph
    def find_events_in_graph(self, graph):
        events = []
        for e in graph:
            for e_prime in graph[e]:
                if e_prime not in events:
                    events.append(e_prime)
            if e not in events:
                events.append(e)
        return events

    # This function returns a list with all the busy events, which
    # is all the events that can be pending
    def find_busy_events(self):
        busyEvents = []
        for e in self.dcr['responseTo']:
            for e_prime in self.dcr['responseTo'][e]:
                if e_prime not in busyEvents:
                    busyEvents.append(e_prime)

        for e in self.dcr['responseToDeadlines']:
            for (e_prime, k) in self.dcr['responseToDeadlines'][e]:
                if e_prime not in busyEvents:
                    busyEvents.append(e_prime)

        for e in self.dcr['marking']['pending']:
            if e not in busyEvents:
                busyEvents.append(e)

        return busyEvents


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
        
    # Creates a reachable graph based on the graph, which is a 
    # dictionary containing every event and for each event is a list of
    # reachable events from the graph
    def create_reachable_graph(self, graph):
        reachableGraph = {}
        eventsInGraph = self.find_events_in_graph(graph)
        if not self.is_cyclic():

            # Gives the current nodes on the path
            recStack = []
            
            # Loops through every node in visited (which correnspond to every event in the dcr)
            for node in eventsInGraph:
                self.reachable_nodes(node, recStack, graph, reachableGraph)
  
        else:
            print("Can not create reachable graph because the inhibitor graph contain cycles")

        return reachableGraph
    
    # A recursive function used by topologicalSort
    def topological_sort_util(self, v, visited, stack):
 
        # Mark the current node as visited.
        visited[v] = True
 
        # Recur for all the vertices adjacent to this vertex
        if v in self.oppGraph:
            for i in self.oppGraph[v]:
                if visited[i] == False:
                    self.topological_sort_util(i, visited, stack)
        stack.append(v)
 
    # The function does Topological Sort on self.executeGraph
    def topological_sort(self):
        if self.is_cyclic() == False:
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
        # if any adjacent is visited and in
        # recStack then graph is cyclic
        if v in self.oppGraph:
            for adjacent in self.oppGraph[v]:
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
        busyEvents = self.find_busy_events()

        for e in self.dcr['events']:
            visited[e] = False
            recStack[e] = False

        for node in busyEvents:
            if visited[node] == False:
                if self.is_cyclic_util(node, visited, recStack) == True:
                    return True
        return False
    
    # This funktion checks if there is a path from e to f, if there is a include or 
    # response relation in the inhibitor graph. True if this is the case for every relation
    # otherwise false is returned
    def check_for_responses(self):
        for e in self.dcr['responseToDeadlines']:
            for (e_prime, k) in self.dcr['responseToDeadlines'][e]:
                if e in self.eventsInIgraph and e_prime in self.eventsInIgraph:
                    if (e in self.reachableGraph and e_prime not in self.reachableGraph[e]) or e not in self.reachableGraph:
                        return False
        for e in self.dcr['responseTo']:
            for e_prime in self.dcr['responseTo'][e]:
                if e in self.eventsInIgraph and e_prime in self.eventsInIgraph:
                    if (e in self.reachableGraph and e_prime not in self.reachableGraph[e]) or e not in self.reachableGraph:
                        return False
        for e in self.dcr['includesTo']:
            for e_prime in self.dcr['includesTo'][e]:
                if e in self.eventsInIgraph and e_prime in self.eventsInIgraph:
                    if (e in self.reachableGraph and e_prime not in self.reachableGraph[e]) or e not in self.reachableGraph:
                        return False
        return True
    
    # This function checks if there is any delay in the inhibitor graph.
    # If there is a delay false is returned otherwise true is returned
    def check_for_delays(self):
        for e in self.dcr['conditionsForDelays']:
            if e in self.eventsInIgraph:
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
    
    # The function either deny or grant an event
    def perform_controllable_event(self, event):
        if dcr_semantics.is_enabled(event, self.dcr):
            dcr_semantics.execute(event, self.dcr)
            return "Grant"
        return "Deny"
    
    # This function return a list with all the urgent events
    # which must be executed now
    def get_urgent_deadlines(self):
        urgentDeadlines = []
        for e in self.dcr['marking']['pendingDeadline']:
            if self.dcr['marking']['pendingDeadline'][e] == 0:
                urgentDeadlines.append(e)
        return urgentDeadlines
    
    # This function returns a list of events that must be executed
    def check_urgent_deadlines(self):
        if self.is_enforceable():
            urgentDeadlines = self.get_urgent_deadlines()
            executeList = []
            if len(urgentDeadlines) > 0:
                for e in urgentDeadlines:
                    if e not in executeList:
                        if dcr_semantics.is_enabled(e, self.dcr):
                            dcr_semantics.execute(e, self.dcr)
                            executeList.append(e)
                        else:
                            for e_prime in self.iGraph.executeGraph[e]:
                                if e_prime in self.dcr['marking']['pending'] or (e_prime not in self.dcr['marking']['executed'] and e_prime in self.dcr['marking']['included']):
                                    dcr_semantics.execute(e_prime, self.dcr)
                                    executeList.append(e_prime)
                            dcr_semantics.execute(e, self.dcr)
                            executeList.append(e)
            return executeList
        return []
                    
            
            
            
            
            
        
        
        