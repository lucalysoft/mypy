import sys
from array import array
from typing import Any
from typing_extensions import Literal

DEFLATED: Literal[8]
DEF_MEM_LEVEL: int  # can change
DEF_BUF_SIZE: Literal[16384]
MAX_WBITS: int
ZLIB_VERSION: str  # can change
ZLIB_RUNTIME_VERSION: str  # can change
Z_NO_COMPRESSION: Literal[0]
Z_PARTIAL_FLUSH: Literal[1]
Z_BEST_COMPRESSION: Literal[9]
Z_BEST_SPEED: Literal[1]
Z_BLOCK: Literal[5]
Z_DEFAULT_COMPRESSION: Literal[-1]
Z_DEFAULT_STRATEGY: Literal[0]
Z_FILTERED: Literal[1]
Z_FINISH: Literal[4]
Z_FIXED: Literal[4]
Z_FULL_FLUSH: Literal[3]
Z_HUFFMAN_ONLY: Literal[2]
Z_NO_FLUSH: Literal[0]
Z_RLE: Literal[3]
Z_SYNC_FLUSH: Literal[2]
Z_TREES: Literal[6]

class error(Exception): ...

class _Compress:
    def compress(self, data: bytes) -> bytes: ...
    def flush(self, mode: int = ...) -> bytes: ...
    def copy(self) -> _Compress: ...

class _Decompress:
    unused_data: bytes
    unconsumed_tail: bytes
    eof: bool
    def decompress(self, data: bytes, max_length: int = ...) -> bytes: ...
    def flush(self, length: int = ...) -> bytes: ...
    def copy(self) -> _Decompress: ...

def adler32(__data: bytes, __value: int = ...) -> int: ...

if sys.version_info >= (3, 11):
    def compress(__data: bytes, level: int = ..., wbits: int = ...) -> bytes: ...

else:
    def compress(__data: bytes, level: int = ...) -> bytes: ...

def compressobj(
    level: int = ..., method: int = ..., wbits: int = ..., memLevel: int = ..., strategy: int = ..., zdict: bytes | None = ...
) -> _Compress: ...
def crc32(__data: array[Any] | bytes, __value: int = ...) -> int: ...
def decompress(__data: bytes, wbits: int = ..., bufsize: int = ...) -> bytes: ...
def decompressobj(wbits: int = ..., zdict: bytes = ...) -> _Decompress: ...
