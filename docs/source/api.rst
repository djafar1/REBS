API Reference
=============
This page provides an overview the extension ``DCR4Py`` for ``pm4py``.

Conversion (:mod:`pm4py.convert`)
-------------------------------------
Conversion of model to petri net has been updated to allow for converting DCR to petri net

  * :meth:`pm4py.convert.convert_to_petri_net` converts a process model to Petri net


Process Discovery (:mod:`pm4py.discovery`)
------------------------------------------
``DCR4Py`` allows for discovery of DCR graphs, note that the dcr-discover will discover a perfect fitting graph for the provided event log.

  * :meth:`pm4py.discovery.discover_dcr`; discovers a *DCR Graph*.


Conformance Checking (:mod:`pm4py.conformance`)
-----------------------------------------------
``DCR4Py`` contains two conformance checking methods, a rule-based and alignment-based conformance checking to help provide insight to a dcr graph conformance compared to the event log.

  * :meth:`pm4py.conformance.conformance_dcr`; rule based conformance checking using a *DCR Graph*
  * :meth:`pm4py.conformance.optimal_alignment_dcr`; optimal alignment conformance checking using a *DCR Graph*


Visualization (:mod:`pm4py.vis`)
------------------------------------------
The ``DCR4Py`` library extension to pm4py implements a visualization for dcr graphs in addtion a method for storing visualization on disk.

  * :meth:`pm4py.vis.view_dcr`; views a *DCR graph*.

ImWe offer also some methods to store the visualizations on the disk:

* :meth:`pm4py.vis.save_vis_dcr`; saves the visualization of a *DCR graph*.



Overall List of Methods
------------------------------------------

.. autosummary::
   :toctree: generated

   pm4py.read.read_dcr_xml
   pm4py.write.write_dcr_xml
   pm4py.convert.convert_to_petri_net
   pm4py.discovery.discover_dcr
   pm4py.conformance.conformance_dcr
   pm4py.conformance.optimal_alignment_dcr
   pm4py.vis.view_dcr
   pm4py.vis.save_vis_dcr
