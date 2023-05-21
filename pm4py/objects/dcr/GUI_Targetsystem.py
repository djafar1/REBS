import tkinter as tk
from tkinter import ttk

import sys
sys.path.insert(1, '/Users/timei/Documents/Datalogi/Semester6/Bachelor/pm4py-dcr')

#import os
#os.chdir('C:/Users/timei/Documents/Datalogi/Semester6/Bachelor/pm4py-dcr')

from pm4py.objects.dcr import enforcement as dcr_enforcement
from pm4py.objects.dcr import semantics as dcr_semantics

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

def insertLine(text):
    mylist.insert(tk.END, text)
    urgentDeadlines = enforcement.check_urgent_deadlines()
    if len(urgentDeadlines) > 0:
        print(urgentDeadlines)
        for e in urgentDeadlines:
            mylist.insert(tk.END, e)
    deadline_label.config(text= "Next deadline: " + str(dcr_semantics.find_next_deadline(enforcement.dcr)))
    delay_label.config(text="Next delay: " + str(dcr_semantics.find_next_delay(enforcement.dcr)))

mylist.grid(row=0, column=0, sticky="news")
scrollbar.config(command = mylist.yview)

buttonframe = tk.Frame(master=window)
buttonframe.columnconfigure(0, weight=1)
buttonframe.columnconfigure(1, weight=1)
buttonframe.columnconfigure(2, weight=1)
buttonframe.columnconfigure(3, weight=1)

button_release = ttk.Button(buttonframe, text="release", command= lambda: insertLine(enforcement.peform_controllable_event("release")))
button_release.grid(row=0, column=0)

button_readmit = ttk.Button(buttonframe, text="readmit", command= lambda: insertLine(enforcement.peform_controllable_event("readmit")))
button_readmit.grid(row=0, column=1)

button_delete = ttk.Button(buttonframe, text="delete", command= lambda: insertLine(enforcement.peform_controllable_event("delete")))
button_delete.grid(row=0, column=2)

button_archive = ttk.Button(buttonframe, text="archive", command= lambda: insertLine(enforcement.peform_controllable_event("archive")))
button_archive.grid(row=0, column=3)

button_unarchive = ttk.Button(buttonframe, text="unarchive", command= lambda: insertLine(enforcement.peform_controllable_event("unarchive")))
button_unarchive.grid(row=0, column=4)

button_add = ttk.Button(buttonframe, text="test", command= lambda: insertLine(dcr_semantics.enabled(enforcement.dcr)))
button_add.grid(row=0, column=5)

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

button_time = ttk.Button(newframe, text="Enter", command= lambda: insertLine(dcr_semantics.time_step(int(time_spinbox.get()), enforcement.dcr, dict_exe)))
button_time.grid(row=6, column=0)

newframe.grid(row=0, column=2)
buttonframe.grid(row=1, column=0)

#button_archive.state(['disabled'])


window.mainloop()