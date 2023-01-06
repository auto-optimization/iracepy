import numpy as np 
from irace import irace
import pandas as pd
from multiprocessing import Queue

q = Queue()

def target_runner(experiment, scenario):
    q.put(124)
    if experiment['configuration']['one'] == '0':
        return dict(cost=0)
    else:
        return dict(cost=1)

def target_runner2(experiment, scenario):
    if experiment['id.instance'] == 1:
        experiment['instance'].put(1335)
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
    assert q.get() == 124
    
def test_instances():
    q = Queue()
    scenario = dict(
        instances = [q],
        maxExperiments = 180,
        debugLevel = 0,
        parallel = 1,
        logFile = "",
        seed = 123
    )
    tuner = irace(scenario, params, target_runner2)
    best_conf = tuner.run()
    assert q.get() == 1335

def test_instances2():
    q = Queue()
    scenario = dict(
        instances = [q],
        maxExperiments = 180,
        debugLevel = 0,
        parallel = 2,
        logFile = "",
        seed = 123
    )
    tuner = irace(scenario, params, target_runner2)
    best_conf = tuner.run()
    assert q.get() == 1335

def test_default_serializer():
    q = Queue()
    scenario = dict(
        instances = [q],
        maxExperiments = 180,
        debugLevel = 0,
        parallel = 2,
        logFile = "",
        seed = 123,
        instanceObjectSerializer = lambda x: 'hello world'
    )
    tuner = irace(scenario, params, target_runner2)
    best_conf = tuner.run()
    assert q.get() == 1335
