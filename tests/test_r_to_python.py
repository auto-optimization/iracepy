from rpy2.robjects import r
from irace import r_to_python
from collections import OrderedDict

def test_no_name_list():
    s = r('list(1, 2, "b", 3)')
    assert r_to_python(s) == OrderedDict(zip((0, 1, 2, 3), (1, 2, 'b', 3)))
