import numpy as np 
from irace import irace
import pandas as pd
from multiprocessing import Process, Queue
from threading import Timer, Thread
from time import sleep

def target_runner(experiment, scenario):
    raise ValueError()


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

killed = False

def test_no_hang():
    p = Process(target=start_irace)
    p.start()
    Timer(1, sigterm_process, args=(p,)).start()
    Timer(2, sigkill_process, args=(p,)).start()
    sleep(3)
    assert not killed 

def sigterm_process(p):
    if p.is_alive():
        p.terminate()
        global killed
        killed = True

def sigkill_process(p):
    if p.is_alive():
        p.kill()
        global killed
        killed = True

def start_irace():
    tuner = irace(scenario, params, target_runner)
    tuner.set_initial(defaults)
    best_conf = tuner.run()
