# Stubs for builtins (Python 2.7)

from typing import (
    TypeVar, Iterator, Iterable, overload,
    Sequence, Mapping, Tuple, List, Any, Dict, Callable, Generic, Set,
    AbstractSet, Sized, Reversible, SupportsInt, SupportsFloat, SupportsAbs,
    SupportsRound, IO, BinaryIO, Union, AnyStr
)
from abc import abstractmethod, ABCMeta

_T = TypeVar('_T')
_KT = TypeVar('_KT')
_VT = TypeVar('_VT')
_S = TypeVar('_S')
_T1 = TypeVar('_T1')
_T2 = TypeVar('_T2')
_T3 = TypeVar('_T3')
_T4 = TypeVar('_T4')

staticmethod = object()  # Special, only valid as a decorator.
classmethod = object()  # Special, only valid as a decorator.
property = object()

class object:
    __doc__ = ''
    __class__ = ...  # type: type

    def __init__(self) -> None: ...
    def __eq__(self, o: object) -> bool: ...
    def __ne__(self, o: object) -> bool: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __hash__(self) -> int: ...

class type:
    __name__ = ''
    __module__ = ''
    __dict__ = ...  # type: Dict[unicode, Any]

    @overload
    def __init__(self, o: object) -> None: ...
    @overload
    def __init__(self, name: str, bases: tuple, dict: Dict[str, Any]) -> None: ...
    # TODO: __new__ may have to be special and not a static method.
    @staticmethod
    def __new__(cls, name: str, bases: tuple, namespace: Dict[str, Any]) -> type: ...

class int(SupportsInt, SupportsFloat, SupportsAbs[int]):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, x: SupportsInt) -> None: ...
    @overload
    def __init__(self, x: Union[str, unicode], base: int = 10) -> None: ...
    @overload
    def __init__(self, x: bytearray, base: int = 10) -> None: ...
    def bit_length(self) -> int: ...

    def __add__(self, x: int) -> int: ...
    def __sub__(self, x: int) -> int: ...
    def __mul__(self, x: int) -> int: ...
    def __floordiv__(self, x: int) -> int: ...
    def __div__(self, x: int) -> int: ...
    def __truediv__(self, x: int) -> float: ...
    def __mod__(self, x: int) -> int: ...
    def __radd__(self, x: int) -> int: ...
    def __rsub__(self, x: int) -> int: ...
    def __rmul__(self, x: int) -> int: ...
    def __rfloordiv__(self, x: int) -> int: ...
    def __rdiv__(self, x: int) -> int: ...
    def __rtruediv__(self, x: int) -> float: ...
    def __rmod__(self, x: int) -> int: ...
    def __pow__(self, x: int) -> Any: ...  # Return type can be int or float, depending on x.
    def __rpow__(self, x: int) -> Any: ...
    def __and__(self, n: int) -> int: ...
    def __or__(self, n: int) -> int: ...
    def __xor__(self, n: int) -> int: ...
    def __lshift__(self, n: int) -> int: ...
    def __rshift__(self, n: int) -> int: ...
    def __rand__(self, n: int) -> int: ...
    def __ror__(self, n: int) -> int: ...
    def __rxor__(self, n: int) -> int: ...
    def __rlshift__(self, n: int) -> int: ...
    def __rrshift__(self, n: int) -> int: ...
    def __neg__(self) -> int: ...
    def __pos__(self) -> int: ...
    def __invert__(self) -> int: ...

    def __eq__(self, x: object) -> bool: ...
    def __ne__(self, x: object) -> bool: ...
    def __lt__(self, x: int) -> bool: ...
    def __le__(self, x: int) -> bool: ...
    def __gt__(self, x: int) -> bool: ...
    def __ge__(self, x: int) -> bool: ...

    def __str__(self) -> str: ...
    def __float__(self) -> float: ...
    def __int__(self) -> int: return self
    def __abs__(self) -> int: ...
    def __hash__(self) -> int: ...

class float(SupportsFloat, SupportsInt, SupportsAbs[float]):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, x: SupportsFloat) -> None: ...
    @overload
    def __init__(self, x: unicode) -> None: ...
    @overload
    def __init__(self, x: bytearray) -> None: ...

    def __add__(self, x: float) -> float: ...
    def __sub__(self, x: float) -> float: ...
    def __mul__(self, x: float) -> float: ...
    def __floordiv__(self, x: float) -> float: ...
    def __div__(self, x: float) -> float: ...
    def __truediv__(self, x: float) -> float: ...
    def __mod__(self, x: float) -> float: ...
    def __pow__(self, x: float) -> float: ...
    def __radd__(self, x: float) -> float: ...
    def __rsub__(self, x: float) -> float: ...
    def __rmul__(self, x: float) -> float: ...
    def __rfloordiv__(self, x: float) -> float: ...
    def __rdiv__(self, x: float) -> float: ...
    def __rtruediv__(self, x: float) -> float: ...
    def __rmod__(self, x: float) -> float: ...
    def __rpow__(self, x: float) -> float: ...

    def __eq__(self, x: object) -> bool: ...
    def __ne__(self, x: object) -> bool: ...
    def __lt__(self, x: float) -> bool: ...
    def __le__(self, x: float) -> bool: ...
    def __gt__(self, x: float) -> bool: ...
    def __ge__(self, x: float) -> bool: ...
    def __neg__(self) -> float: ...
    def __pos__(self) -> float: ...

    def __str__(self) -> str: ...
    def __int__(self) -> int: ...
    def __float__(self) -> float: return self
    def __abs__(self) -> float: ...
    def __hash__(self) -> int: ...

