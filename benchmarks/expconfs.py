import pprint

from commons import *
from experimenter import get_shared_para_dict
from utilities.utils import *

# LEVELDB
#   k written_bytes valid_data_bytes   num max_key   hotness
# 1 1     2.5875816       0.10041694 6e+06   6e+05 25.768377
# 2 2     4.1530533       0.49622203 6e+06   6e+06  8.369345
# 3 3     0.9941254       0.01778593 6e+06   6e+04 55.893923
# 4 4     0.4081306       0.01940136 3e+06   3e+04 21.036185      20+sec
# 5 5     1.0261040       0.06891455 3e+06   3e+05 14.889512
# 6 6     1.6484642       0.23112959 3e+06   3e+06  7.132208      20+ sec
# 7 1     1.6486170       0.23750480 3e+06   3e+06  6.941405
# 8 2     2.5417020       0.30242460 4e+06   4e+06  8.404416
# 9 3     2.3927960       0.27410040 4e+06   3e+06  8.729633

def repeat_bench(name, n):
    return ','.join([name] * n)


proc_settings = {
    ######## LevelDB #######
    'leveldb': {

        'aging_overwrite':
            {'name' : 'LevelDB',
             'benchmarks': 'overwrite,compact',
             'num': 3*MILLION,
             'max_key': 3*MILLION,
             'max_log': -1,
             'do_strace': False,
             'use_existing_db': 0,
            },

        'aging_fillseq':
            {'name' : 'LevelDB',
             'benchmarks': 'fillseq,compact',
             'num': 3*MILLION,
             'max_key': 3*MILLION,
             'max_log': -1,
             'do_strace': False,
             'use_existing_db': 0,
            },

        'readrandom':
            {'name' : 'LevelDB',
             'benchmarks': 'readrandom',
             'num': 3*MILLION,
             'max_key': 3*MILLION,
             'max_log': -1,
             'do_strace': False,
             'use_existing_db': 1,
             },

        'readseq':
            {'name' : 'LevelDB',
             'benchmarks': 'readseq',
             'num': 3*MILLION,
             'max_key': 3*MILLION,
             'max_log': -1,
             'do_strace': False,
             'use_existing_db': 1,
             },
    }, ### LevelDB

    ######## RocksDB #######
    'rocksdb': {
        'aging_overwrite':
            {'name' : 'RocksDB',
             'benchmarks': 'overwrite,compact',
             'num': 3*MILLION,
             'do_strace': False,
             'use_existing_db': 0,
             'mem_limit_in_bytes': 1*GB,
            },

        'aging_fillseq':
            {'name' : 'RocksDB',
             'benchmarks': 'fillseq,compact',
             'num': 3*MILLION,
             'do_strace': False,
             'use_existing_db': 0,
             'mem_limit_in_bytes': 1*GB,
            },

        'readrandom':
            {'name' : 'RocksDB',
             'benchmarks': 'readrandom',
             'num': 3*MILLION,
             'do_strace': False,
             'use_existing_db': 1,
             'mem_limit_in_bytes': 128*MB,
             },

        'readseq':
            {'name' : 'RocksDB',
             'benchmarks': 'readseq,readseq,readseq,readseq,readseq,readseq',
             'num': 3*MILLION,
             'do_strace': False,
             'use_existing_db': 1,
             'mem_limit_in_bytes': 128*MB,
             },

        'writeseq':
            {'name' : 'RocksDB',
             'benchmarks': repeat_bench('fillseq', 10),
             'num': 1*MILLION,
             'do_strace': False,
             'use_existing_db': 0,
             'mem_limit_in_bytes': 10*GB,
             },

        'writerandom':
            {'name' : 'RocksDB',
             'benchmarks': repeat_bench('overwrite', 10),
             'num': 3*MILLION,
             'do_strace': False,
             'use_existing_db': 0,
             'mem_limit_in_bytes': 10*GB,
             },



    }, ### RocksDB
}



