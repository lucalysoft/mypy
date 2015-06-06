# Stubs for requests.packages.urllib3._collections (Python 3.4)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any
from collections import MutableMapping

class RLock:
    def __enter__(self): pass
    def __exit__(self, exc_type, exc_value, traceback): pass

class RecentlyUsedContainer(MutableMapping):
    ContainerCls = ...  # type: Any
    dispose_func = ...  # type: Any
    lock = ...  # type: Any
    def __init__(self, maxsize=10, dispose_func=None): pass
    def __getitem__(self, key): pass
    def __setitem__(self, key, value): pass
    def __delitem__(self, key): pass
    def __len__(self): pass
    def __iter__(self): pass
    def clear(self): pass
    def keys(self): pass

class HTTPHeaderDict(dict):
    def __init__(self, headers=None, **kwargs): pass
    def __setitem__(self, key, val): pass
    def __getitem__(self, key): pass
    def __delitem__(self, key): pass
    def __contains__(self, key): pass
    def __eq__(self, other): pass
    def __ne__(self, other): pass
    values = ...  # type: Any
    get = ...  # type: Any
    update = ...  # type: Any
    iterkeys = ...  # type: Any
    itervalues = ...  # type: Any
    def pop(self, key, default=...): pass
    def discard(self, key): pass
    def add(self, key, val): pass
    def extend(*args, **kwargs): pass
    def getlist(self, key): pass
    getheaders = ...  # type: Any
    getallmatchingheaders = ...  # type: Any
    iget = ...  # type: Any
    def copy(self): pass
    def iteritems(self): pass
    def itermerged(self): pass
    def items(self): pass
    @classmethod
    def from_httplib(cls, message, duplicates=...): pass