class complex(SupportsAbs[float]):
    @overload
    def __init__(self, re: float = 0.0, im: float = 0.0) -> None: ...
    @overload
    def __init__(self, s: str) -> None: ...

    @property
    def real(self) -> float: ...
    @property
    def imag(self) -> float: ...

    def conjugate(self) -> complex: ...

    def __add__(self, x: complex) -> complex: ...
    def __sub__(self, x: complex) -> complex: ...
    def __mul__(self, x: complex) -> complex: ...
    def __pow__(self, x: complex) -> complex: ...
    def __div__(self, x: complex) -> complex: ...
    def __truediv__(self, x: complex) -> complex: ...
    def __radd__(self, x: complex) -> complex: ...
    def __rsub__(self, x: complex) -> complex: ...
    def __rmul__(self, x: complex) -> complex: ...
    def __rpow__(self, x: complex) -> complex: ...
    def __rdiv__(self, x: complex) -> complex: ...
    def __rtruediv__(self, x: complex) -> complex: ...

    def __eq__(self, x: object) -> bool: ...
    def __ne__(self, x: object) -> bool: ...
    def __neg__(self) -> complex: ...
    def __pos__(self) -> complex: ...

    def __str__(self) -> str: ...
    def __abs__(self) -> float: ...
    def __hash__(self) -> int: ...

class basestring(metaclass=ABCMeta):
    pass

class unicode(basestring, Sequence[unicode]):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, o: object) -> None: ...
    @overload
    def __init__(self, o: str, encoding: unicode = ..., errors: unicode = 'strict') -> None: ...
    @overload
    def __init__(self, o: bytearray, encoding: unicode = ...,
                 errors: unicode = 'strict') -> None: ...
    def capitalize(self) -> unicode: ...
    def center(self, width: int, fillchar: unicode = u' ') -> unicode: ...
    def count(self, x: unicode) -> int: ...
    def decode(self, encoding: unicode = 'utf-8', errors: unicode = 'strict') -> unicode: ...
    def encode(self, encoding: unicode = 'utf-8', errors: unicode = 'strict') -> str: ...
    def endswith(self, suffix: Union[unicode, tuple], start: int = 0, end: int = ...) -> bool: ...
    def expandtabs(self, tabsize: int = 8) -> unicode: ...
    def find(self, sub: unicode, start: int = 0, end: int = 0) -> int: ...
    def format(self, *args: Any, **kwargs: Any) -> unicode: ...
    def format_map(self, map: Mapping[unicode, Any]) -> unicode: ...
    def index(self, sub: unicode, start: int = 0, end: int = 0) -> int: ...
    def isalnum(self) -> bool: ...
    def isalpha(self) -> bool: ...
    def isdecimal(self) -> bool: ...
    def isdigit(self) -> bool: ...
    def isidentifier(self) -> bool: ...
    def islower(self) -> bool: ...
    def isnumeric(self) -> bool: ...
    def isprintable(self) -> bool: ...
    def isspace(self) -> bool: ...
    def istitle(self) -> bool: ...
    def isupper(self) -> bool: ...
    def join(self, iterable: Iterable[unicode]) -> unicode: ...
    def ljust(self, width: int, fillchar: unicode = u' ') -> unicode: ...
    def lower(self) -> unicode: ...
    def lstrip(self, chars: unicode = ...) -> unicode: ...
    def partition(self, sep: unicode) -> Tuple[unicode, unicode, unicode]: ...
    def replace(self, old: unicode, new: unicode, count: int = ...) -> unicode: ...
    def rfind(self, sub: unicode, start: int = 0, end: int = 0) -> int: ...
    def rindex(self, sub: unicode, start: int = 0, end: int = 0) -> int: ...
    def rjust(self, width: int, fillchar: unicode = u' ') -> unicode: ...
    def rpartition(self, sep: unicode) -> Tuple[unicode, unicode, unicode]: ...
    def rsplit(self, sep: unicode = ..., maxsplit: int = ...) -> List[unicode]: ...
    def rstrip(self, chars: unicode = ...) -> unicode: ...
    def split(self, sep: unicode = ..., maxsplit: int = ...) -> List[unicode]: ...
    def splitlines(self, keepends: bool = False) -> List[unicode]: ...
    def startswith(self, prefix: Union[unicode, tuple], start: int = 0,
                   end: int = ...) -> bool: ...
    def strip(self, chars: unicode = ...) -> unicode: ...
    def swapcase(self) -> unicode: ...
    def title(self) -> unicode: ...
    def translate(self, table: Union[Dict[int, Any], unicode]) -> unicode: ...
    def upper(self) -> unicode: ...
    def zfill(self, width: int) -> unicode: ...
    # TODO maketrans

    @overload
    def __getitem__(self, i: int) -> unicode: ...
    @overload
    def __getitem__(self, s: slice) -> unicode: ...
    def __getslice__(self, start: int, stop: int) -> unicode: ...
    def __add__(self, s: unicode) -> unicode: ...
    def __mul__(self, n: int) -> unicode: ...
    def __mod__(self, *args: Any) -> unicode: ...
    def __eq__(self, x: object) -> bool: ...
    def __ne__(self, x: object) -> bool: ...
    def __lt__(self, x: unicode) -> bool: ...
    def __le__(self, x: unicode) -> bool: ...
    def __gt__(self, x: unicode) -> bool: ...
    def __ge__(self, x: unicode) -> bool: ...

    def __len__(self) -> int: ...
    def __contains__(self, s: object) -> bool: ...
    def __iter__(self) -> Iterator[unicode]: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __int__(self) -> int: ...
    def __float__(self) -> float: ...
    def __hash__(self) -> int: ...

