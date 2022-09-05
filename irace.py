import numpy as np

from collections import OrderedDict

from rpy2.robjects.packages import importr
from rpy2.robjects import numpy2ri
numpy2ri.activate()
import rpy2.rinterface as ri
from rpy2.robjects.vectors import DataFrame, BoolVector, FloatVector, IntVector, StrVector, ListVector, IntArray, Matrix, ListSexpVector,FloatSexpVector,IntSexpVector,StrSexpVector,BoolSexpVector
from rpy2.robjects.functions import SignatureTranslatedFunction

def r_to_python(data):
    """
    Step through an R object recursively and convert the types to python types as appropriate. 
    Leaves will be converted to e.g. numpy arrays or lists as appropriate and the whole tree to a dictionary.
    """
    r_dict_types = [DataFrame, ListVector, ListSexpVector]
    r_array_types = [BoolVector, FloatVector, IntVector, Matrix, IntArray, FloatSexpVector,IntSexpVector,BoolSexpVector]
    r_list_types = [StrVector,StrSexpVector]
    if type(data) in r_dict_types:
        return OrderedDict(zip(data.names, [r_to_python(elt) for elt in data]))
    elif type(data) in r_list_types:
        if hasattr(data, "__len__") and len(data) == 1:
            return r_to_python(data[0])
        return [r_to_python(elt) for elt in data]
    elif type(data) in r_array_types:
        if hasattr(data, "__len__") and len(data) == 1:
            return data[0]
        return np.array(data)
    elif isinstance(data, SignatureTranslatedFunction) or isinstance(data, ri.SexpClosure):
        return data  # TODO: get the actual Python function
    elif data == ri.NULL:
        return None
    elif hasattr(data, "rclass"):  # An unsupported r class
        raise KeyError(f'Could not proceed, type {type(data)} is not defined! To add support for this type,'
                       ' just add it to the imports and to the appropriate type list above')
    else:
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

    def set_initial(self, configurations_table):
        confs = self._pkg.readConfigurationsFile(text = configurations_table, parameters = self.parameters)
        self.scenario['initConfigurations'] = confs
        return confs
    
    def run(self):
        self.scenario['targetRunner'] = self.r_target_runner
        res = self._pkg.irace(ListVector(self.scenario), self.parameters)
        # Convert to R object. Pandas?
        return res
