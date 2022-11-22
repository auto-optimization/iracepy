from .errors import irace_assert, check_illegal_character
import re
from typing import Iterable
from rpy2.robjects.packages import importr
from rpy2 import robjects
from rpy2.rinterface import evalr_expr

rbase = importr('base')

robjects.r('''
 dputpy <- function(x) {
   text_con <- textConnection("output", "w")
   dput(x, text_con)
   close(text_con)
   paste(output, collapse = '')
 } ''')

dputpy = robjects.globalenv['dputpy']

class Expr:
    def __init__(self):
        pass
    
    def __hash__(self):
        return hash(repr(self))

    @classmethod
    def raw_r(cls, expr_str):
        return rbase.eval(rbase.parse(text = 'expression(' + expr_str + ')'))

    def export(self):
        return self.raw_r(repr(self))
    
    def __eq__(self, other):
        return Eq(self, other)

    def __ne__(self, other):
        return Ne(self, other)

    def __ge__(self, other):
        return Ge(self, other)

    def __gt__(self, other):
        return Gt(self, other)

    def __le__(self, other):
        return Le(self, other)

    def __lt__(self, other):
        return Lt(self, other)

    def __and__(self, other):
        return And(self, other)

    def __not__(self):
        return Not(self)

    def __add__(self, other):
        return Add(self, other)

    def __sub__(self, other):
        return Sub(self, other)

    def __mul__(self, other):
        return Mul(self, other)
    
    def __truediv__(self, other):
        return Div(self, other)

    def __mod__(self, other):
        return Mod(self, other)

class List:
    def __init__(self, element: Iterable):
        lst = list(element)
        irace_assert(all(isinstance(x, int) for x in lst) or all(isinstance(x, float) for x in lst) or all(isinstance(x, str) for x in lst), "List must be all integers, all floating points or all strings.")
        self.data = lst

    def __repr__(self):
        return str(dputpy(self.export())[0])
    
    def export(self):
        if all(isinstance(x, int) for x in self.data):
            return robjects.IntVector(self.data)
        elif all(isinstance(x, float) for x in self.data):
            return robjects.FloatVector(self.data)
        elif all(isinstance(x, str) for x in self.data):
            return robjects.StrSexpVector(self.data)
        else:
            raise ValueError("List must be all integers, all floating points or all strings.")
    
    def contains(self, element):
        return In(element, self)

class Singular(Expr):
    def __init__(self, element):
        self.element = element
        self.left_op = ''
        self.right_op = ''

    def __repr__(self):
        return "(" + self.left_op + repr(self.element) + self.right_op + ")"


class BinaryRelations(Expr):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.left_op = ''
        self.center_op = ''
        self.right_op = ''

    def __repr__(self):
        return "(" + self.left_op + repr(self.left) + self.center_op + repr(self.right) + self.right_op + ")"

class Symbol(Singular):
    def __init__(self, name):
        check_illegal_character(name)
        super().__init__(name)
    
    def __repr__(self):
        return self.element
    
    @property
    def name(self):
        return self.element


class True_(Expr):
    def __init__(self) -> None:
        pass
    
    def export(self):
        return rbase.eval(rbase.parse(text = 'TRUE'))

class Not(Singular):
    def __init__(self, element):
        super().__init__(element)
        self.left_op = '!'

class Symmetric(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)

class Eq(Symmetric):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '=='

class Ge(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '>='

class Gt(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '>'

class Le(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '<='
    
class Lt(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '<'

class Ne(Symmetric):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '!='

class Or(Symmetric):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '|'

class And(Symmetric):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '&'

class In(BinaryRelations):
    def __init__(self, left, right):
        irace_assert(isinstance(right, List), f"expected a irace.expressions.List, but found {type(right)}")
        super().__init__(left, right)
        self.center_op = '%in%'

class BinaryNamedFunction(BinaryRelations):
    def __init__(self, left, right, name):
        super().__init__(left, right)
        self.left_op = name + '('
        self.center_op = ','
        self.right_op = ')'

class SingularNamedFunction(Singular):
    def __init__(self, element, name):
        super().__init__(element)
        self.left_op = name +'('
        self.right_op = ')'

class Min(BinaryNamedFunction):
    def __init__(self, left, right):
        super().__init__(left, right, 'min')
        
class Max(BinaryNamedFunction):
    def __init__(self, left, right):
        super().__init__(left, right, 'max')

class Mul(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '*'

class Add(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '+'

class Sub(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '-'

class Div(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '/'

class Mod(BinaryRelations):
    def __init__(self, left, right):
        super().__init__(left, right)
        self.center_op = '%%'

class Round(SingularNamedFunction):
    def __init__(self, element):
        super().__init__(element, 'round')
        
class Floor(SingularNamedFunction):
    def __init__(self, element):
        super().__init__(element, 'floor')

class Ceiling(SingularNamedFunction):
    def __init__(self, element):
        super().__init__(element, 'ceiling')

class Trunc(SingularNamedFunction):
    def __init__(self, element):
        super().__init__(element, 'trunc')