class str(basestring, Sequence[str]):
    def __init__(self, object: object) -> None: ...
    def capitalize(self) -> str: ...
    def center(self, width: int, fillchar: Union[str, bytearray] = ...) -> str: ...
    def count(self, x: Union[unicode, bytearray]) -> int: ...
    def decode(self, encoding: unicode = 'utf-8', errors: unicode = 'strict') -> unicode: ...
    def encode(self, encoding: unicode = 'utf-8', errors: unicode = 'strict') -> str: ...
    def endswith(self, suffix: Union[unicode, bytearray]) -> bool: ...
    def expandtabs(self, tabsize: int = 8) -> str: ...
    def find(self, sub: Union[unicode, bytearray], start: int = 0, end: int = 0) -> int: ...
    def format(self, *args: Any) -> str: ...
    def index(self, sub: Union[unicode, bytearray], start: int = 0, end: int = 0) -> int: ...
    def isalnum(self) -> bool: ...
    def isalpha(self) -> bool: ...
    def isdigit(self) -> bool: ...
    def islower(self) -> bool: ...
    def isspace(self) -> bool: ...
    def istitle(self) -> bool: ...
    def isupper(self) -> bool: ...
    def join(self, iterable: Iterable[AnyStr]) -> AnyStr: ...
    def ljust(self, width: int, fillchar: Union[str, bytearray] = ...) -> str: ...
    def lower(self) -> str: ...
    @overload
    def lstrip(self, chars: Union[str, bytearray] = ...) -> str: ...
    @overload
    def lstrip(self, chars: unicode) -> unicode: ...
    @overload
    def partition(self, sep: str) -> Tuple[str, str, str]: ...
    @overload
    def partition(self, sep: bytearray) -> Tuple[str, bytearray, str]: ...
    @overload
    def partition(self, sep: unicode) -> Tuple[unicode, unicode, unicode]: ...
    @overload
    def replace(self, old: Union[str, bytearray], new: Union[str, bytearray],
                count: int = ...) -> str: ...
    @overload
    def replace(self, old: unicode, new: unicode, count: int = ...) -> unicode: ...
    def rfind(self, sub: Union[unicode, bytearray], start: int = 0, end: int = 0) -> int: ...
    def rindex(self, sub: Union[unicode, bytearray], start: int = 0, end: int = 0) -> int: ...
    def rjust(self, width: int, fillchar: Union[str, bytearray] = ...) -> str: ...
    @overload
    def rpartition(self, sep: str) -> Tuple[str, str, str]: ...
    @overload
    def rpartition(self, sep: bytearray) -> Tuple[str, bytearray, str]: ...
    @overload
    def rpartition(self, sep: unicode) -> Tuple[unicode, unicode, unicode]: ...
    @overload
    def rsplit(self, sep: Union[str, bytearray] = ..., maxsplit: int = ...) -> List[str]: ...
    @overload
    def rsplit(self, sep: unicode, maxsplit: int = ...) -> List[unicode]: ...
    @overload
    def rstrip(self, chars: Union[str, bytearray] = ...) -> str: ...
    @overload
    def rstrip(self, chars: unicode) -> unicode: ...
    @overload
    def split(self, sep: Union[str, bytearray] = ..., maxsplit: int = ...) -> List[str]: ...
    @overload
    def split(self, sep: unicode, maxsplit: int = ...) -> List[unicode]: ...
    def splitlines(self, keepends: bool = False) -> List[str]: ...
    def startswith(self, prefix: Union[unicode, bytearray]) -> bool: ...
    @overload
    def strip(self, chars: Union[str, bytearray] = ...) -> str: ...
    @overload
    def strip(self, chars: unicode) -> unicode: ...
    def swapcase(self) -> str: ...
    def title(self) -> str: ...
    @overload
    def translate(self, table: Union[str, bytearray], deletechars: Union[str, bytearray] = None) -> str: ...
    @overload
    def translate(self, table: unicode, deletechars: str = ...) -> unicode: ...
    def upper(self) -> str: ...
    def zfill(self, width: int) -> str: ...
    # TODO fromhex
    # TODO maketrans

    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[str]: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __int__(self) -> int: ...
    def __float__(self) -> float: ...
    def __hash__(self) -> int: ...
    @overload
    def __getitem__(self, i: int) -> str: ...
    @overload
    def __getitem__(self, s: slice) -> str: ...
    def __getslice__(self, start: int, stop: int) -> str: ...
    @overload
    def __add__(self, s: str) -> str: ...
    @overload
    def __add__(self, s: bytearray) -> str: ...
    @overload
    def __add__(self, s: unicode) -> unicode: ...
    def __mul__(self, n: int) -> str: ...
    def __rmul__(self, n: int) -> str: ...
    def __contains__(self, o: object) -> bool: ...
    def __eq__(self, x: object) -> bool: ...
    def __ne__(self, x: object) -> bool: ...
    def __lt__(self, x: unicode) -> bool: ...
    def __le__(self, x: unicode) -> bool: ...
    def __gt__(self, x: unicode) -> bool: ...
    def __ge__(self, x: unicode) -> bool: ...

