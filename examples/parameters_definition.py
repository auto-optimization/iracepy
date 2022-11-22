from irace import Symbol, Parameters, Param, Integer, Real, Categorical, Ordinal, Min, In, List

from rpy2.robjects.packages import importr
base = importr('base')
parameters = Parameters()

parameters.algorithm = Param(Categorical(('as', 'mmas', 'eas', 'ras', 'acs')))
parameters.localsearch = Param(Categorical(('0', '1', '2', '3')))
parameters.alpha = Param(Real(0, 5))
parameters.beta = Param(Real(0, 10))
parameters.rho = Param(Real(0.01, 1))
parameters.ants = Param(Integer(5, 100, log=True))
parameters.q0 = Param(Real(0, 1), condition=Symbol('algorithm') == "acs")
parameters.rasrank = Param(Integer(1, Min(Symbol('ants'), 10)), condition=Symbol('algorithm') == 'ras')
parameters.elitistants = Param(Integer(1, Symbol('ants')), condition=Symbol('algorithm') == 'eas')
parameters.nnls = Param(Integer(5, 50), condition=List((1, 2, 3)).contains(Symbol('localsearch')))
parameters.dlbs = Param(Integer(5, 50), condition=List((1, 2, 3)).contains(Symbol('localsearch')))


a = parameters._export()

base.print(a)
