import unittest
import collections
import shutil
import os
import argparse

import config
from workflow import *
import wiscsim
from mp_utils import *
from utilities import utils
from config_helper import rule_parameter
from pyreuse.helpers import shcmd
from config_helper import experiment
import math

KB = 1024
MB = 1024**2
GB = 1024**3

def create_config(mode):
    conf = wiscsim.dftldes.Config()

    conf['ftl_type'] = "dftldes"
    conf['SSDFramework']['ncq_depth'] = 8

    # ssd config
    if mode == "small":
        total_capacity = 1*GB
    elif mode == "medium":
        total_capacity = 4*GB

    n_blocks_per_plane = total_capacity / (256*8*4*KB)
    conf['flash_config']['n_pages_per_block'] = 256
    conf['flash_config']['n_blocks_per_plane'] = n_blocks_per_plane
    conf['flash_config']['n_planes_per_chip'] = 1
    conf['flash_config']['n_chips_per_package'] = 1
    conf['flash_config']['n_packages_per_channel'] = 1
    conf['flash_config']['n_channels_per_dev'] = 8

    # set ftl
    conf['do_not_check_gc_setting'] = True
    conf['enable_simulation'] = True
    conf['mapping_cache_bytes'] = 20 * MB

    conf['simulator_class'] = 'SimulatorDESNew'

    utils.runtime_update(conf)

    return conf

class RunFTL():
    def __init__(self, args):
        self.ftl = "dftldes"
        if args.mode == "small":
            self.trace = "traces/wdev_2.csv"
        elif args.mode == "medium":
            self.trace = "traces/ts_0.csv"
        else:
            raise NotImplementedError

        self.conf = create_config(args.mode)
        self.func = "self.run_%s()" % self.ftl
        self.conf['result_dir'] = args.output
        self.conf.GC_high_threshold_ratio = 1 - args.gc_low
        self.conf.GC_low_threshold_ratio = 1 - args.gc_high

        self.events = parse_events(self.trace, start_lineno = 0, lineno=1000000, format="MSR")

    def run(self):
        eval(self.func)

    def run_dftldes(self):
        wf = Workflow(self.conf)
        sim = wf.run_simulator(self.events)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', dest="mode", required=True, help="Running mode")
    parser.add_argument('-o', '--output', dest="output", default='.', help="Output directory")
    parser.add_argument('-gh', '--high', dest="gc_high", default=0.3, type=float, help="GC high threshold ratio")
    parser.add_argument('-gl', '--low', dest="gc_low", default=0.1, type=float, help="GC low threshold ratio")
    args = parser.parse_args()

    experiment = RunFTL(args)
    experiment.run()