class bytearray(Sequence[int]):
    @overload
    def __init__(self, ints: Iterable[int]) -> None: ...
    @overload
    def __init__(self, string: unicode, encoding: unicode,
                 errors: unicode = 'strict') -> None: ...
    @overload
    def __init__(self, length: int) -> None: ...
    @overload
    def __init__(self) -> None: ...
    def capitalize(self) -> bytearray: ...
    @overload
    def center(self, width: int, fillchar: str = ...) -> bytearray: ...
    @overload
    def center(self, width: int, fillchar: bytearray = ...) -> bytearray: ...
    @overload
    def count(self, x: str) -> int: ...
    @overload
    def count(self, x: bytearray) -> int: ...
    def decode(self, encoding: unicode = 'utf-8', errors: unicode = 'strict') -> str: ...
    @overload
    def endswith(self, suffix: str) -> bool: ...
    @overload
    def endswith(self, suffix: bytearray) -> bool: ...
    def expandtabs(self, tabsize: int = 8) -> bytearray: ...
    @overload
    def find(self, sub: str, start: int = 0) -> int: ...
    @overload
    def find(self, sub: str, start: int, end: int) -> int: ...
    @overload
    def find(self, sub: bytearray, start: int = 0) -> int: ...
    @overload
    def find(self, sub: bytearray, start: int, end: int) -> int: ...
    @overload
    def index(self, sub: str, start: int = 0) -> int: ...
    @overload
    def index(self, sub: str, start: int, end: int) -> int: ...
    @overload
    def index(self, sub: bytearray, start: int = 0) -> int: ...
    @overload
    def index(self, sub: bytearray, start: int, end: int) -> int: ...
    def isalnum(self) -> bool: ...
    def isalpha(self) -> bool: ...
    def isdigit(self) -> bool: ...
    def islower(self) -> bool: ...
    def isspace(self) -> bool: ...
    def istitle(self) -> bool: ...
    def isupper(self) -> bool: ...
    @overload
    def join(self, iterable: Iterable[str]) -> bytearray: ...
    @overload
    def join(self, iterable: Iterable[bytearray]) -> bytearray: ...
    @overload
    def ljust(self, width: int, fillchar: str = ...) -> bytearray: ...
    @overload
    def ljust(self, width: int, fillchar: bytearray = ...) -> bytearray: ...
    def lower(self) -> bytearray: ...
    @overload
    def lstrip(self, chars: str = ...) -> bytearray: ...
    @overload
    def lstrip(self, chars: bytearray = ...) -> bytearray: ...
    @overload
    def partition(self, sep: str) -> Tuple[bytearray, bytearray, bytearray]: ...
    @overload
    def partition(self, sep: bytearray) -> Tuple[bytearray, bytearray, bytearray]: ...
    @overload
    def replace(self, old: str, new: str, count: int = ...) -> bytearray: ...
    @overload
    def replace(self, old: bytearray, new: bytearray, count: int = ...) -> bytearray: ...
    @overload
    def rfind(self, sub: str, start: int = 0) -> int: ...
    @overload
    def rfind(self, sub: str, start: int, end: int) -> int: ...
    @overload
    def rfind(self, sub: bytearray, start: int = 0) -> int: ...
    @overload
    def rfind(self, sub: bytearray, start: int, end: int) -> int: ...
    @overload
    def rindex(self, sub: str, start: int = 0) -> int: ...
    @overload
    def rindex(self, sub: str, start: int, end: int) -> int: ...
    @overload
    def rindex(self, sub: bytearray, start: int = 0) -> int: ...
    @overload
    def rindex(self, sub: bytearray, start: int, end: int) -> int: ...
    @overload
    def rjust(self, width: int, fillchar: str = ...) -> bytearray: ...
    @overload
    def rjust(self, width: int, fillchar: bytearray = ...) -> bytearray: ...
    @overload
    def rpartition(self, sep: str) -> Tuple[bytearray, bytearray, bytearray]: ...
    @overload
    def rpartition(self, sep: bytearray) -> Tuple[bytearray, bytearray, bytearray]:...
    @overload
    def rsplit(self, sep: str = ..., maxsplit: int = ...) -> List[bytearray]: ...
    @overload
    def rsplit(self, sep: bytearray = ..., maxsplit: int = ...) -> List[bytearray]: ...
    @overload
    def rstrip(self, chars: str = ...) -> bytearray: ...
    @overload
    def rstrip(self, chars: bytearray = ...) -> bytearray: ...
    @overload
    def split(self, sep: str = ..., maxsplit: int = ...) -> List[bytearray]: ...
    @overload
    def split(self, sep: bytearray = ..., maxsplit: int = ...) -> List[bytearray]: ...
    def splitlines(self, keepends: bool = False) -> List[bytearray]: ...
    @overload
    def startswith(self, prefix: str) -> bool: ...
    @overload
    def startswith(self, prefix: bytearray) -> bool: ...
    @overload
    def strip(self, chars: str = ...) -> bytearray: ...
    @overload
    def strip(self, chars: bytearray = ...) -> bytearray: ...
    def swapcase(self) -> bytearray: ...
    def title(self) -> bytearray: ...
    @overload
    def translate(self, table: str) -> bytearray: ...
    @overload
    def translate(self, table: bytearray) -> bytearray: ...
    def upper(self) -> bytearray: ...
    def zfill(self, width: int) -> bytearray: ...
    # TODO fromhex
    # TODO maketrans

    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[int]: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __int__(self) -> int: ...
    def __float__(self) -> float: ...
    def __hash__(self) -> int: ...
    @overload
    def __getitem__(self, i: int) -> int: ...
    @overload
    def __getitem__(self, s: slice) -> bytearray: ...
    def __getslice__(self, start: int, stop: int) -> bytearray: ...
    @overload
    def __setitem__(self, i: int, x: int) -> None: ...
    @overload
    def __setitem__(self, s: slice, x: Sequence[int]) -> None: ...
    def __setslice__(self, start: int, stop: int, x: Sequence[int]) -> None: ...
    @overload
    def __delitem__(self, i: int) -> None: ...
    @overload
    def __delitem__(self, s: slice) -> None: ...
    def __delslice__(self, start: int, stop: int) -> None: ...
    @overload
    def __add__(self, s: str) -> bytearray: ...
    @overload
    def __add__(self, s: bytearray) -> bytearray: ...
    def __mul__(self, n: int) -> bytearray: ...
    def __contains__(self, o: object) -> bool: ...
    def __eq__(self, x: object) -> bool: ...
    def __ne__(self, x: object) -> bool: ...
    @overload
    def __lt__(self, x: bytearray) -> bool: ...
    @overload
    def __lt__(self, x: str) -> bool: ...
    @overload
    def __le__(self, x: bytearray) -> bool: ...
    @overload
    def __le__(self, x: str) -> bool: ...
    @overload
    def __gt__(self, x: bytearray) -> bool: ...
    @overload
    def __gt__(self, x: str) -> bool: ...
    @overload
    def __ge__(self, x: bytearray) -> bool: ...
    @overload
    def __ge__(self, x: str) -> bool: ...

