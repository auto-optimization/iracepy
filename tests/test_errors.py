import numpy as np 
from irace import irace
import pandas as pd
from multiprocessing import Process, Queue
from threading import Timer, Thread, Event
from time import sleep

BASE_TIME = 100

def target_runner(experiment, scenario):
    raise ValueError()

params = '''
one "" r (0, 1)
'''

defaults = pd.DataFrame(data=dict(
    one=[0.6]
))

scenario1 = dict(
    instances = np.arange(10),
    maxExperiments = 96,
    debugLevel = 0,
    parallel = 1,
    logFile = ""
)

scenario2 = dict(
    instances = np.arange(10),
    maxExperiments = 96,
    debugLevel = 0,
    parallel = 2,
    logFile = ""
)
killed = False


def test_no_hang1():
    q = Queue()
    p = Process(target=start_irace, args=(q, scenario1))
    p.start()
    t1 = Timer(20, sigterm_process, args=(p,))
    t2 = Timer(21, sigkill_process, args=(p,))
    t1.start()
    t2.start()
    print("jfjfjfj")
    for i in range(22):
        sleep(1)
        if not p.is_alive():
            t1.cancel()
            t2.cancel()
            break
    assert not killed 

def test_no_hang2():
    q = Queue()
    p = Process(target=start_irace, args=(q, scenario2))
    p.start()
    t1 = Timer(BASE_TIME, sigterm_process, args=(p,))
    t2 = Timer(BASE_TIME + 1, sigkill_process, args=(p,))
    t1.start()
    t2.start()
    for i in range(BASE_TIME + 2):
        sleep(1)
        if not p.is_alive():
            t1.cancel()
            t2.cancel()
            break
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

def start_irace(q, scenario):
    tuner = irace(scenario, params, target_runner)
    tuner.set_initial(defaults)
    try:
        best_conf = tuner.run()
    except:
        q.put(0)

def test_correct_exit1():
    q = Queue()
    p = Process(target=start_irace, args=(q, scenario1))
    p.start()
    t1 = Timer(BASE_TIME, sigterm_process, args=(p,))
    t2 = Timer(BASE_TIME + 1, sigkill_process, args=(p,))
    t1.start()
    t2.start()
    for i in range(BASE_TIME + 2):
        sleep(1)
        if not p.is_alive():
            t1.cancel()
            t2.cancel()
            break
    assert not q.empty()

def test_correct_exit2():
    q = Queue()
    p = Process(target=start_irace, args=(q, scenario2))
    p.start()
    t1 = Timer(20, sigterm_process, args=(p,))
    t2 = Timer(21, sigkill_process, args=(p,))
    t1.start()
    t2.start()
    for i in range(22):
        sleep(1)
        if not p.is_alive():
            t1.cancel()
            t2.cancel()
            break
    assert not q.empty()
