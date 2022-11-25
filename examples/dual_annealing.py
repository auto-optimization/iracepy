import numpy as np
from scipy.optimize import dual_annealing

from irace import irace

DIM=10 # This works even with parallel
LB = [-5.12]
UB = [5.12]
# This target_runner is over-complicated on purpose to show what is possible.
def target_runner(experiment, scenario, lb = LB, ub = UB):
    func = lambda x: np.sum(x*x - DIM*np.cos(2*np.pi*x)) + DIM * np.size(x)
    lw = lb * DIM
    up = ub * DIM
    # Some configurations produced a warning, but the values are within the limits. That seems a bug in scipy. TODO: Report the bug to scipy.
    print(f'{experiment["configuration"]}')
    ret = dual_annealing(func, bounds=list(zip(lw, up)), seed=experiment['seed'], maxfun = 1e4,
                         **experiment['configuration'])
    return dict(cost=ret.fun)

parameters_table = '''
initial_temp       "" r,log (0.02, 5e4)
restart_temp_ratio "" r,log (1e-5, 1)
visit              "" r     (1.001, 3)
accept             "" r     (-1e3, -5)
# TODO: irace does not have a type boolean yet.
no_local_search    "" c     ("","1") 
'''

default_values = '''
initial_temp restart_temp_ratio visit accept no_local_search
5230         2e-5               2.62  -5.0   ""
'''

# These are dummy "instances", we are tuning only on a single function.
instances = np.arange(100)

# See https://mlopez-ibanez.github.io/irace/reference/defaultScenario.html
scenario = dict(
    instances = instances,
    maxExperiments = 500,
    debugLevel = 3,
    digits = 5,
    parallel=2, # It can run in parallel ! 
    logFile = "")


tuner = irace(scenario, parameters_table, target_runner)
tuner.set_initial_from_str(default_values)
best_confs = tuner.run()
# Pandas DataFrame
print(best_confs)