class bool(int, SupportsInt, SupportsFloat):
    def __init__(self, o: object = False) -> None: ...

class slice:
    start = 0
    step = 0
    stop = 0
    def __init__(self, start: int, stop: int, step: int) -> None: ...

class tuple(Sequence[Any]):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, iterable: Iterable[Any]) -> None: ...
    def __len__(self) -> int: ...
    def __contains__(self, x: object) -> bool: ...
    @overload
    def __getitem__(self, x: int) -> Any: ...
    @overload
    def __getitem__(self, x: slice) -> tuple: ...
    def __iter__(self) -> Iterator[Any]: ...
    def __lt__(self, x: tuple) -> bool: ...
    def __le__(self, x: tuple) -> bool: ...
    def __gt__(self, x: tuple) -> bool: ...
    def __ge__(self, x: tuple) -> bool: ...
    def __add__(self, x: tuple) -> tuple: ...
    def count(self, x: Any) -> int: ...
    def index(self, x: Any) -> int: ...

class function:
    # TODO name of the class (corresponds to Python 'function' class)
    __name__ = ''
    __module__ = ''

class list(Sequence[_T], Reversible[_T], Generic[_T]):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, iterable: Iterable[_T]) -> None: ...
    def append(self, object: _T) -> None: ...
    def extend(self, iterable: Iterable[_T]) -> None: ...
    def pop(self, index: int = -1) -> _T: ...
    def index(self, object: _T, start: int = 0, stop: int = ...) -> int: ...
    def count(self, object: _T) -> int: ...
    def insert(self, index: int, object: _T) -> None: ...
    def remove(self, object: _T) -> None: ...
    def reverse(self) -> None: ...
    def sort(self, *, key: Callable[[_T], Any] = ..., reverse: bool = False) -> None: ...

    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[_T]: ...
    def __str__(self) -> str: ...
    def __hash__(self) -> int: ...
    @overload
    def __getitem__(self, i: int) -> _T: ...
    @overload
    def __getitem__(self, s: slice) -> List[_T]: ...
    def __getslice__(self, start: int, stop: int) -> List[_T]: ...
    @overload
    def __setitem__(self, i: int, o: _T) -> None: ...
    @overload
    def __setitem__(self, s: slice, o: Sequence[_T]) -> None: ...
    def __setslice__(self, start: int, stop: int, o: Sequence[_T]) -> None: ...
    @overload
    def __delitem__(self, i: int) -> None: ...
    @overload
    def __delitem__(self, s: slice) -> None: ...
    def __delslice(self, start: int, stop: int) -> None: ...
    def __add__(self, x: List[_T]) -> List[_T]: ...
    def __mul__(self, n: int) -> List[_T]: ...
    def __rmul__(self, n: int) -> List[_T]: ...
    def __contains__(self, o: object) -> bool: ...
    def __reversed__(self) -> Iterator[_T]: ...
    def __gt__(self, x: List[_T]) -> bool: ...
    def __ge__(self, x: List[_T]) -> bool: ...
    def __lt__(self, x: List[_T]) -> bool: ...
    def __le__(self, x: List[_T]) -> bool: ...

