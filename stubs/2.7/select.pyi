# Stubs for select (Python 2)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any

KQ_EV_ADD = ... # type: int
KQ_EV_CLEAR = ... # type: int
KQ_EV_DELETE = ... # type: int
KQ_EV_DISABLE = ... # type: int
KQ_EV_ENABLE = ... # type: int
KQ_EV_EOF = ... # type: int
KQ_EV_ERROR = ... # type: int
KQ_EV_FLAG1 = ... # type: int
KQ_EV_ONESHOT = ... # type: int
KQ_EV_SYSFLAGS = ... # type: int
KQ_FILTER_AIO = ... # type: int
KQ_FILTER_PROC = ... # type: int
KQ_FILTER_READ = ... # type: int
KQ_FILTER_SIGNAL = ... # type: int
KQ_FILTER_TIMER = ... # type: int
KQ_FILTER_VNODE = ... # type: int
KQ_FILTER_WRITE = ... # type: int
KQ_NOTE_ATTRIB = ... # type: int
KQ_NOTE_CHILD = ... # type: int
KQ_NOTE_DELETE = ... # type: int
KQ_NOTE_EXEC = ... # type: int
KQ_NOTE_EXIT = ... # type: int
KQ_NOTE_EXTEND = ... # type: int
KQ_NOTE_FORK = ... # type: int
KQ_NOTE_LINK = ... # type: int
KQ_NOTE_LOWAT = ... # type: int
KQ_NOTE_PCTRLMASK = ... # type: int
KQ_NOTE_PDATAMASK = ... # type: int
KQ_NOTE_RENAME = ... # type: int
KQ_NOTE_REVOKE = ... # type: int
KQ_NOTE_TRACK = ... # type: int
KQ_NOTE_TRACKERR = ... # type: int
KQ_NOTE_WRITE = ... # type: int
PIPE_BUF = ... # type: int
POLLERR = ... # type: int
POLLHUP = ... # type: int
POLLIN = ... # type: int
POLLNVAL = ... # type: int
POLLOUT = ... # type: int
POLLPRI = ... # type: int
POLLRDBAND = ... # type: int
POLLRDNORM = ... # type: int
POLLWRBAND = ... # type: int
POLLWRNORM = ... # type: int
EPOLLIN = ... # type: int
EPOLLOUT = ... # type: int
EPOLLPRI = ... # type: int
EPOLLERR = ... # type: int
EPOLLHUP = ... # type: int
EPOLLET = ... # type: int
EPOLLONESHOT = ... # type: int
EPOLLRDNORM = ... # type: int
EPOLLRDBAND = ... # type: int
EPOLLWRNORM = ... # type: int
EPOLLWRBAND = ... # type: int
EPOLLMSG = ... # type: int

def poll(): ...
def select(rlist, wlist, xlist, timeout=...): ...

class error(Exception):
    characters_written = ... # type: Any
    errno = ... # type: Any
    filename = ... # type: Any
    filename2 = ... # type: Any
    strerror = ... # type: Any
    def __init__(self, *args, **kwargs): ...
    def __reduce__(self): ...

class kevent:
    data = ... # type: Any
    fflags = ... # type: Any
    filter = ... # type: Any
    flags = ... # type: Any
    ident = ... # type: Any
    udata = ... # type: Any
    __hash__ = ... # type: Any
    def __init__(self, *args, **kwargs): ...
    def __eq__(self, other): ...
    def __ge__(self, other): ...
    def __gt__(self, other): ...
    def __le__(self, other): ...
    def __lt__(self, other): ...
    def __ne__(self, other): ...

class kqueue:
    closed = ... # type: Any
    def __init__(self, *args, **kwargs): ...
    def close(self): ...
    def control(self, *args, **kwargs): ...
    def fileno(self): ...
    @classmethod
    def fromfd(cls, fd): ...

class epoll:
    def __init__(self, sizehint: int = ...) -> None: ...
    def close(self) -> None: ...
    def fileno(self) -> int: ...
    def fromfd(self, fd): ...
    def register(self, fd: int, eventmask: int = ...) -> None: ...
    def modify(self, fd: int, eventmask: int) -> None: ...
    def unregister(fd: int) -> None: ...
    def poll(timeout: float = ..., maxevents: int = ...) -> Any: ...
