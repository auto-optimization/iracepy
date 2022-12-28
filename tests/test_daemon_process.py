# This test is written because daemonic processes are not allowed to have children
# and multiprocessing.Pool uses daemonic process.
import numpy as np 
from irace import irace
import pandas as pd
from multiprocessing import Process

import json
def target_runner(experiment, scenario):
    Process(target=print, args=(1,)).start()
    return dict(cost=experiment['configuration']['one'])

params = '''
one "" r (0, 1)
'''

defaults = pd.DataFrame(data=dict(
    one=[0.6]
))

scenario = dict(
    instances = np.arange(10),
    maxExperiments = 96,
    debugLevel = 0,
    parallel = 2,
    logFile = ""
)


def test():
    tuner = irace(scenario, params, target_runner)
    tuner.set_initial(defaults)
    best_conf = tuner.run()
    print(best_conf)