class dict(Mapping[_KT, _VT], Generic[_KT, _VT]):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, map: Mapping[_KT, _VT]) -> None: ...
    @overload
    def __init__(self, iterable: Iterable[Tuple[_KT, _VT]]) -> None: ...  # TODO keyword args

    def has_key(self, k: _KT) -> bool: ...
    def clear(self) -> None: ...
    def copy(self) -> Dict[_KT, _VT]: ...
    def get(self, k: _KT, default: _VT = None) -> _VT: ...
    @overload
    def pop(self, k: _KT) -> _VT: ...
    @overload
    def pop(self, k: _KT, default: _VT) -> _VT: ...
    def popitem(self) -> Tuple[_KT, _VT]: ...
    @overload
    def setdefault(self, k: _KT) -> _VT: ...
    @overload
    def setdefault(self, k: _KT, default: _VT) -> _VT: ...
    @overload
    def update(self, m: Mapping[_KT, _VT]) -> None: ...
    @overload
    def update(self, m: Iterable[Tuple[_KT, _VT]]) -> None: ...
    def keys(self) -> List[_KT]: ...
    def values(self) -> List[_VT]: ...
    def items(self) -> List[Tuple[_KT, _VT]]: ...
    def iterkeys(self) -> Iterator[_KT]: ...
    def itervalues(self) -> Iterator[_VT]: ...
    def iteritems(self) -> Iterator[Tuple[_KT, _VT]]: ...
    def __len__(self) -> int: ...
    def __getitem__(self, k: _KT) -> _VT: ...
    def __setitem__(self, k: _KT, v: _VT) -> None: ...
    def __delitem__(self, v: _KT) -> None: ...
    def __contains__(self, o: object) -> bool: ...
    def __iter__(self) -> Iterator[_KT]: ...
    def __str__(self) -> str: ...

class set(AbstractSet[_T], Generic[_T]):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, iterable: Iterable[_T]) -> None: ...
    def add(self, element: _T) -> None: ...
    def remove(self, element: _T) -> None: ...
    def copy(self) -> AbstractSet[_T]: ...
    def isdisjoint(self, s: AbstractSet[_T]) -> bool: ...
    def update(self, s: AbstractSet[_T]) -> None: ...
    def difference_update(self, s: AbstractSet[_T]) -> None: ...
    def intersection_update(self, s: AbstractSet[_T]) -> None: ...
    def __len__(self) -> int: ...
    def __contains__(self, o: object) -> bool: ...
    def __iter__(self) -> Iterator[_T]: ...
    def __str__(self) -> str: ...
    def __and__(self, s: AbstractSet[_T]) -> AbstractSet[_T]: ...
    def __or__(self, s: AbstractSet[_S]) -> AbstractSet[Union[_T, _S]]: ...
    def __sub__(self, s: AbstractSet[_T]) -> AbstractSet[_T]: ...
    def __xor__(self, s: AbstractSet[_S]) -> AbstractSet[Union[_T, _S]]: ...
    # TODO more set operations

class frozenset(AbstractSet[_T], Generic[_T]):
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, iterable: Iterable[_T]) -> None: ...
    def isdisjoint(self, s: AbstractSet[_T]) -> bool: ...
    def __len__(self) -> int: ...
    def __contains__(self, o: object) -> bool: ...
    def __iter__(self) -> Iterator[_T]: ...
    def __str__(self) -> str: ...
    def __and__(self, s: AbstractSet[_T]) -> frozenset[_T]: ...
    def __or__(self, s: AbstractSet[_S]) -> frozenset[Union[_T, _S]]: ...
    def __sub__(self, s: AbstractSet[_T]) -> frozenset[_T]: ...
    def __xor__(self, s: AbstractSet[_S]) -> frozenset[Union[_T, _S]]: ...
    # TODO more set operations

