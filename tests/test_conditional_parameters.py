import numpy as np 
from irace import irace

def target_runner(experiment, scenario):
    configuration = experiment['configuration']
    assert 'two' not in configuration or configuration['flag'] == '1'
    assert configuration['flag'] != '1' or 'two' in configuration
    return dict(cost=experiment['configuration']['one'])


params = '''
one "" r (0, 1)
flag "" c ("", "1") 
two "" r (0, 4) | flag == "1"
'''

scenario = dict(
    instances = np.arange(10),
    maxExperiments = 96,
    debugLevel = 0,
    seed = 123,
    parallel = 1,
    logFile = ""
)

def test_run():
    tuner = irace(scenario, params, target_runner)
    best_confs = tuner.run()
    # Pandas DataFrame
    print(best_confs)
