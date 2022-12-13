from collections import OrderedDict
import numpy as np
import pandas as pd

# FIXME: Properly initialize rpy2 to run interactively or not depending on the context. See issue https://github.com/auto-optimization/iracepy/issues/21 for more details.
import os
from rpy2.rinterface import embedded
embedded._initr(interactive=False)

from rpy2.robjects.packages import importr, PackageNotInstalledError
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri,numpy2ri
numpy2ri.activate() # FIXME: This gives a deprecation warning but it is not clear how to replace it.
from rpy2.robjects.conversion import localconverter
from rpy2 import rinterface as ri
from rpy2.rinterface_lib import na_values

@ro.default_converter.rpy2py.register(ri.IntSexpVector)
def to_int(obj):
    return [int(v) if v != na_values.NA_Integer else pd.NA for v in obj]

@ro.default_converter.rpy2py.register(ri.FloatSexpVector)
def to_float(obj):
    return [float(v) if v != na_values.NA_Real else pd.NA for v in obj]

@ro.default_converter.rpy2py.register(ri.StrSexpVector)
def to_str(obj):
    return [str(v) if v != na_values.NA_Character else pd.NA for v in obj]

@ro.default_converter.rpy2py.register(ri.BoolSexpVector)
def to_bool(obj):
    return [bool(v) if v != na_values.NA_Logical else pd.NA for v in obj]

irace_converter = ro.default_converter + pandas2ri.converter

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
    elif data == ri.NULL:
        return None
    elif data == na_values.NA_Character:
        return None
    elif hasattr(data, "rclass"):
        if data.rclass[0] == 'data.frame':
            with localconverter(irace_converter):
              return ro.conversion.rpy2py(data)  
        elif data.rclass[0] == 'list':
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

def make_target_runner(py_target_runner):
    @ri.rternalize
    def tmp_r_target_runner(experiment, scenario):
        py_experiment = r_to_python(experiment)
        py_scenario = r_to_python(scenario)
        # FIXME: How to skip this conversion?
        py_experiment['configuration'] = py_experiment['configuration'].to_dict('records')[0]
        # FIXME: We should also filter 'switches'
        # Filter all the NaN from keys in the dictionary
        py_experiment['configuration'] = OrderedDict(
            (k,v) for k,v in py_experiment['configuration'].items() if not pd.isna(v)
        )
        print(py_experiment['configuration'])
        try:
            ret = py_target_runner(py_experiment, py_scenario)
        except:
            traceback.print_exc()
            ret = dict(error=traceback.format_exc())
        return ListVector(ret)
    return tmp_r_target_runner

def check_windows(scenario):
    if scenario.get('parallel', 1) != 1 and os.name == 'nt':
        raise NotImplementedError('Parallel running on windows is not supported yet. Follow https://github.com/auto-optimization/iracepy/issues/16 for updates. Alternatively, use Linux or MacOS or the irace R package directly.')

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
        self.parameters = self._pkg.readParameters(text = parameters_table, digits = scenario.get('digits', 4))
        # IMPORTANT: We need to save this in a variable or it will be garbage
        # collected by Python and crash later.
        self.r_target_runner = make_target_runner(target_runner)
        check_windows(scenario)

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
        confs = self.read_configurations(filename = filename)
        self.set_initial(confs)
        return confs
    
    def set_initial_from_str(self, text):
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
        self.scenario['targetRunner'] = self.r_target_runner
        res = self._pkg.irace(ListVector(self.scenario), self.parameters)
        with localconverter(irace_converter):
            res = ro.conversion.rpy2py(res)
        # Remove metadata columns.
        res = res.loc[:, ~res.columns.str.startswith('.')]
        return res
