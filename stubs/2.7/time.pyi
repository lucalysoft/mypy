"""Stub file for the 'time' module."""
# based on autogenerated stub from typeshed and https://docs.python.org/2/library/time.html

from typing import NamedTuple, Tuple, Union

# ----- variables and constants -----
accept2dyear = False 
altzone = 0
daylight = 0
timezone = 0
tzname = ... # type: Tuple[str, str]

struct_time = NamedTuple('struct_time',
                         [('tm_year', int), ('tm_mon', int), ('tm_mday', int),
                          ('tm_hour', int), ('tm_min', int), ('tm_sec', int),
                          ('tm_wday', int), ('tm_yday', int), ('tm_isdst', int)])

_TIME_TUPLE = Tuple[int, int, int, int, int, int, int, int, int]

def asctime(t: struct_time = None) -> str:
    raise ValueError()

def clock() -> float: ...

def ctime(secs: float = None) -> str:
    raise ValueError()

def gmtime(secs: float = None) -> struct_time: ...

def localtime(secs: float = None) -> struct_time: ...

def mktime(t: struct_time) -> float:
    raise OverflowError()
    raise ValueError()

def sleep(secs: float) -> None: ...

def strftime(format: str, t: struct_time = None) -> str:
    raise MemoryError()
    raise ValueError()

def strptime(string: str, format: str = "%a %b %d %H:%M:%S %Y") -> struct_time:
    raise ValueError()

def time() -> float:
    raise IOError()

def tzset() -> None: ...
