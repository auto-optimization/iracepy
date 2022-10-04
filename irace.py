from collections import OrderedDict
import numpy as np
import pandas as pd

from rpy2.robjects.packages import importr
from rpy2.robjects import numpy2ri
numpy2ri.activate()
import rpy2.rinterface as ri
from rpy2.robjects.vectors import DataFrame, BoolVector, FloatVector, IntVector, StrVector, ListVector, IntArray, Matrix, ListSexpVector,FloatSexpVector,IntSexpVector,StrSexpVector,BoolSexpVector
from rpy2.robjects.functions import SignatureTranslatedFunction

base = importr('base')

def r_to_python(data):
    """
    Step through an R object recursively and convert the types to python types as appropriate. 
    Leaves will be converted to e.g. numpy arrays or lists as appropriate and the whole tree to a dictionary.
    """
    if isinstance(data, SignatureTranslatedFunction) or isinstance(data, ri.SexpClosure):
        return data  # TODO: get the actual Python function
    elif data == ri.NULL:
        return None
    elif hasattr(data, "rclass"):
        if data.rclass[0] in ['list','data.frame']:
            return OrderedDict(zip(data.names, [r_to_python(elt) for elt in data]))
        elif data.rclass[0] in ['numeric','logical','integer','RTYPES.INTSXP','array','RTYPES.LGLSXP']:
            if len(data) == 1:
                return data[0]
            return np.array(data)
        elif data.rclass[0] == 'factor':
            return r_to_python(base.as_character(data))
        elif data.rclass[0] == 'character':
            if len(data) == 1:
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
        ret = py_target_runner(py_experiment, py_scenario)
        # TODO: return also error codes and call for debugging.
        return ListVector(ret)
    return tmp_r_target_runner

class irace:
    # Imported R package
    _pkg = importr("irace")
    
    def __init__(self, scenario, parameters_table, target_runner):
        self.scenario = scenario
        self.parameters = self._pkg.readParameters(text = parameters_table, digits = scenario['digits'])
        # IMPORTANT: We need to save this in a variable or it will be garbage
        # collected by Python and crash later.
        self.r_target_runner = make_target_runner(target_runner)

    def read_configurations(self, filename=None, text=None):
        if text is None:
            confs = self._pkg.readConfigurationsFile(filename = filename, parameters = self.parameters)
        else:
            confs = self._pkg.readConfigurationsFile(text = text, parameters = self.parameters)
        return pd.DataFrame(confs)

    def set_initial_from_file(self, filename):
        confs = self.read_configurations(filename = filename)
        self.set_initial(confs)
        return confs
    
    def set_initial_from_str(self, text):
        confs = self.read_configurations(text = text)
        self.set_initial(confs)
        return confs
    
    def set_initial(self, x):
        if isinstance(x,pd.DataFrame):
            x = x.to_records(index=False)
        assert isinstance(x, np.recarray)
        self.scenario['initConfigurations'] = x
        return self
        
    def run(self):
        """Returns a Pandas DataFrame, one column per parameter and the row index are the configuration ID."""
        self.scenario['targetRunner'] = self.r_target_runner
        res = self._pkg.irace(ListVector(self.scenario), self.parameters)
        res = pd.DataFrame(res)
        # ID should be already strings but it seems R is storing them as
        # floating-point.
        res.index = res['.ID.'].astype(int).astype(str).values
        # Remove metadata columns.
        res = res.loc[:, ~res.columns.str.startswith('.')]
        return res
