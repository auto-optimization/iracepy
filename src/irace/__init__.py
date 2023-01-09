from collections import OrderedDict
import os
import numpy as np
import pandas as pd
import traceback
import warnings
from typing import Union

import rpy2.robjects as ro
from rpy2.robjects.packages import importr, PackageNotInstalledError
from rpy2.robjects import pandas2ri,numpy2ri
from rpy2.robjects.conversion import localconverter
from rpy2 import rinterface as ri
from rpy2.rinterface_lib import na_values
from rpy2.rinterface_lib.sexp import NACharacterType
from rpy2.robjects.vectors import DataFrame, BoolVector, FloatVector, IntVector, StrVector, ListVector, IntArray, Matrix, ListSexpVector,FloatSexpVector,IntSexpVector,StrSexpVector,BoolSexpVector
from rpy2.robjects.functions import SignatureTranslatedFunction
from rpy2.rinterface import RRuntimeWarning
from .errors import irace_assert

# Re export useful Functions
from .expressions import Symbol, Min, Max, Round, Floor, Ceiling, Trunc, In, List
from .parameters import Integer, Real, Ordinal, Categorical, Param, Parameters

rpy2conversion = ro.conversion.get_conversion()
irace_converter =  ro.default_converter + numpy2ri.converter + pandas2ri.converter
# FIXME: Make this the same as irace_converter. See https://github.com/auto-optimization/iracepy/issues/31.
irace_converter_hack = numpy2ri.converter + ro.default_converter

@irace_converter.rpy2py.register(NACharacterType)
def convert(o):
    return None

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
              return rpy2conversion.rpy2py(data)  
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

def make_target_runner(context):
    @ri.rternalize
    def tmp_r_target_runner(experiment, scenario):
        py_scenario = context['py_scenario']
        py_experiment = r_to_python(experiment)
        # FIXME: How to skip this conversion?
        py_experiment['configuration'] = py_experiment['configuration'].to_dict('records')[0]
        # FIXME: We should also filter 'switches'
        # Filter all the NaN from keys in the dictionary
        py_experiment['configuration'] = OrderedDict(
            (k,v) for k,v in py_experiment['configuration'].items() if not pd.isna(v)
        )
        try:
            ret = context['py_target_runner'](py_experiment, py_scenario)
        except:
            traceback.print_exc()
            ret = dict(error=traceback.format_exc())
        return ListVector(ret)
    return tmp_r_target_runner

def check_windows(scenario):
    if scenario.get('parallel', 1) != 1 and os.name == 'nt':
        raise NotImplementedError('Parallel running on windows is not supported yet. Follow https://github.com/auto-optimization/iracepy/issues/16 for updates. Alternatively, use Linux or MacOS or the irace R package directly.')

class irace:
    # Import irace R package
    try:
        # FiXME: This may generate an R warning:
        #   library ‘/usr/local/lib/R/site-library’ contains no packages
        # How to suppress it?
        _pkg = importr("irace")
    except PackageNotInstalledError as e:
        raise PackageNotInstalledError('The R package irace needs to be installed for this python binding to work. Consider running `Rscript -e "install.packages(\'irace\', repos=\'https://cloud.r-project.org\')"` in your shell. See more details at https://github.com/mLopez-Ibanez/irace#quick-start') from e

    def __init__(self, scenario, parameters: Union[Parameters, str], target_runner):
        self.scenario = scenario
        if 'instances' in scenario:
            self.scenario['instances'] = np.asarray(scenario['instances'])
        if isinstance(parameters, Parameters):
            self.parameters = parameters._export()
        elif isinstance(parameters, str):
            with localconverter(irace_converter_hack):
                self.parameters = self._pkg.readParameters(text = parameters, digits = self.scenario.get('digits', 4))
        else:
            raise ValueError(f"parameters needs to be type irace.Parameters or string, but {type(parameters)} is found.")
        self.context = {'py_target_runner' : target_runner,
                        'py_scenario': self.scenario }
        check_windows(scenario)

    def read_configurations(self, filename=None, text=None):
        if text is None:
            confs = self._pkg.readConfigurationsFile(filename = filename, parameters = self.parameters)
        else:
            confs = self._pkg.readConfigurationsFile(text = text, parameters = self.parameters)
        with localconverter(irace_converter):
            confs = rpy2conversion.rpy2py(confs)
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
        # IMPORTANT: We need to save the output of make_target_runner in a variable or it will be garbage
        # collected by Python and crash later.
        self.r_target_runner = make_target_runner(self.context)
        self.scenario['targetRunner'] = self.r_target_runner
        with localconverter(irace_converter_hack):
            self.r_scenario = self._pkg.checkScenario(ListVector(self.scenario))
        self.scenario = r_to_python(self.r_scenario)
        self.context['py_scenario'] = self.scenario
        # According to Deyao, keeping r_target_runner in the python scenario
        # crashes `multiprocessing.Queue`. See issue https://github.com/rpy2/rpy2/issues/970
        self.scenario['targetRunner'] = None
        
        with localconverter(irace_converter):
            res = self._pkg.irace(self.r_scenario, self.parameters)
            res = rpy2conversion.rpy2py(res)
        # Remove metadata columns.
        res = res.loc[:, ~res.columns.str.startswith('.')]
        return res