class enumerate(Iterator[Tuple[int, _T]], Generic[_T]):
    def __init__(self, iterable: Iterable[_T], start: int = 0) -> None: ...
    def __iter__(self) -> Iterator[Tuple[int, _T]]: ...
    def next(self) -> Tuple[int, _T]: ...
    # TODO __getattribute__

class xrange(Sized, Iterable[int], Reversible[int]):
    @overload
    def __init__(self, stop: int) -> None: ...
    @overload
    def __init__(self, start: int, stop: int, step: int = 1) -> None: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[int]: ...
    def __getitem__(self, i: int) -> int: ...
    def __reversed__(self) -> Iterator[int]: ...

class module:
    __name__ = ''
    __file__ = ''
    __dict__ = ...  # type: Dict[unicode, Any]

True = ...  # type: bool
False = ...  # type: bool
__debug__ = False

long = int
bytes = str

NotImplemented = ...  # type: Any

def abs(n: SupportsAbs[_T]) -> _T: ...
def all(i: Iterable) -> bool: ...
def any(i: Iterable) -> bool: ...
def bin(number: int) -> str: ...
def callable(o: object) -> bool: ...
def chr(code: int) -> str: ...
def delattr(o: Any, name: unicode) -> None: ...
def dir(o: object = ...) -> List[str]: ...
@overload
def divmod(a: int, b: int) -> Tuple[int, int]: ...
@overload
def divmod(a: float, b: float) -> Tuple[float, float]: ...
def exit(code: int = ...) -> None: ...
def filter(function: Callable[[_T], Any],
           iterable: Iterable[_T]) -> List[_T]: ...
def format(o: object, format_spec: str = '') -> str: ...  # TODO unicode
def getattr(o: Any, name: unicode, default: Any = None) -> Any: ...
def hasattr(o: Any, name: unicode) -> bool: ...
def hash(o: object) -> int: ...
def hex(i: int) -> str: ...  # TODO __index__
def id(o: object) -> int: ...
def input(prompt: unicode = ...) -> Any: ...
def intern(string: str) -> str: ...
@overload
def iter(iterable: Iterable[_T]) -> Iterator[_T]: ...
@overload
def iter(function: Callable[[], _T], sentinel: _T) -> Iterator[_T]: ...
@overload
def isinstance(o: object, t: type) -> bool: ...
@overload
def isinstance(o: object, t: tuple) -> bool: ...
def issubclass(cls: type, classinfo: type) -> bool: ...
# TODO support this
#def issubclass(type cld, classinfo: Sequence[type]) -> bool: ...
def len(o: Sized) -> int: ...
@overload
def map(func: Callable[[_T1], _S], iter1: Iterable[_T1]) -> List[_S]: ...
@overload
def map(func: Callable[[_T1, _T2], _S],
        iter1: Iterable[_T1],
        iter2: Iterable[_T2]) -> List[_S]: ...  # TODO more than two iterables
@overload
def max(iterable: Iterable[_T]) -> _T: ...  # TODO keyword argument key
@overload
def max(arg1: _T, arg2: _T, *args: _T) -> _T: ...
# TODO memoryview
@overload
def min(iterable: Iterable[_T]) -> _T: ...
@overload
def min(arg1: _T, arg2: _T, *args: _T) -> _T: ...
@overload
def next(i: Iterator[_T]) -> _T: ...
@overload
def next(i: Iterator[_T], default: _T) -> _T: ...
def oct(i: int) -> str: ...  # TODO __index__
@overload
def open(file: str, mode: str = 'r', buffering: int = ...) -> BinaryIO: ...
@overload
def open(file: unicode, mode: str = 'r', buffering: int = ...) -> BinaryIO: ...
@overload
def open(file: int, mode: str = 'r', buffering: int = ...) -> BinaryIO: ...
@overload
def ord(c: unicode) -> int: ...
@overload
def ord(c: bytearray) -> int: ...
# This is only available after from __future__ import print_function.
def print(*values: Any, sep: unicode = u' ', end: unicode = u'\n',
           file: IO[Any] = ...) -> None: ...
@overload
def pow(x: int, y: int) -> Any: ...  # The return type can be int or float, depending on y.
@overload
def pow(x: int, y: int, z: int) -> Any: ...
@overload
def pow(x: float, y: float) -> float: ...
@overload
def pow(x: float, y: float, z: float) -> float: ...
def quit(code: int = ...) -> None: ...
def range(x: int, y: int = 0, step: int = 1) -> List[int]: ...
def raw_input(prompt: unicode = ...) -> str: ...

def reduce(function: Callable[[_T, _T], _T], iterable: Iterable[_T], initializer: _T = None) -> _T: ...

