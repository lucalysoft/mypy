# Stubs for pickle

# NOTE: These are incomplete!

from typing import Any

def dumps(obj: Any, protocol: int = None, *,
          fix_imports: bool = True) -> bytes: pass
def loads(p: bytes, *, fix_imports: bool = True,
          encoding: str = 'ASCII', errors: str = 'strict') -> Any: pass
