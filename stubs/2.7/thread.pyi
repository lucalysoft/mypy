from typing import Callable, Any

class error(Exception): ...
class LockType:
    def acquire(self, waitflag: int = None) -> bool: ...
    def release(self) -> None: ...
    def locked(self) -> bool: ...
    def __enter__(self) -> LockType: ...
    def __exit__(self, value: Any, traceback: Any) -> None: ...

def start_new_thread(function: Callable[..., Any], args: Any, kwargs: Any = None) -> int: ...
def interrupt_main() -> None: ...
def exit() -> None: ...
def allocate_lock() -> LockType: ...
def get_ident() -> int: ...
def stack_size(size: int = None) -> int: ...
