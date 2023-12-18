import pm4py
from pm4py.algo.discovery.dcr_discover import algorithm as alg
from pm4py.objects.dcr.importer import importer as dcr_importer
from pm4py.objects.dcr.exporter import exporter as dcr_exporter
from pm4py.objects.dcr.semantics import DcrSemantics
from pm4py.objects.conversion.dcr import *


if __name__ == "__main__":
    dcr_graph = dcr_importer.apply('data/dcr_from_portal.xml')
    semantics_obj = DcrSemantics(dcr_graph)
    semantics_obj.execute('C')
    semantics_obj.execute(31)
    semantics_obj.execute('B')
    semantics_obj.execute(20)
    semantics_obj.execute('A')
    semantics_obj.execute('D')
    print(semantics_obj.enabled())
    dcr_exporter.apply(dcr_graph,'data/dcr_to_portal.xml')
