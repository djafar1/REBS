import sys
import os

# Assuming the pm4py library is in the parent directory of your script
pm4py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(pm4py_path)

os.environ['PM4PY_SHOW_EVENT_LOG_DEPRECATION'] = 'false'

import pm4py
pm4py.util.constants.SHOW_EVENT_LOG_DEPRECATION = False
import time
from pm4py.algo.discovery.dcr_discover import algorithm as dcr_alg
from pm4py.algo.discovery.dcr_discover.algorithm import Variants
from pm4py.objects.dcr.utils.dcr_utils import time_to_int, clean_input
from pm4py.objects.conversion.dcr import converter as dcr_to_tapn
import pm4py.objects.petri_net.utils.final_marking as discover_fm
from pm4py.objects.dcr.exporter import exporter as dcr_exporter

# all bpi + sepsis + rtfmp + dreyers + pdc
logs_list = {}
logs_folder = '/home/vco/Datasets/data/TKDE_Benchmark'
for file in os.listdir(logs_folder):
    if file.endswith(".xes"):
        name = os.path.basename(file.split('.')[0])
        logs_list[name] = os.path.join(logs_folder, file)
logs_list = logs_list | {
    # 'BPIC19': '/home/vco/Datasets/BPI_Challenge_2019.xes',
    'BPIC17': '/home/vco/Datasets/BPI Challenge 2017.xes',
    'BPIC17-Offer': '/home/vco/Datasets/BPI Challenge 2017 - Offer log.xes'
}
logs_list.pop('BPIC15_1f') # converting to a PN causes pycharm to crash (I suspect it runs out of RAM, try it in the terminal.
logs_list.pop('BPIC15_2f') # converting to a PN causes pycharm to crash (I suspect it runs out of RAM, try it in the terminal.
logs_list.pop('BPIC15_3f') # converting to a PN causes pycharm to crash (I suspect it runs out of RAM, try it in the terminal.
logs_list.pop('BPIC15_4f') # converting to a PN causes pycharm to crash (I suspect it runs out of RAM, try it in the terminal.
logs_list.pop('BPIC15_5f') # converting to a PN causes pycharm to crash (I suspect it runs out of RAM, try it in the terminal.
print(f'[i] Prepared for benchmarking on {len(logs_list)} logs')
print(logs_list)


def train_dcr_model(train, log_name, config):
    dcr_model, _ = dcr_alg.apply(train, **config)
    if log_name == 'SEPSIS':
        dcr_model = time_to_int(dcr_model, precision='hours')
    else:
        dcr_model = time_to_int(dcr_model, precision='days')
    dcr_model = clean_input(dcr_model, white_space_replacement='_')
    dcr_exporter.apply(dcr_model,f'models/tapnminer_dcr_compare/{log_name}.xml')
    # print(f'[!TAPN] Starting conversion for: models/tapnminer/{log_name}.tapn')
    # tapn, im = dcr_to_tapn.apply(dcr_model, variant=dcr_to_tapn.Variants.TO_TIMED_ARC_PETRI_NET,
    #                              parameters={'preoptimize': True, 'postoptimize': True, 'map_unexecutable_events': False, 'debug': False, 'tapn_path': f'models/tapnminer/{log_name}.tapn'})
    # fm = discover_fm.discover_final_marking(tapn)
    # print(f'[!TAPN] Done! Net saved in: models/tapnminer/{log_name}.tapn')
    # return tapn, im, fm, dcr_model


def score_based_on_config(train, config, log_name):
    start_time = time.time()
    tapn, im, fm, dcr_model = train_dcr_model(train, log_name, config)
    elapsed = time.time() - start_time


def score_everything(logs_name_path_dict, config):
    for l_name, log_path in logs_name_path_dict.items():
        # if not os.path.isfile(f'models/tapnminer/{l_name}.tapn'):
        print(f'[i] Started for {l_name}')
        single_log = pm4py.read_xes(log_path, return_legacy_log_object=True, show_progress_bar=False)
        score_based_on_config(single_log, config, l_name)
        # else:
        #     print(f'[i] Skipping {l_name} tapn already exists!')



if __name__ == "__main__":
    config = {'variant': Variants.DCR_BASIC, 'timed': True, 'pending': True}
    score_everything(logs_list, config)
