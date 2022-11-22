import pytest
from irace import Symbol, Parameters, Param, Integer, Real, Categorical, Ordinal, Min, In, List

from rpy2.robjects.packages import importr
from irace.expressions import dputpy
base = importr('base')
irace_pkg = importr('irace')


def test_1():
    parameters = Parameters()

    parameters.algorithm = Param(Categorical(('as', 'mmas', 'eas', 'ras', 'acs')), switch="--")


    s = ''' 
    # name       switch           type  values                             [conditions (using R syntax)]
    algorithm    "--"             c     (as,mmas,eas,ras,acs)
    '''

    a = parameters._export()
    b = irace_pkg.readParameters(text = s)

    assert base.identical(a, b)[0]

def test_2():
    parameters = Parameters()

    parameters.alpha = Param(Real(0, 5), switch="--alpha ")

    s = ''' 
    # name       switch           type  values                             [conditions (using R syntax)]
    alpha        "--alpha "       r     (0.00, 5.00)
    '''

    a = parameters._export()
    b = irace_pkg.readParameters(text = s)

    assert base.identical(a, b)[0]

def test_3():
    parameters = Parameters()

    values = Categorical(('0', '1', '2'))
    values.add_element('3')
    parameters.localsearch = Param(values, switch="--localsearch ")

    s = ''' 
    # name       switch           type  values               [conditions (using R syntax)]
    localsearch  "--localsearch " c     (0, 1, 2, 3)
    '''

    a = parameters._export()
    b = irace_pkg.readParameters(text = s)
    print(dputpy(a)[0])
    print(dputpy(b)[0])

    assert base.identical(a, b)[0] 

def test_4():
    with pytest.raises(Exception):
        values = Categorical(('0', '1', '2', '2', '3', '4'))

def test_5():
    with pytest.raises(Exception):
        values = Categorical(('0', 1, 3))

def test_6():
    values = Categorical(("1", Symbol('abc') + 2))
    values.export()

def test_7():
    with pytest.raises(Exception):
        values = Categorical((1, 3, 4.0))

