import tkinter as tk
from tkinter import ttk

import sys
sys.path.insert(1, '/Users/timei/Documents/Datalogi/Semester6/Bachelor/pm4py-dcr')

#import os
#os.chdir('C:/Users/timei/Documents/Datalogi/Semester6/Bachelor/pm4py-dcr')

from pm4py.objects.dcr import enforcement as dcr_enforcement
from pm4py.objects.dcr import semantics as dcr_semantics

# DCR Hospital example
dcr = {
    'events': {'release', 'archive', 'delete', 'readmit', 'unarchive'},
    'labels': set(),
    'labelMapping': set(),
    'conditionsFor': {'delete': {'release'}, 'unarchive':{'release'}, 'archive':{'release'}},  # this should be a dict with events as keys and sets as values
    'milestonesFor': {'delete': {'archive'}},
    'responseTo': {},
    'noResponseTo': {},
    'includesTo': {'release':{'archive', 'delete', 'unarchive'}},
    'excludesTo': {'readmit':{'unarchive', 'archive', 'delete'}},
    'conditionsForDelays': {'unarchive':{('archive', 2920)}},  # this should be a dict with events as keys and tuples as values
    'responseToDeadlines': {'release':{('archive', 14), ('delete', 14)}},
    'marking': {'executed': set(),
                'included': {'release', 'archive', 'delete', 'readmit', 'unarchive'},
                'pending': set(),
                'executedTime': {}, # Gives the time since a event was executed
                'pendingDeadline': {} # The deadline until an event must be executed 
                }
}

# DCR example with an inhibitor graph with cycles
dcr_cyclic_inhib = {
    'events': {'release', 'archive', 'delete', 'readmit', 'unarchive'},
    'labels': set(),
    'labelMapping': set(),
    'conditionsFor': {'release': {'delete'}, 'unarchive':{'release'}, 'archive':{'release'}},  # this should be a dict with events as keys and sets as values
    'milestonesFor': {'delete': {'archive'}},
    'responseTo': {},
    'noResponseTo': {},
    'includesTo': {'release':{'archive', 'delete', 'unarchive'}},
    'excludesTo': {'readmit':{'unarchive', 'archive', 'delete'}},
    'conditionsForDelays': {'unarchive':{('archive', 2920)}},  # this should be a dict with events as keys and tuples as values
    'responseToDeadlines': {'release':{('archive', 14), ('delete', 14)}},
    'marking': {'executed': set(),
                'included': {'release', 'archive', 'delete', 'readmit', 'unarchive'},
                'pending': set(),
                'executedTime': {}, # Gives the time since a event was executed
                'pendingDeadline': {} # The deadline until an event must be executed 
                }
}

# DCR example where a response relation points to itself
dcr_response_cycle_inhib = {
    'events': {'release', 'archive', 'delete', 'readmit', 'unarchive'},
    'labels': set(),
    'labelMapping': set(),
    'conditionsFor': {'delete': {'release'}, 'unarchive':{'release'}, 'archive':{'release'}},  # this should be a dict with events as keys and sets as values
    'milestonesFor': {'delete': {'archive'}},
    'responseTo': {'archive':{'archive'}},
    'noResponseTo': {},
    'includesTo': {'release':{'archive', 'delete', 'unarchive'}},
    'excludesTo': {'readmit':{'unarchive', 'archive', 'delete'}},
    'conditionsForDelays': {'unarchive':{('archive', 2920)}},  # this should be a dict with events as keys and tuples as values
    'responseToDeadlines': {'release':{('archive', 14), ('delete', 14)}},
    'marking': {'executed': set(),
                'included': {'release', 'archive', 'delete', 'readmit', 'unarchive'},
                'pending': set(),
                'executedTime': {}, # Gives the time since a event was executed
                'pendingDeadline': {} # The deadline until an event must be executed 
                }
}

# DCR example where the response arrow points to a previous executed event
dcr_response_inhib = {
    'events': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'activity5'},
    'labels': set(),
    'labelMapping': set(),
    'conditionsFor': {'delete': {'release', 'activity5'}, 'unarchive':{'release'}, 'activity5':{'archive'}, 'archive':{'release'}},  # this should be a dict with events as keys and sets as values
    'milestonesFor': {'delete': {'archive'}},
    'responseTo': {'activity5': {'release'}},
    'noResponseTo': {},
    'includesTo': {'release':{'archive', 'delete', 'unarchive'}},
    'excludesTo': {'readmit':{'unarchive', 'archive', 'delete'}},
    'conditionsForDelays': {'unarchive':{('archive', 2920)}},  # this should be a dict with events as keys and tuples as values
    'responseToDeadlines': {'release':{('archive', 14), ('delete', 14)}},
    'marking': {'executed': set(),
                'included': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'activity5'},
                'pending': set(),
                'executedTime': {}, # Gives the time since a event was executed
                'pendingDeadline': {} # The deadline until an event must be executed 
                }
}

