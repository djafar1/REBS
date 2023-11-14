import pm4py
from copy import deepcopy
from pm4py.algo.conformance.dcr.variants.classic import Outputs, HandleChecker
from pm4py.objects.dcr.semantics import DCRSemantics
def conformance_ground_truth(graph, ground_truth):
    """
    Due to how the conformance was implemented, it was necesary to extract the implementation,
    such that the run time for each run time with deviation and no deviation could be marked with a time
    """
    log = ground_truth
    checker = HandleChecker(graph)
    semantics = DCRSemantics()
    initial_marking = deepcopy(graph.marking)
    total_num_constraints = graph.get_constraints()
    for trace in ground_truth:
        graph.marking.reset(deepcopy(initial_marking))

        # create base dict to accumalate trace conformance data
        ret = {Outputs.NO_CONSTR_TOTAL.value: total_num_constraints, Outputs.DEVIATIONS.value: []}

        response_origin = []
        # iterate through all events in a trace
        for event in trace:
            # get the event to be executed
            e = graph.get_event(event[activity_key])
            # check for deviations
            if e in graph.responses:
                for response in self.__g.responses[e]:
                    response_origin.append((e, response))

            self.__checker.all_checker(e, event, self.__g, ret[Outputs.DEVIATIONS.value],
                                       parameters=self.__parameters)

            if not self.__semantics.is_enabled(e, self.__g):
                self.__checker.enabled_checker(e, self.__g, ret[Outputs.DEVIATIONS.value],
                                               parameters=self.__parameters)

            # execute the event
            self.__semantics.execute(self.__g, e)

            if len(response_origin) > 0:
                for i in response_origin:
                    if e == i[1]:
                        response_origin.remove(i)

        # check if run is accepting
        if not self.__semantics.is_accepting(self.__g):
            self.__checker.accepting_checker(self.__g, response_origin, ret[Outputs.DEVIATIONS.value],
                                             parameters=self.__parameters)


        ret[Outputs.NO_DEV_TOTAL.value] = len(ret[Outputs.DEVIATIONS.value])
        ret[Outputs.FITNESS.value] = 1 - ret[Outputs.NO_DEV_TOTAL.value] / ret[Outputs.NO_CONSTR_TOTAL.value]
        ret[Outputs.IS_FIT.value] = ret[Outputs.NO_DEV_TOTAL.value] == 0
        conf_case.append(ret)


        self.__g.marking.reset(deepcopy(initial_marking))
        #due to how the rule conformance was implemented,it was necessary to take the implementation into the conformance c