from enum import Enum
from typing import Union

from pm4py.objects.dcr.group_subprocess.obj import GroupSubprocessDcrGraph
from pm4py.objects.dcr.milestone_noresponse.obj import MilestoneNoResponseDcrGraph
from pm4py.objects.dcr.timed.obj import TimedDcrGraph
from pm4py.objects.dcr.utils.utils import nested_groups_and_sps_to_flat_dcr
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.conversion.dcr.variants import to_inhibitor_net, to_timed_arc_petri_net
from pm4py.objects.dcr.obj import DcrGraph
from pm4py.util import exec_utils


class Variants(Enum):
    TO_INHIBITOR_NET = to_inhibitor_net
    TO_TIMED_ARC_PETRI_NET = to_timed_arc_petri_net


DEFAULT_VARIANT = Variants.TO_INHIBITOR_NET


def apply(obj: Union[DcrGraph,MilestoneNoResponseDcrGraph,GroupSubprocessDcrGraph,TimedDcrGraph],
          variant=DEFAULT_VARIANT, parameters=None) -> (PetriNet, Marking):
    """
    Converts a DCR Graph to a Petri Net

    Reference paper:
    Vlad Paul Cosma, Thomas T. Hildebrandt & Tijs Slaats. "Transforming Dynamic Condition Response Graphs to Safe Petri Nets" https://doi.org/10.1007/978-3-031-33620-1_22
    Parameters
    ----------
    obj :
        A DCR Graph with all 6 relations and optionally timed.
    variant:
        TO_INHIBITOR_NET|TO_TIMED_ARC_PETRI_NET Create either an untimed inhibitor net or a timed arc petri net respectively.
    parameters:
        Configurable parameters:
            -preoptimize: True if the conversion should be optimized based on the reachable DCR Markings else False
            -postoptimize: True if the conversion should be optimized based on the reachable Petri Net Marking else False
            -map_unexecutable_events: True if events not executable in the DCR Graph should be mapped, else False
            -tapn_path: Path to export the net to. Can end in .pnml or .tapn for timed arc petri nets[1]
            -debug: True if debug information should be displayed and a Petri Net for each step in the conversion should be generated else False
    Returns
    --------
    A petri net and its initial marking based on the input DCR Graph

    References:
    [1] Lasse Jacobsen, Morten Jacobsen, Mikael H. Møller, and Jirı Srba. "Verification of Timed-Arc Petri Nets" https://doi.org/10.1007/978-3-642-18381-2_4
    """
    if parameters is None:
        parameters = {}
    if isinstance(obj, GroupSubprocessDcrGraph):
        obj = nested_groups_and_sps_to_flat_dcr(obj)
    obj = obj.obj_to_template()
    return exec_utils.get_variant(variant).apply(obj, parameters=parameters)
