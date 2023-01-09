from enum import Enum
from typing import Iterable, Union
from .errors import irace_assert, check_numbers
import re
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import StrVector, IntArray, FloatArray
from rpy2.rlike.container import TaggedList
from .expressions import Expr, True_

base = importr('base')
irace_pkg = importr('irace')

class ParameterType(Enum):
    INTEGER = 'i'
    REAL = 'r'
    ORDINAL = 'o'
    CATEGORICAL = 'c'
    INTEGER_LOG = 'i,log'
    REAL_LOG = 'r,log'

class ParameterDomain:
    pass

class Integer(ParameterDomain):
    def __init__(self, start, end, log=False):
        self.start = start
        self.end = end
        self.type = ParameterType.INTEGER_LOG if log else ParameterType.INTEGER
        check_numbers(start, end, log)
        irace_assert((isinstance(start, int) or isinstance(start, Expr)) and (isinstance(end, int) or isinstance(end, Expr)), "bounds must be integers or expressions")
    
    def export(self):
        if isinstance(self.start, Expr) or isinstance(self.end, Expr):
            return base.eval(base.parse(text = 'expression(' + repr(self.start) + ',' + repr(self.end) + ')'))
        else:
            return IntArray((self.start, self.end))

class Real(ParameterDomain):
    def __init__(self, start, end, log=False):
        start = float(start) if isinstance(start, int) else start
        self.start = start
        end = float(end) if isinstance(end, int) else end
        self.end = end
        self.type = ParameterType.REAL_LOG if log else ParameterType.REAL
        check_numbers(start, end, log)
        irace_assert((isinstance(start, float) or isinstance(start, Expr)) and (isinstance(end, float) or isinstance(end, Expr)), "bounds must be numbers or expressions")
    
    def export(self):
        if isinstance(self.start, Expr) or isinstance(self.end, Expr):
            # FIXME: Ideally floating point should not be converted to string because it will lose precision, but this seems to be the only way to construct an expression. 
            return base.eval(base.parse(text = 'expression(' + repr(self.start) + ',' + repr(self.end) + ')'))
        else:
            return FloatArray((self.start, self.end))

class Categorical(ParameterDomain):
    def __init__(self, domain: Iterable = None):
        if domain:
            self.domain = list(domain)
            self.type = ParameterType.CATEGORICAL
            irace_assert(len(set(domain)) == len(list(domain)), "domain has duplicate elements")
            for d in domain:
                irace_assert(isinstance(d, Expr) or isinstance(d, str), "domain element must be either string or expression (irace.expressions.Expr)")
        else:
            self.domain = list()

    def add_element(self, element):
        self.domain.append(element)

    def export(self):
        self.domain = list(map(lambda x: repr(x) if isinstance(x, Expr) else x, self.domain))
        return StrVector(self.domain)

class Ordinal(ParameterDomain):
    def __init__(self, domain: Iterable = None):
        if domain:
            self.domain = list(domain)
            self.type = ParameterType.ORDINAL
            for d in domain:
                irace_assert(isinstance(d, Expr) or isinstance(d, str), "domain element must be either string or expression (irace.expressions.Expr)")
            irace_assert(len(set(self.domain)) == len(self.domain), "domain has duplicate elements")
        else:
            self.domain = list()
    def add_element(self, element):
        self.domain.append(element)
    
    def export(self):
        self.domain = list(map(lambda x: repr(x) if isinstance(x, Expr) else x, self.domain))
        return StrVector(self.domain)

class Param:
    def __init__(self, domain: ParameterDomain, condition: Expr = True_(), switch = ""):
        self.domain = domain
        self.condition = condition
        self.switch = switch
    
    def set_condition(self, condition: Expr):
        self.condition = condition

class Parameters:
    def __init__(self):
        pass

    def _export(self):
        names = []
        types = []
        switches = []
        domain = []
        conditions = []
        for attr in dir(self):
            if not re.match("^__.+__$", attr) and not re.match('^_export$', attr):
                irace_assert(isinstance(getattr(self, attr), Param), f"The parameter has to be of type Param, but found {type(getattr(self, attr))}")
                names.append(attr)
                types.append(getattr(self, attr).domain.type.value)
                switches.append(getattr(self, attr).switch)
                domain.append(getattr(self, attr).domain.export())
                conditions.append(getattr(self, attr).condition.export())
        
        names = StrVector(names)
        types = StrVector(types)
        switches = StrVector(switches)
        domain = TaggedList(domain)
        conditions = TaggedList(conditions)
        return irace_pkg.readParametersData(names = names, types = types, switches = switches, domain = domain, conditions = conditions)
    