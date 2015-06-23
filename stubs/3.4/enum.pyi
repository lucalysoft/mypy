from typing import List, Any, TypeVar


class Enum:
    def __new__(cls, value: Any) -> None: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __dir__(self) -> List[str]: ...
    def __format__(self, format_spec: str) -> str: ...
    def __hash__(self) -> Any: ...
    def __reduce_ex__(self, proto: Any) -> Any: ...

    def name(self) -> str: ...
    def value(self) -> Any: ...


class IntEnum(int, Enum):
    pass


_T = TypeVar('_T')

def unique(enumeration: _T) -> _T:
    pass