def reload(module: Any) -> Any: ...
@overload
def reversed(object: Reversible[_T]) -> Iterator[_T]: ...
@overload
def reversed(object: Sequence[_T]) -> Iterator[_T]: ...
def repr(o: object) -> str: ...
@overload
def round(number: float) -> int: ...
@overload
def round(number: float, ndigits: int) -> float: ...  # Always return a float if given ndigits.
@overload
def round(number: SupportsRound[_T]) -> _T: ...
@overload
def round(number: SupportsRound[_T], ndigits: int) -> _T: ...
def setattr(object: Any, name: unicode, value: Any) -> None: ...
def sorted(iterable: Iterable[_T], *,
           cmp: Callable[[_T, _T], int] = ...,
           key: Callable[[_T], Any] = ...,
           reverse: bool = False) -> List[_T]: ...
def sum(iterable: Iterable[_T], start: _T = ...) -> _T: ...
def unichr(i: int) -> unicode: ...
def vars(object: Any = ...) -> Dict[str, Any]: ...
@overload
def zip(iter1: Iterable[_T1]) -> List[Tuple[_T1]]: ...
@overload
def zip(iter1: Iterable[_T1],
        iter2: Iterable[_T2]) -> List[Tuple[_T1, _T2]]: ...
@overload
def zip(iter1: Iterable[_T1], iter2: Iterable[_T2],
        iter3: Iterable[_T3]) -> List[Tuple[_T1, _T2, _T3]]: ...
@overload
def zip(iter1: Iterable[_T1], iter2: Iterable[_T2], iter3: Iterable[_T3],
        iter4: Iterable[_T4]) -> List[Tuple[_T1, _T2,
                                           _T3, _T4]]: ...  # TODO more than four iterables
def __import__(name: unicode,
               globals: Dict[str, Any] = ...,
               locals: Dict[str, Any] = ...,
               fromlist: List[str] = ..., level: int = ...) -> Any: ...

def globals() -> Dict[str, Any]: ...

# TODO: buffer support is incomplete; e.g. some_string.startswith(some_buffer) doesn't type check.
AnyBuffer = TypeVar('AnyBuffer', str, unicode, bytearray, buffer)

class buffer(Sized):
    def __init__(self, object: AnyBuffer, offset: int = ..., size: int = ...) -> None: ...
    def __add__(self, other: AnyBuffer) -> str: ...
    def __cmp__(self, other: AnyBuffer) -> bool: ...
    def __getitem__(self, key: Union[int, slice]) -> str: ...
    def __getslice__(self, i: int, j: int) -> str: ...
    def __len__(self) -> int: ...
    def __mul__(self, x: int) -> str: ...

class BaseException:
    args = ...  # type: Any
    def __init__(self, *args: Any) -> None: ...
    def with_traceback(self, tb: Any) -> BaseException: ...
class GeneratorExit(BaseException): ...
class KeyboardInterrupt(BaseException): ...
class SystemExit(BaseException):
    code = 0
class Exception(BaseException): ...
class StopIteration(Exception): ...
class StandardError(Exception): ...
class ArithmeticError(StandardError): ...
class EnvironmentError(StandardError):
    errno = 0
    strerror = ''
    filename = '' # TODO can this be unicode?
class LookupError(StandardError): ...
class RuntimeError(StandardError): ...
class ValueError(StandardError): ...
class AssertionError(StandardError): ...
class AttributeError(StandardError): ...
class EOFError(StandardError): ...
class FloatingPointError(ArithmeticError): ...
class IOError(EnvironmentError): ...
class ImportError(StandardError): ...
class IndexError(LookupError): ...
class KeyError(LookupError): ...
class MemoryError(StandardError): ...
class NameError(StandardError): ...
class NotImplementedError(RuntimeError): ...
class OSError(EnvironmentError): ...
class WindowsError(OSError): ...
class OverflowError(ArithmeticError): ...
class ReferenceError(StandardError): ...
class SyntaxError(StandardError): ...
class IndentationError(SyntaxError): ...
class TabError(IndentationError): ...
class SystemError(StandardError): ...
class TypeError(StandardError): ...
class UnboundLocalError(NameError): ...
class UnicodeError(ValueError): ...
class UnicodeDecodeError(UnicodeError): ...
class UnicodeEncodeError(UnicodeError): ...
class UnicodeTranslateError(UnicodeError): ...
class ZeroDivisionError(ArithmeticError): ...

class Warning(Exception): ...
class UserWarning(Warning): ...
class DeprecationWarning(Warning): ...
class SyntaxWarning(Warning): ...
class RuntimeWarning(Warning): ...
class FutureWarning(Warning): ...
class PendingDeprecationWarning(Warning): ...
class ImportWarning(Warning): ...
class UnicodeWarning(Warning): ...
class BytesWarning(Warning): ...
class ResourceWarning(Warning): ...

def eval(s: str) -> Any: ...

def cmp(x: Any, y: Any) -> int: ...

def execfile(filename: str, globals: Dict[str, Any] = None, locals: Dict[str, Any] = None) -> None: ...
