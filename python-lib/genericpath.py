"""
Path operations common to more than one OS
Do not use directly.  The OS specific modules import the appropriate
functions from this module themselves.
"""
import os
import stat
from typing import overload as overload_, Any, List

__all__ = ['commonprefix', 'exists', 'getatime', 'getctime', 'getmtime',
           'getsize', 'isdir', 'isfile']


# Does a path exist?
# This is false for dangling symbolic links on systems that support them.
def _exists(path):
    try:
        os.stat(path)
    except OSError:
        return False
    return True

@overload_
def exists(path: str) -> bool:
    """Test whether a path exists.  Returns False for broken symbolic links"""
    return _exists(path)

@overload_
def exists(path: bytes) -> bool:
    return _exists(path)


# This follows symbolic links, so both islink() and isdir() can be true
# for the same path ono systems that support symlinks
def _isfile(path):
    """Test whether a path is a regular file"""
    try:
        st = os.stat(path)
    except OSError:
        return False
    return stat.S_ISREG(st.st_mode)

@overload_
def isfile(path: str) -> bool:
    """Test whether a path is a regular file"""
    return _isfile(path)

@overload_
def isfile(path: bytes) -> bool:
    return _isfile(path)


# Is a path a directory?
# This follows symbolic links, so both islink() and isdir()
# can be true for the same path on systems that support symlinks
def _isdir(s):
    try:
        st = os.stat(s)
    except OSError:
        return False
    return stat.S_ISDIR(st.st_mode)

@overload_
def isdir(s: str) -> bool:
    """Return true if the pathname refers to an existing directory."""
    return _isdir(s)

@overload_
def isdir(s: bytes) -> bool:
    return _isdir(s)


@overload_
def getsize(filename: str) -> int:
    """Return the size of a file, reported by os.stat()."""
    return os.stat(filename).st_size

@overload_
def getsize(filename: bytes) -> int:
    return os.stat(filename).st_size


@overload_
def getmtime(filename: str) -> Any:
    """Return the last modification time of a file, reported by os.stat()."""
    return os.stat(filename).st_mtime

@overload_
def getmtime(filename: bytes) -> Any:
    return os.stat(filename).st_mtime


@overload_
def getatime(filename: str) -> Any:
    """Return the last access time of a file, reported by os.stat()."""
    return os.stat(filename).st_atime

@overload_
def getatime(filename: bytes) -> Any:
    return os.stat(filename).st_atime


@overload_
def getctime(filename: str) -> Any:
    """Return the metadata change time of a file, reported by os.stat()."""
    return os.stat(filename).st_ctime

@overload_
def getctime(filename: bytes) -> Any:
    return os.stat(filename).st_ctime


# Return the longest prefix of all list elements.
def _commonprefix(m):
    if not m: return ''
    s1 = min(m)
    s2 = max(m)
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1

@overload_
def commonprefix(m: List[str]) -> str:
    "Given a list of pathnames, returns the longest common leading component"
    return _commonprefix(m)

@overload_
def commonprefix(m: List[bytes]) -> bytes:
    return _commonprefix(m)


# Split a path in root and extension.
# The extension is everything starting at the last dot in the last
# pathname component; the root is everything before that.
# It is always true that root + ext == p.

# Generic implementation of splitext, to be parametrized with
# the separators
def _splitext(p, sep, altsep, extsep):
    """Split the extension from a pathname.

    Extension is everything from the last dot to the end, ignoring
    leading dots.  Returns "(root, ext)"; ext may be empty."""
    # NOTE: This code must work for text and bytes strings.

    sepIndex = p.rfind(sep)
    if altsep:
        altsepIndex = p.rfind(altsep)
        sepIndex = max(sepIndex, altsepIndex)

    dotIndex = p.rfind(extsep)
    if dotIndex > sepIndex:
        # skip all leading dots
        filenameIndex = sepIndex + 1
        while filenameIndex < dotIndex:
            if p[filenameIndex:filenameIndex+1] != extsep:
                return p[:dotIndex], p[dotIndex:]
            filenameIndex += 1

    return p, p[:0]
