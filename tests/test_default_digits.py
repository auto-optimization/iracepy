import numpy as np 
from irace import irace

import json
def target_runner(experiment, scenario):
    with open('abc.json', 'w') as f:
        json.dump(experiment, f)
    return dict(cost=experiment['configuration']['one'])


params = '''
one "" r (0, 1)
'''

scenario = dict(
    instances = np.arange(10),
    maxExperiments = 96,
    debugLevel = 0,
    parallel = 1
)


def test_default_digits():
    tuner = irace(scenario, params, target_runner)
    best_conf = tuner.run()
    print(best_conf)