# DCR example where the includeTo relation points to a previous executed event
dcr_includes_inhib = {
    'events': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'activity5'},
    'labels': set(),
    'labelMapping': set(),
    'conditionsFor': {'delete': {'release', 'activity5'}, 'unarchive':{'release'}, 'activity5':{'archive'}, 'archive':{'release'}},  # this should be a dict with events as keys and sets as values
    'milestonesFor': {'delete': {'archive'}},
    'responseTo': {},
    'noResponseTo': {},
    'includesTo': {'release':{'archive', 'delete', 'unarchive'}, 'delete':{'archive'}},
    'excludesTo': {'readmit':{'unarchive', 'archive', 'delete'}},
    'conditionsForDelays': {'unarchive':{('archive', 2920)}},  # this should be a dict with events as keys and tuples as values
    'responseToDeadlines': {'release':{('archive', 14), ('delete', 14)}},
    'marking': {'executed': set(),
                'included': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'activity5'},
                'pending': set(),
                'executedTime': {}, # Gives the time since a event was executed
                'pendingDeadline': {} # The deadline until an event must be executed 
                }
}

# DCR example where there is a delay in the inhibitor graph
dcr_delay_inhib = {
    'events': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'a', 'b'},
    'labels': set(),
    'labelMapping': set(),
    'conditionsFor': {'delete': {'release', 'a'}, 'unarchive':{'release'}, 'archive':{'release'}, 'a':{'archive'}},  # this should be a dict with events as keys and sets as values
    'milestonesFor': {'delete': {'archive'}},
    'responseTo': {},
    'noResponseTo': {},
    'includesTo': {'release':{'archive', 'delete', 'unarchive'}},
    'excludesTo': {'readmit':{'unarchive', 'archive', 'delete'}},
    'conditionsForDelays': {'unarchive':{('archive', 2920)}, 'a':{('b', 200)}},  # this should be a dict with events as keys and tuples as values
    'responseToDeadlines': {'release':{('archive', 14), ('delete', 14)}},
    'marking': {'executed': set(),
                'included': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'a', 'b'},
                'pending': set(),
                'executedTime': {}, # Gives the time since a event was executed
                'pendingDeadline': {} # The deadline until an event must be executed 
                }
} 

# DCR example where there is a cycle in the condition and milestone graph
# but not in the inihibitor graph
dcr_1 = {
    'events': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'activity5', 'a', 'b'},
    'labels': set(),
    'labelMapping': set(),
    'conditionsFor': {'delete': {'release', 'activity5'}, 'unarchive':{'release'}, 'activity5':{'archive'}, 'archive':{'release'}, 'a':{'activity5'}, 'b':{'delete'}, 'a':{'b'}, 'b':{'a'}},  # this should be a dict with events as keys and sets as values
    'milestonesFor': {'delete': {'archive'}},
    'responseTo': {},
    'noResponseTo': {},
    'includesTo': {'release':{'archive', 'delete', 'unarchive'}},
    'excludesTo': {'readmit':{'unarchive', 'archive', 'delete'}},
    'conditionsForDelays': {'unarchive':{('archive', 2920)}},  # this should be a dict with events as keys and tuples as values
    'responseToDeadlines': {'release':{('archive', 14), ('delete', 14)}},
    'marking': {'executed': set(),
                'included': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'activity5', 'a', 'b'},
                'pending': set(),
                'executedTime': {}, # Gives the time since a event was executed
                'pendingDeadline': {} # The deadline until an event must be executed 
                }
}

# DCR example where there is more depended events on delete
# to show the proactive enforcement works as exepcted
dcr_2 = {
    'events': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'activity5', 'a', 'b'},
    'labels': set(),
    'labelMapping': set(),
    'conditionsFor': {'delete': {'release', 'activity5', 'b'}, 'unarchive':{'release'}, 'activity5':{'archive'}, 'archive':{'release'}, 'a':{'activity5'}, 'b':{'a'}},  # this should be a dict with events as keys and sets as values
    'milestonesFor': {'delete': {'archive'}},
    'responseTo': {},
    'noResponseTo': {},
    'includesTo': {'release':{'archive', 'delete', 'unarchive'}},
    'excludesTo': {'readmit':{'unarchive', 'archive', 'delete'}},
    'conditionsForDelays': {'unarchive':{('archive', 2920)}},  # this should be a dict with events as keys and tuples as values
    'responseToDeadlines': {'release':{('archive', 14), ('delete', 14)}},
    'marking': {'executed': set(),
                'included': {'release', 'archive', 'delete', 'readmit', 'unarchive', 'activity5', 'a', 'b'},
                'pending': set(),
                'executedTime': {}, # Gives the time since a event was executed
                'pendingDeadline': {} # The deadline until an event must be executed 
                }
}

