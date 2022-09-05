import numpy as np
from scipy.optimize import dual_annealing

from irace import irace

def target_runner(experiment, scenario):
    DIM = 10
    func = lambda x: np.sum(x*x - DIM*np.cos(2*np.pi*x)) + DIM * np.size(x)
    lw = [-5.12] * DIM
    up = [5.12] * DIM
    # Some configurations produced a warning, but the values are within the limits. That seems a bug in scipy.
    print(f'{experiment["configuration"]}')
    ret = dual_annealing(func, bounds=list(zip(lw, up)), seed=experiment['seed'], maxfun = 1e4,
                         **experiment['configuration'])
    return dict(cost=ret.fun)

parameters_table = '''
initial_temp       "" r,log (0.02, 5e4)
restart_temp_ratio "" r,log (1e-5, 1)
visit              "" r     (1.001, 3)
accept             "" r     (-1e3, -5)
'''

default_values = '''
initial_temp restart_temp_ratio visit accept
5230         2e-5               2.62  -5.0
'''

# These are dummy "instances", we are tuning only on a single function.
instances = np.arange(100)

scenario = dict(
    instances = instances,
    maxExperiments = 500,
    debugLevel = 3,
    digits = 5,
    parallel=2, # It can run in parallel ! 
    logFile = "")


tuner = irace(scenario, parameters_table, target_runner)
tuner.set_initial(default_values)
tuner.run()

