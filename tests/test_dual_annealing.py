import numpy as np
from irace import irace
import os
import pytest
from utils import PropagatingThread

DIM=10 # This works even with parallel
LB = [-5.12]
UB = [5.12]
# This target_runner is over-complicated on purpose to show what is possible.
def target_runner(experiment, scenario, lb = LB, ub = UB):
    func = lambda x: np.sum(x*x - DIM*np.cos(2*np.pi*x)) + DIM * np.size(x)
    lw = lb * DIM
    up = ub * DIM
    if experiment['configuration']['initial_temp'] == 1:
        assert 'integer' not in experiment['configuration']
    # No actual computation because computation is expensive and we don't care about it.
    return dict(cost=experiment['configuration']['initial_temp'])

parameters_table = '''
initial_temp       "" r,log (0.02, 5e4)
restart_temp_ratio "" r,log (1e-5, 1)
visit              "" r     (1.001, 3)
accept             "" r     (-1e3, -5)
integer            "" i     (1, 10)     |  no_local_search == "1"
# TODO: irace does not have a type boolean yet.
no_local_search    "" c     ("","1") 
'''

default_values = '''
initial_temp restart_temp_ratio visit accept integer no_local_search
5230         2e-5               2.62  -5.0   NA        ""
'''

# These are dummy "instances", we are tuning only on a single function.
instances = np.arange(100)

# See https://mlopez-ibanez.github.io/irace/reference/defaultScenario.html

if os.name == 'nt':
    parallel = 1
else:
    parallel = 2

scenario = dict(
    instances = instances,
    maxExperiments = 180,
    debugLevel = 3,
    seed = 123,
    digits = 5,
    parallel= parallel, # It can run in parallel ! 
    logFile = "")

def run_irace(scenario, parameters_table, target_runner):
    tuner = irace(scenario, parameters_table, target_runner)
    tuner.set_initial_from_str(default_values)
    best_confs = tuner.run()
    # FIXME: assert type Pandas DataFrame
    print(best_confs)

def test_fail_windows():
    # FIXME: remove when https://github.com/auto-optimization/iracepy/issues/16 is closed. 
    if os.name == 'nt':
        with pytest.raises(NotImplementedError):
            scenario = dict(
                instances = instances,
                maxExperiments = 180,
                debugLevel = 3,
                seed = 123,
                digits = 5,
                parallel= 2, # It can run in parallel ! 
                logFile = "")
            tuner = irace(scenario, parameters_table, target_runner)
            tuner.run()
            

def test_run():
    run_irace(scenario, parameters_table, target_runner)

def test_run_in_thread():
    tuner_t = PropagatingThread(target=run_irace, args=(scenario, parameters_table, target_runner))
    tuner_t.start()
    tuner_t.join()
