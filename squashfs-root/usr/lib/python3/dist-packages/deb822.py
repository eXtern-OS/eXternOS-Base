import warnings

warnings.warn("please use 'debian.deb822' instead", DeprecationWarning,
              stacklevel=2)

from debian.deb822 import *
