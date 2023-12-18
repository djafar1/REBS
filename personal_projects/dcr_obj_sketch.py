from pm4py.objects.dcr.obj import *

# working ideas on how DCR objects should look like in pm4py

# graphs and events as objects (marking inside events)
graph = DCRGraph()
# markings can be 0/1 or True/False
event_A = Event(id='A',label='A',parent=None,children=None,marking=Marking(0,1,0))
event_B = Event('B','B',None, None,Marking(False,True,False))
graph.add_event(event=event_A)
graph.add_event(event_B)
# behind this method it will create a event object
graph.add_event(id='D',label='D',marking=Marking(False,True,False))

# should be the same event can be retrieved by unique id (name)
print(event_A == graph.get_event('A'))
print(event_B == graph.get_event('B'))

# several ways to add a relation
graph.add_condition(src=event_A,trg=event_B)
graph.add_condition('A','B')
# relations are weak entities (cannot exist without their events so they are not objects at the moment.
# if we mimic the petri net obj.py we need an object for relations to, this might make sense if we want to
# support advanced guards and not only time.

# delays and deadlines added on the relation
graph.add_condition(event_A, event_B,delay=20)
graph.add_response(event_A,event_B,deadline=30)

# execution semantics embedded in the objects
graph.get_event('A').enabled()
graph.get_event(event_A).execute()
# decide if ticks are int or timedelta objects
print(graph.can_time_step(ticks=35))
graph.time_step(ticks=25)
graph.get_event('B').canExecute()
graph.execute('B')
print(graph.has_event(event_B))
graph.is_accepting()
print(graph.get_event('C').marking)

# can replace an event with another. what happens with the execution semantics?
event_C = Event('C','C',None, None)
graph.replace_event(event_B, event_C)

# subprocesses and nestings can be parents and children of their respective events
# the parent/children assignment should be immediately reflected in the respective child/parent
# the child is also part of the graph its parent is a part of
event_E = Event('E','E',parent=event_C,type=Enum.Subprocess)
# or alternatively (add_parent takes exactly one event
event_E.add_parent(parent=event_C,type=Enum.Subprocess)
# or alternatively (add_children should take a list)
event_C.add_children(children=[event_E],type=Enum.Subprocess)

# can be a nesting
event_C.add_children(children=[event_E],type=Enum.Nesting)

# subprocesses and nestings can be a hierarchy of events or a dcr graph within a dcr graph (sub graphs and parent graphs)?
sub_graph = DCRGraph(parent_graph=graph)
sub_graph.add_event(Event('D','D',None,None,Marking(0,1,0)))

# there should be a base DCRGraph object and all extensions build on that object. Which hierarchies make the most sense?
dcr_basic = DCRGraph()
dcr_subprocess = DCRGraphSubprocess() # extends from basic
dcr_subprocess_nesting = DCRGraphNesting() # note extends from subprocess
dcr_spawn = DCRGraphSpawn() # extends from basic
# all other extensions, with roles, spawn etc... take the same structure
# summaries should be printed accordingly in the __str__ method (to string)
# visualisations can be done similarly as for petri nets (would be cool if we can make dcr marking visible)
