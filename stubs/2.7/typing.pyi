# Stubs for typing (Python 2.7)

from abc import abstractmethod, ABCMeta

# Definitions of special type checking related constructs.  Their definition
# are not used, so their value does not matter.

cast = object()
overload = object()
Any = object()
TypeVar = object()
Generic = object()
Tuple = object()
Callable = object()
builtinclass = object()
_promote = object()
NamedTuple = object()

# Type aliases

class TypeAlias:
    # Class for defining generic aliases for library types.
    def __init__(self, target_type): pass
    def __getitem__(self, typeargs): pass

Union = TypeAlias(object)
Optional = TypeAlias(object)
List = TypeAlias(object)
Dict = TypeAlias(object)
Set = TypeAlias(object)

# Predefined type variables.
AnyStr = TypeVar('AnyStr', str, unicode)

# Abstract base classes.

# Some unconstrained type variables.  These are used by the container types.
_T = TypeVar('_T')  # Any type.
_KT = TypeVar('_KT')  # Key type.
_VT = TypeVar('_VT')  # Value type.
_T_co = TypeVar('_T_co', covariant=True)  # Any type covariant containers.
_V_co = TypeVar('_V_co', covariant=True)  # Any type covariant containers.
_VT_co = TypeVar('_VT_co', covariant=True)  # Value type covariant containers.
_T_contra = TypeVar('_T_contra', contravariant=True)  # Ditto contravariant.

# TODO Container etc.

class SupportsInt(metaclass=ABCMeta):
    @abstractmethod
    def __int__(self) -> int: pass

class SupportsFloat(metaclass=ABCMeta):
    @abstractmethod
    def __float__(self) -> float: pass

class SupportsAbs(Generic[_T]):
    @abstractmethod
    def __abs__(self) -> _T: pass

class SupportsRound(Generic[_T]):
    @abstractmethod
    def __round__(self, ndigits: int = 0) -> _T: pass

class Reversible(Generic[_T]):
    @abstractmethod
    def __reversed__(self) -> Iterator[_T]: pass

class Sized(metaclass=ABCMeta):
    @abstractmethod
    def __len__(self) -> int: pass

class Iterable(Generic[_T_co]):
    @abstractmethod
    def __iter__(self) -> Iterator[_T_co]: pass

class Iterator(Iterable[_T_co], Generic[_T_co]):
    @abstractmethod
    def next(self) -> _T_co: pass

class Sequence(Sized, Iterable[_T_co], Generic[_T_co]):
    @abstractmethod
    def __contains__(self, x: object) -> bool: pass
    @overload
    @abstractmethod
    def __getitem__(self, i: int) -> _T_co: pass
    @overload
    @abstractmethod
    def __getitem__(self, s: slice) -> Sequence[_T_co]: pass
    @abstractmethod
    def index(self, x: Any) -> int: pass
    @abstractmethod
    def count(self, x: Any) -> int: pass

class AbstractSet(Sized, Iterable[_T_co], Generic[_T_co]):
    @abstractmethod
    def __contains__(self, x: object) -> bool: pass
    # Mixin methods
    def __le__(self, s: AbstractSet[Any]) -> bool: pass
    def __lt__(self, s: AbstractSet[Any]) -> bool: pass
    def __gt__(self, s: AbstractSet[Any]) -> bool: pass
    def __ge__(self, s: AbstractSet[Any]) -> bool: pass
    def __and__(self, s: AbstractSet[Any]) -> AbstractSet[_T_co]: pass
    def __or__(self, s: AbstractSet[_T]) -> AbstractSet[Union[_T_co, _T]]: pass
    def __sub__(self, s: AbstractSet[Any]) -> AbstractSet[_T_co]: pass
    def __xor__(self, s: AbstractSet[_T]) -> AbstractSet[Union[_T_co, _T]]: pass
    # TODO: argument can be any container?
    def isdisjoint(self, s: AbstractSet[Any]) -> bool: pass

class Mapping(Sized, Iterable[_KT], Generic[_KT, _VT]):
    @abstractmethod
    def __getitem__(self, k: _KT) -> _VT: pass
    # Mixin methods
    def get(self, k: _KT, default: _VT = ...) -> _VT: pass
    def keys(self) -> list[_KT]: pass
    def values(self) -> list[_VT]: pass
    def items(self) -> list[Tuple[_KT, _VT]]: pass
    def iterkeys(self) -> Iterator[_KT]: pass
    def itervalues(self) -> Iterator[_VT]: pass
    def iteritems(self) -> Iterator[Tuple[_KT, _VT]]: pass
    def __contains__(self, o: object) -> bool: pass

# TODO: MutableMapping

