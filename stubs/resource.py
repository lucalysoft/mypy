# Stubs for resource

# NOTE: These are incomplete!

from typing import Tuple

RLIMIT_CORE = 0

def getrlimit(resource: int) -> Tuple[int, int]: pass
def setrlimit(resource: int, limits: Tuple[int, int]) -> None: pass
