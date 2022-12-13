from collections import OrderedDict
import numpy as np
import pandas as pd

import os

from rpy2.robjects.packages import importr, PackageNotInstalledError
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri,numpy2ri
from rpy2.robjects.conversion import localconverter
from rpy2 import rinterface as ri
from rpy2.rinterface_lib import na_values
from rpy2.rinterface_lib.sexp import NACharacterType
from multiprocessing import Queue, Process
import json
from rpy2.rinterface_lib.sexp import NACharacterType

irace_converter =  ro.default_converter + numpy2ri.converter + pandas2ri.converter

# FIXME: Make this the same as irace_converter. See https://github.com/auto-optimization/iracepy/issues/31.
irace_converter_hack = numpy2ri.converter + ro.default_converter

@irace_converter.rpy2py.register(NACharacterType)
def convert(o):
    return None

from rpy2.robjects.vectors import DataFrame, BoolVector, FloatVector, IntVector, StrVector, ListVector, IntArray, Matrix, ListSexpVector,FloatSexpVector,IntSexpVector,StrSexpVector,BoolSexpVector
from rpy2.robjects.functions import SignatureTranslatedFunction
import traceback

base = importr('base')

# FIXME: Make this into a conversion function
def r_to_python(data):
    """
    Step through an R object recursively and convert the types to python types as appropriate. 
    Leaves will be converted to e.g. numpy arrays or lists as appropriate and the whole tree to a dictionary.
    """
    if isinstance(data, SignatureTranslatedFunction) or isinstance(data, ri.SexpClosure):
        return data  # TODO: get the actual Python function
    elif isinstance(data, np.ndarray):
        return data
    elif isinstance(data, pd.DataFrame):
        return data
    elif data == ri.NULL:
        return None
    elif data == na_values.NA_Character:
        return None
    elif hasattr(data, "rclass"):
        if data.rclass[0] == 'data.frame':
            with localconverter(irace_converter):
              return ro.conversion.rpy2py(data)  
        elif data.rclass[0] == 'list':
            with localconverter(irace_converter):
                if isinstance(data.names, ri.NULLType):
                    keys = range(len(data))
                else:
                    keys = data.names 
                return OrderedDict(zip(keys, [r_to_python(elt) for elt in data]))
        elif data.rclass[0] in ['numeric','logical','integer','RTYPES.INTSXP','array','RTYPES.LGLSXP']:
            if len(data) == 1:
                return data[0]
            return np.array(data)
        elif data.rclass[0] == 'factor':
            return r_to_python(base.as_character(data))
        elif data.rclass[0] == 'character':
            if len(data) == 1:
                if data[0] == na_values.NA_Character:
                    return None
                else:
                    return str(data[0])
            return [str(x) for x in data]
        else:
            raise KeyError(f'Could not proceed, type {type(data)} of rclass ({data.rclass[0]}) is not defined!')
    return data  # We reached the end of recursion

def run_with_catch(f, args, kwargs):
    try:
        res = f(*args, **kwargs)
    except:
        res = dict(error=traceback.format_exc())
    return res

def make_target_runner_parallel(aq: Queue, rq: Queue, check_output_target_runner, scenario_a, target_runner, has_worker):
    @ri.rternalize
    def parallel_runner(*args, **kwargs):
        try:
            experiments = list(r_to_python(args[0]).values())
            n = len(experiments)

            ans = [None for i in range(n)]
            for i, experiment in enumerate(experiments):
                # FIXME: How to skip this conversion?
                experiment['configuration'] = experiment['configuration'].to_dict('records')[0]
                # FIXME: We should also filter 'switches'
                # Filter all the NaN from keys in the dictionary
                experiment['configuration'] = OrderedDict(
                    (k,v) for k,v in experiment['configuration'].items() if not pd.isna(v)
                )
                if has_worker:
                    aq.put((i, experiment, scenario_a[0]))
                else:
                    res = run_with_catch(target_runner, (experiment, scenario_a[0]), {})
                    res = check_output_target_runner(ListVector(res), scenario_a[1])
                    ans[i] = res

            if has_worker:
                for _ in range(n):
                    i, res = rq.get()
                    with localconverter(irace_converter_hack):
                        res = check_output_target_runner(ListVector(res), scenario_a[1])
                    ans[i] = res

            return ListVector(zip(range(len(ans)), ans)) 
        except:
            # rpy2 swallows traceback from any r.rternalize function so we print it manually.
            traceback.print_exc()
            raise
    return parallel_runner

