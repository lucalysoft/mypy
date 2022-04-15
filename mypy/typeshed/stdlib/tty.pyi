import sys
from typing import IO

if sys.platform != "win32":
    __all__ = ["setraw", "setcbreak"]

    _FD = int | IO[str]

    # XXX: Undocumented integer constants
    IFLAG: int
    OFLAG: int
    CFLAG: int
    LFLAG: int
    ISPEED: int
    OSPEED: int
    CC: int
    def setraw(fd: _FD, when: int = ...) -> None: ...
    def setcbreak(fd: _FD, when: int = ...) -> None: ...
