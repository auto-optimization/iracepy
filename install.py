## FIXME: This doesn't work in general, we need to find another way, maybe using "pak" of installing packages from python
# R package names
packnames = ('devtools','irace')

# import rpy2's package module
import rpy2.robjects.packages as rpackages

# import R's utility package
utils = rpackages.importr('utils')
# select a mirror for R packages
utils.chooseCRANmirror(ind=1) # select the first mirror in the list

# R vector of strings
from rpy2.robjects.vectors import StrVector
# Selectively install what needs to be installed.
# We are fancy, just because we can.
names_to_install = [x for x in packnames if not rpackages.isinstalled(x)]
if len(names_to_install) > 0:
    utils.install_packages(StrVector(names_to_install), verbose=True)

