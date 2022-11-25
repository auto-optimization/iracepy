import numpy as np 
from irace import irace
import pandas as pd

import json
def target_runner(experiment, scenario):
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
    parallel = 1,
    logFile = ""
)


def test_default_digits():
    tuner = irace(scenario, params, target_runner)
    tuner.set_initial(defaults)
    best_conf = tuner.run()
    print(best_conf)
