# Builtins stub used in set-related test cases.

from typing import TypeVar, Generic, Iterator, Iterable, Set

T = TypeVar('T')

class object:
    def __init__(self) -> None: pass

class type: pass
class tuple: pass
class function: pass

class bool: pass  # needed for automatic True, False, and __debug__ definitions
class int: pass
class str: pass

class set(Iterable[T], Generic[T]):
    def __iter__(self) -> Iterator[T]: pass
    def add(self, x: T) -> None: pass
    def discard(self, x: T) -> None: pass
    def update(self, x: Set[T]) -> None: pass
