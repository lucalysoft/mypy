# Stubs for msvcrt

# NOTE: These are incomplete!

from typing import overload, IO, TextIO

def get_osfhandle(file: int) -> int: pass
def open_osfhandle(handle: int, flags: int) -> int: pass
