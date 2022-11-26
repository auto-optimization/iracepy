from irace import irace

def target_runner(experiment, scenario):
    return dict(cost=experiment['configuration']['one'])


params = '''
one "" r (0, 1)
'''

scenario = dict(
    instances = range(5),
    deterministic=True,
    maxExperiments = 96,
    debugLevel = 0,
    parallel = 1,
    logFile = ""
)


def test_default_digits():
    tuner = irace(scenario, params, target_runner)
    best_conf = tuner.run()
    print(best_conf)

