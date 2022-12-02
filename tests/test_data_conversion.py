import numpy as np 
from irace import irace
import pandas as pd

import json
def target_runner(experiment, scenario):
    if experiment['configuration']['one'] == '0':
        return dict(cost=0)
    else:
        return dict(cost=1)


params = '''
one "" c ('0', '1')
two "" c ("a", "b") | one == '1'
three "" r (0, 1) | one == '1'
four "" i (1, 10) | one == '1'
'''

scenario = dict(
    instances = np.arange(10),
    maxExperiments = 180,
    debugLevel = 0,
    parallel = 1,
    logFile = "",
    seed = 123
)


def test():
    tuner = irace(scenario, params, target_runner)
    best_conf = tuner.run()
    print(best_conf)
    for rowIndex, row in best_conf.iterrows(): #iterate over rows
        for columnIndex, v in row.items():
            assert v is None \
                or v == np.nan \
                or isinstance(v, str) \
                or isinstance(v, float) \
                or isinstance(v, int)