# Change the input in the enforcement mechanism with one of the above dcr graphs
enforcement = dcr_enforcement.Enforcement_mechanisme(dcr)
dict_exe = dcr_semantics.create_max_executed_time_dict(enforcement.dcr)

window = tk.Tk()

# Specify Grid
tk.Grid.rowconfigure(window,0,weight=1)
tk.Grid.columnconfigure(window,0,weight=1)
tk.Grid.rowconfigure(window,1,weight=1)

#window.geometry("1920x1080")
window.title("Hospital Targetsystem")

scrollbar = tk.Scrollbar(window)
scrollbar.grid(row=0, column=1, sticky="news")

mylist = tk.Listbox(window, yscrollcommand= scrollbar.set)

mylist.grid(row=0, column=0, sticky="news")
scrollbar.config(command = mylist.yview)

# This function is called every time a line is inserted into the listbox
def insert_line(text):
    if type(text) is tuple:
        if text[0]:
            text = str(text[1]) + " tick(s) time step has been taken"
        else:
            text = str(text[1]) + " tick(s) time step has not been taken, you are gonna miss a deadline"
    if text in enforcement.dcr['events']:
        is_access = enforcement.perform_controllable_event(text)
        if is_access == "Grant":
            text = "Grant access to perform " + text
        else:
            text = "Deny performing " + text
    mylist.insert(tk.END, text)
    urgentDeadlines = enforcement.check_urgent_deadlines()
    if len(urgentDeadlines) > 0:
        print(urgentDeadlines)
        for e in urgentDeadlines:
            mylist.insert(tk.END, e + " is executed because of urgent event")
    mylist.yview(tk.END)
    deadline_label.config(text= "Next deadline: " + str(dcr_semantics.find_next_deadline(enforcement.dcr)))
    delay_label.config(text="Next delay: " + str(dcr_semantics.find_next_delay(enforcement.dcr)))

buttonframe = tk.Frame(master=window)
buttonframe.columnconfigure(0, weight=1)
buttonframe.columnconfigure(1, weight=1)
buttonframe.columnconfigure(2, weight=1)
buttonframe.columnconfigure(3, weight=1)

event_frame = tk.LabelFrame(buttonframe, text="Events in the DCR")
event_frame.grid(row=0, column=0, sticky="news", padx=20, pady=10)

button_release = ttk.Button(event_frame, text="release", command= lambda: insert_line("release"))
button_release.grid(row=0, column=0)

button_readmit = ttk.Button(event_frame, text="readmit", command= lambda: insert_line("readmit"))
button_readmit.grid(row=0, column=1)

button_delete = ttk.Button(event_frame, text="delete", command= lambda: insert_line("delete"))
button_delete.grid(row=0, column=2)

button_archive = ttk.Button(event_frame, text="archive", command= lambda: insert_line("archive"))
button_archive.grid(row=0, column=3)

button_unarchive = ttk.Button(event_frame, text="unarchive", command= lambda: insert_line("unarchive"))
button_unarchive.grid(row=0, column=4)

button_availableEvents = ttk.Button(buttonframe, text="Available events", command= lambda: insert_line("Avaiable events: " + str(dcr_semantics.enabled(enforcement.dcr))))
button_availableEvents.grid(row=1, column=0)

newframe = tk.Frame(master=window)
newframe.columnconfigure(0, weight=1)

deadline_label = tk.Label(newframe, text="Next deadline: " + str(dcr_semantics.find_next_deadline(enforcement.dcr)))
deadline_label.grid(row=0, column=0)

delay_label = tk.Label(newframe, text="Next delay: " + str(dcr_semantics.find_next_delay(enforcement.dcr)))
delay_label.grid(row=1, column=0)

time_label = tk.Label(newframe, text="Time step")
time_spinbox = tk.Spinbox(newframe, from_=0, to=sys.maxsize)
time_label.grid(row=4, column=0)
time_spinbox.grid(row=5, column=0)

button_time = ttk.Button(newframe, text="Enter", command= lambda: insert_line(dcr_semantics.time_step(int(time_spinbox.get()), enforcement.dcr, dict_exe)))
button_time.grid(row=6, column=0)

newframe.grid(row=0, column=2)
buttonframe.grid(row=1, column=0)

# This part checks if the policy is enforceable, and if it is not
# then it tells which of the three points are violated
if enforcement.is_enforceable():
    insert_line("The policy is enforceable")
else:
    insert_line("The policy is not enforceable")
    if enforcement.iGraph.is_cyclic():
        insert_line("The policy contains cycles so we do not check further enforcement violations")
    else:
        if enforcement.iGraph.check_for_responses() == False:
            insert_line("The policy contains reponses and includesTo in wrong direction")
        if enforcement.iGraph.check_for_delays() == False:
            insert_line("The policy contains delay in the inhibitor graph")

#button_archive.state(['disabled'])


window.mainloop()