def runner_worker(target_runner, aq: Queue, rq: Queue):
    while True:
        i, experiment, scenario = aq.get()
        if i == -1:
            break
        rq.put((i, run_with_catch(target_runner, (experiment, scenario), {})))

def check_unsupported_scenarios(scenario):
    if scenario.get('targetRunnerRetries', 1) > 1:
        raise NotImplementedError("targetRunnerRetries is not yet supported by the python binding although it's supported in the irace R package. We recommend you to implement retries in your target runner.")
    if 'targetRunnerParallel' in scenario:
        raise NotImplementedError("targetRunnerParallel is not yet supported. If you need this feature, consider opening an issue to show us some people actually want to use this.")

def run_irace(irace, args, q: Queue):
    r = irace(*args)
    q.put(r)

class irace:
    # Imported R package
    try:
        _pkg = importr("irace")
    except PackageNotInstalledError as e:
        raise PackageNotInstalledError('The R package irace needs to be installed for this python binding to work. Consider running `Rscript -e "install.packages(\'irace\', repos=\'https://cloud.r-project.org\')"` in your shell. See more details at https://github.com/mLopez-Ibanez/irace#quick-start') from e

    def __init__(self, scenario, parameters_table, target_runner):
        self.scenario = scenario
        if 'instances' in scenario:
            self.scenario['instances'] = np.asarray(scenario['instances'])
        with localconverter(irace_converter_hack):
            self.parameters = self._pkg.readParameters(text = parameters_table, digits = scenario.get('digits', 4))
        # IMPORTANT: We need to save this in a variable or it will be garbage
        # collected by Python and crash later.
        self.target_runner = target_runner
        self.worker_count = max(self.scenario.get('parallel', 1), 1)
        if self.worker_count != 1:
            self.target_aq = Queue()
            self.target_rq = Queue()
        else:
            self.target_aq = None
            self.target_rq = None
        self.workers: list[Process] = []
        if self.worker_count != 1:
            for i in range(self.worker_count):
                self.workers.append(Process(target=runner_worker, args=(self.target_runner, self.target_aq, self.target_rq)))
            for worker in self.workers:
                worker.start()
            

    def read_configurations(self, filename=None, text=None):
        if text is None:
            confs = self._pkg.readConfigurationsFile(filename = filename, parameters = self.parameters)
        else:
            confs = self._pkg.readConfigurationsFile(text = text, parameters = self.parameters)
        # FIXME: can we save this converter to use it every where?
        with localconverter(irace_converter):
            confs = ro.conversion.rpy2py(confs)
        assert isinstance(confs,pd.DataFrame)
        return confs

    def set_initial_from_file(self, filename):
        with localconverter(irace_converter):
            confs = self.read_configurations(filename = filename)
        self.set_initial(confs)
        return confs
    
    def set_initial_from_str(self, text):
        with localconverter(irace_converter):
            confs = self.read_configurations(text = text)
        self.set_initial(confs)
        return confs
    
    def set_initial(self, x):
        if isinstance(x, pd.DataFrame):
            x = x.to_records(index=False)
        assert isinstance(x, np.recarray)
        self.scenario['initConfigurations'] = x
        return self
        
    def run(self):
        """Returns a Pandas DataFrame, one column per parameter and the row index are the configuration ID."""
        scenario_a = [None, None]
        self.r_target_runner_parallel = make_target_runner_parallel(self.target_aq, self.target_rq, self._pkg.check_output_target_runner, scenario_a, self.target_runner, self.worker_count != 1)
        self.scenario['targetRunnerParallel'] = self.r_target_runner_parallel

        with localconverter(irace_converter_hack):
            self.r_scenario = self._pkg.checkScenario(ListVector(self.scenario))
        self.scenario = r_to_python(self.r_scenario)
        self.scenario.pop('targetRunnerParallel', None)
        scenario_a[0] = self.scenario
        scenario_a[1] = self.r_scenario
        try:
            with localconverter(irace_converter_hack):
                res = self._pkg.irace(self.r_scenario, self.parameters)
            print(res)
        except:
            self.cleanup(True)
            raise
        self.cleanup(False)
        with localconverter(irace_converter):
            res = ro.conversion.rpy2py(res)
        # Remove metadata columns.
        res = res.loc[:, ~res.columns.str.startswith('.')]
        return res

    def cleanup(self, forced):
        if self.worker_count == 1:
            return
        if forced:
            for worker in self.workers:
                worker.terminate()
        for i in range(self.worker_count):
            self.target_aq.put((-1, None, None))
        self.target_aq.close()
        self.target_rq.close()
