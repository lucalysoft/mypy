from typing import Any, BinaryIO, Callable

BOM_UTF8 = b''

class Codec: ...
class StreamWriter(Codec): ...

class CodecInfo(tuple):
    def __init__(self, *args) -> None: ...

def register(search_function: Callable[[str], CodecInfo]) -> None:
    ...

def register_error(name: str, error_handler: Callable[[UnicodeError], Any]) -> None: ...

def lookup(encoding: str) -> CodecInfo:
    ...

# TODO This Callable is actually a StreamWriter constructor
def getwriter(encoding: str) -> Callable[[BinaryIO], StreamWriter]: ...

class IncrementalDecoder:
    errors = ...  # type: Any
    def __init__(self, errors=''): ...
    def decode(self, input, final=False): ...
    def reset(self): ...
    def getstate(self): ...
    def setstate(self, state): ...