class ParameterPool(object):
    def __init__(self, expname, testname, filesystem):
        self.lbabytes = 1 * GB
        self.expname = expname
        self.filesystem = filesystem

        self.para_dicts = []

        for name in testname:
            func = eval('self.{}'.format(name))
            func()

    def __iter__(self):
        for para_dict in self.para_dicts:
            yield para_dict

    def env_reqscale(self, d):
        d.update(
            {
                'ftl' : ['ftlcounter'],
                'enable_simulation': [True],
                'dump_ext4_after_workload': [True],
                'only_get_traffic': [False],
                'do_ncq_depth_time_line': [True],
            })

    def get_base_dict(self):
        shared_para_dict = get_shared_para_dict(
                self.expname, self.lbabytes)
        shared_para_dict['filesystem'] = self.filesystem

        return shared_para_dict

    def extend_para_dicts(self, para_dicts):
        self.para_dicts.extend(para_dicts)




    def rocksdb_reqscale_r_seq(self):
        shared_para_dict = self.get_base_dict()
        self.env_reqscale(shared_para_dict)

        # set aging
        shared_para_dict.update({
            'age_workload_class': ['AppMix'],
            'aging_appconfs': [
                    [
                        proc_settings['rocksdb']['aging_fillseq']
                    ]
                ],
        })

        # set target
        shared_para_dict.update({
            'workload_class' : [ 'AppMix' ],
            'run_seconds'    : [None],
            'appconfs': [
                    [
                        proc_settings['rocksdb']['readseq']
                    ]
                ],
        })

        self.extend_para_dicts(ParameterCombinations(shared_para_dict))
        pprint.pprint( self.para_dicts )

    def rocksdb_reqscale_r_rand(self):
        shared_para_dict = self.get_base_dict()
        self.env_reqscale(shared_para_dict)

        # set aging
        shared_para_dict.update({
            'age_workload_class': ['AppMix'],
            'aging_appconfs': [
                    [
                        proc_settings['rocksdb']['aging_overwrite']
                    ]
                ],
        })

        # set target
        shared_para_dict.update({
            'workload_class' : [ 'AppMix' ],
            'run_seconds'    : [None],
            'appconfs': [
                    [
                        proc_settings['rocksdb']['readrandom'],
                    ]
                ],
        })

        self.extend_para_dicts(ParameterCombinations(shared_para_dict))
        pprint.pprint( self.para_dicts )

    def rocksdb_reqscale_r_mix(self):
        shared_para_dict = self.get_base_dict()
        self.env_reqscale(shared_para_dict)

        # set aging
        shared_para_dict.update({
            'age_workload_class': ['AppMix'],
            'aging_appconfs': [
                    [
                        proc_settings['rocksdb']['aging_fillseq'],
                        proc_settings['rocksdb']['aging_overwrite']
                    ]
                ],
        })

        # set target
        shared_para_dict.update({
            'workload_class' : [ 'AppMix' ],
            'run_seconds'    : [5],
            'appconfs': [
                    [
                        proc_settings['rocksdb']['readseq'],
                        proc_settings['rocksdb']['readrandom'],
                    ]
                ],
        })

        self.extend_para_dicts(ParameterCombinations(shared_para_dict))
        pprint.pprint( self.para_dicts )

    def rocksdb_reqscale_w_rand(self):
        shared_para_dict = self.get_base_dict()
        self.env_reqscale(shared_para_dict)

        # set aging
        # Do nothing.

        # set target
        shared_para_dict.update({
            'workload_class' : [ 'AppMix' ],
            'run_seconds'    : [None],
            'appconfs': [
                    [
                        proc_settings['rocksdb']['writerandom'],
                    ]
                ],
        })

        self.para_dicts = ParameterCombinations(shared_para_dict)
        pprint.pprint( self.para_dicts )

    def rocksdb_reqscale_w_seq(self):
        self.env_reqscale(shared_para_dict)

        # set aging
        # Do nothing.

        # set target
        shared_para_dict.update({
            'workload_class' : [ 'AppMix' ],
            'run_seconds'    : [None],
            'appconfs': [
                    [
                        proc_settings['rocksdb']['writeseq'],
                    ]
                ],
        })

        self.extend_para_dicts(ParameterCombinations(shared_para_dict))
        pprint.pprint( self.para_dicts )

    def rocksdb_reqscale_w_mix(self):
        shared_para_dict = self.get_base_dict()
        self.env_reqscale(shared_para_dict)

        # set aging
        # Do nothing.

        # set target
        shared_para_dict.update({
            'workload_class' : [ 'AppMix' ],
            'run_seconds'    : [None],
            'appconfs': [
                    [
                        proc_settings['rocksdb']['writeseq'],
                        proc_settings['rocksdb']['writerandom'],
                    ]
                ],
        })

        self.extend_para_dicts(ParameterCombinations(shared_para_dict))
        self.para_dicts = ParameterCombinations(shared_para_dict)
        pprint.pprint( self.para_dicts )

    def leveldb_reqscale_r_seq(self):
        shared_para_dict = self.get_base_dict()
        self.env_reqscale(shared_para_dict)

        # set aging
        shared_para_dict.update({
            'age_workload_class': ['AppMix'],
            'aging_appconfs': [
                    [
                        proc_settings['leveldb']['aging_fillseq']
                    ]
                ],
        })

        # set target
        shared_para_dict.update({
            'workload_class' : [ 'AppMix' ],
            'run_seconds'    : [None],
            'appconfs': [
                    [
                        proc_settings['leveldb']['readseq']
                    ]
                ],
        })

        self.extend_para_dicts(ParameterCombinations(shared_para_dict))
        pprint.pprint( self.para_dicts )















