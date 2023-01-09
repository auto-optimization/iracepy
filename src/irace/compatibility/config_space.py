from ..errors import irace_assert, check_illegal_character
import re
from ConfigSpace.hyperparameters import CategoricalHyperparameter, OrdinalHyperparameter, IntegerHyperparameter, FloatHyperparameter
from ..parameters import Categorical, Ordinal, Real, Integer, Parameters, Param
from ..expressions import And, Or, Eq, Not, Lt, Gt, Symbol, List
from ConfigSpace.conditions import EqualsCondition, NotEqualsCondition, LessThanCondition, GreaterThanCondition, InCondition, AndConjunction, OrConjunction

def check_parameter_name(name):
    check_illegal_character(name)
    irace_assert(not (re.match('^__.*__$', name) or re.match('^_export$', name)), f"Unfortunately, your name parameter {repr(name)} clashes with reserved names, which are '__.*__' and '_export'. Please rename the name.")

def convert_from_config_space(config_space):
    parameters = Parameters()
    for cf_param_name in config_space:
        check_parameter_name(cf_param_name)
        cf_param = config_space[cf_param_name]
        if isinstance(cf_param, CategoricalHyperparameter):
            param = Param(Categorical(cf_param.choices))
        elif isinstance(cf_param, OrdinalHyperparameter):
            param = Param(Ordinal(cf_param.sequence))
        elif isinstance(cf_param, IntegerHyperparameter):
            param = Param(Integer(cf_param.lower, cf_param.upper, log=cf_param.log))
        elif isinstance(cf_param, FloatHyperparameter):
            param = Param(Real(cf_param.lower, cf_param.upper, log=cf_param.log))
        else:
            raise NotImplementedError(f"parameter type {type(cf_param)} is currently not supported. If you are nice enough, please open an issue at https://github.com/auto-optimization/iracepy/issues.")
        
        setattr(parameters, cf_param_name, param)
    
    for name_symbol, condition in translate_conditions(config_space):
        getattr(parameters, name_symbol.name).set_condition(condition)

    return parameters

def translate_condition(config_space_condition):
    condition = config_space_condition
    if isinstance(condition, EqualsCondition):
        left = Symbol(condition.get_parents()[0].name)
        right = condition.value
        return Eq(left, right)
    elif isinstance(condition, NotEqualsCondition):
        left = Symbol(condition.get_parents()[0].name)
        right = condition.value
        return Not(Eq(left, right))
    elif isinstance(condition, LessThanCondition):
        left = Symbol(condition.get_parents()[0].name)
        right = condition.value
        return Lt(left, right)
    elif isinstance(condition, GreaterThanCondition):
        left = Symbol(condition.get_parents()[0].name)
        right = condition.value
        return Gt(left, right)
    elif isinstance(condition, InCondition):
        left = Symbol(condition.get_parents()[0].name)
        right = List(condition.value)
        return right.contains(left)
    elif isinstance(condition, AndConjunction):
        elements = condition.components
        irace_assert(len(elements) >= 2, "And condition has less than two elements?")
        res = And(translate_condition(elements[0]), translate_condition(elements[1]))
        for i in range(2, len(elements)):
            res = And(translate_condition(elements[i]), res)
        return res
    elif isinstance(condition, OrConjunction):
        elements = condition.components
        irace_assert(len(elements) >= 2, "Or condition has less than two elements?")
        res = Or(translate_condition(elements[0]), translate_condition(elements[1]))
        for i in range(2, len(elements)):
            res = Or(translate_condition(elements[i]), res)
        return res


def translate_conditions(config_space):
    con = config_space.get_conditions()
    for condition in con:
        name = condition.get_children()[0].name
        yield Symbol(name), translate_condition(condition)