class IO(Iterable[AnyStr], Generic[AnyStr]):
    # TODO detach
    # TODO use abstract properties
    @property
    def mode(self) -> str: pass
    @property
    def name(self) -> str: pass
    @abstractmethod
    def close(self) -> None: pass
    @property
    def closed(self) -> bool: pass
    @abstractmethod
    def fileno(self) -> int: pass
    @abstractmethod
    def flush(self) -> None: pass
    @abstractmethod
    def isatty(self) -> bool: pass
    # TODO what if n is None?
    @abstractmethod
    def read(self, n: int = -1) -> AnyStr: pass
    @abstractmethod
    def readable(self) -> bool: pass
    @abstractmethod
    def readline(self, limit: int = -1) -> AnyStr: pass
    @abstractmethod
    def readlines(self, hint: int = -1) -> list[AnyStr]: pass
    @abstractmethod
    def seek(self, offset: int, whence: int = 0) -> int: pass
    @abstractmethod
    def seekable(self) -> bool: pass
    @abstractmethod
    def tell(self) -> int: pass
    # TODO None should not be compatible with int
    @abstractmethod
    def truncate(self, size: int = None) -> int: pass
    @abstractmethod
    def writable(self) -> bool: pass
    # TODO buffer objects
    @abstractmethod
    def write(self, s: AnyStr) -> int: pass
    @abstractmethod
    def writelines(self, lines: Iterable[AnyStr]) -> None: pass

    @abstractmethod
    def __iter__(self) -> Iterator[AnyStr]: pass
    @abstractmethod
    def __enter__(self) -> 'IO[AnyStr]': pass
    @abstractmethod
    def __exit__(self, type, value, traceback) -> bool: pass

class BinaryIO(IO[str]):
    # TODO readinto
    # TODO read1?
    # TODO peek?
    @overload
    @abstractmethod
    def write(self, s: str) -> int: pass
    @overload
    @abstractmethod
    def write(self, s: bytearray) -> int: pass

    @abstractmethod
    def __enter__(self) -> BinaryIO: pass

class TextIO(IO[unicode]):
    # TODO use abstractproperty
    @property
    def buffer(self) -> BinaryIO: pass
    @property
    def encoding(self) -> str: pass
    @property
    def errors(self) -> str: pass
    @property
    def line_buffering(self) -> bool: pass
    @property
    def newlines(self) -> Any: pass # None, str or tuple
    @abstractmethod
    def __enter__(self) -> TextIO: pass

class Match(Generic[AnyStr]):
    pos = 0
    endpos = 0
    lastindex = 0
    lastgroup = None  # type: AnyStr
    string = None  # type: AnyStr

    # The regular expression object whose match() or search() method produced
    # this match instance.
    re = None  # type: 'Pattern[AnyStr]'

    def expand(self, template: AnyStr) -> AnyStr: pass

    @overload
    def group(self, group1: int = 0) -> AnyStr: pass
    @overload
    def group(self, group1: str) -> AnyStr: pass
    @overload
    def group(self, group1: int, group2: int,
              *groups: int) -> Sequence[AnyStr]: pass
    @overload
    def group(self, group1: str, group2: str,
              *groups: str) -> Sequence[AnyStr]: pass

    def groups(self, default: AnyStr = None) -> Sequence[AnyStr]: pass
    def groupdict(self, default: AnyStr = None) -> dict[str, AnyStr]: pass
    def start(self, group: int = 0) -> int: pass
    def end(self, group: int = 0) -> int: pass
    def span(self, group: int = 0) -> Tuple[int, int]: pass

class Pattern(Generic[AnyStr]):
    flags = 0
    groupindex = 0
    groups = 0
    pattern = None  # type: AnyStr

    def search(self, string: AnyStr, pos: int = 0,
               endpos: int = -1) -> Match[AnyStr]: pass
    def match(self, string: AnyStr, pos: int = 0,
              endpos: int = -1) -> Match[AnyStr]: pass
    def split(self, string: AnyStr, maxsplit: int = 0) -> list[AnyStr]: pass
    def findall(self, string: AnyStr, pos: int = 0,
                endpos: int = -1) -> list[AnyStr]: pass
    def finditer(self, string: AnyStr, pos: int = 0,
                 endpos: int = -1) -> Iterator[Match[AnyStr]]: pass

    @overload
    def sub(self, repl: AnyStr, string: AnyStr,
            count: int = 0) -> AnyStr: pass
    @overload
    def sub(self, repl: Callable[[Match[AnyStr]], AnyStr], string: AnyStr,
            count: int = 0) -> AnyStr: pass

    @overload
    def subn(self, repl: AnyStr, string: AnyStr,
             count: int = 0) -> Tuple[AnyStr, int]: pass
    @overload
    def subn(self, repl: Callable[[Match[AnyStr]], AnyStr], string: AnyStr,
             count: int = 0) -> Tuple[AnyStr, int]: pass
