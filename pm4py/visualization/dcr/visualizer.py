from pm4py.visualization.dcr.variants import classic
from enum import Enum
from pm4py.util import exec_utils
from copy import deepcopy


class Variants(Enum):
    CLASSIC = classic


DEFAULT_VARIANT = Variants.CLASSIC


def apply(dcr, variant=DEFAULT_VARIANT):
    dcr = deepcopy(dcr)
    return exec_utils.get_variant(variant).apply(dcr)
