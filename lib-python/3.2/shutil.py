"""Utility functions for copying and archiving files and directory trees.

XXX The functions here don't copy the resource fork or other metadata on Mac.

"""

import os
import sys
import stat
from os.path import abspath
import fnmatch
import collections
import errno
import tarfile
import builtins

from typing import (
    Any, AnyStr, IO, List, Iterable, Function, Tuple, Dict, Sequence, cast,
    Traceback
)

try:
    import bz2
    _BZ2_SUPPORTED = True
except ImportError:
    _BZ2_SUPPORTED = False

try:
    from pwd import getpwnam as _getpwnam
    getpwnam = _getpwnam
except ImportError:
    getpwnam = None

try:
    from grp import getgrnam as _getgrnam
    getgrnam = _getgrnam
except ImportError:
    getgrnam = None

__all__ = ["copyfileobj", "copyfile", "copymode", "copystat", "copy", "copy2",
           "copytree", "move", "rmtree", "Error", "SpecialFileError",
           "ExecError", "make_archive", "get_archive_formats",
           "register_archive_format", "unregister_archive_format",
           "get_unpack_formats", "register_unpack_format",
           "unregister_unpack_format", "unpack_archive", "ignore_patterns"]

class Error(EnvironmentError):
    pass

class SpecialFileError(EnvironmentError):
    """Raised when trying to do a kind of operation (e.g. copying) which is
    not supported on a special file (e.g. a named pipe)"""

class ExecError(EnvironmentError):
    """Raised when a command could not be executed"""

class ReadError(EnvironmentError):
    """Raised when an archive cannot be read"""

class RegistryError(Exception):
    """Raised when a registery operation with the archiving
    and unpacking registeries fails"""


try:
    _WindowsError = WindowsError # type: type
except NameError:
    _WindowsError = None


# Function aliases to be patched in test cases
rename = os.rename
open = builtins.open


def copyfileobj(fsrc: IO[AnyStr], fdst: IO[AnyStr],
                length: int = 16*1024) -> None:
    """copy data from file-like object fsrc to file-like object fdst"""
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)

def _samefile(src: str, dst: str) -> bool:
    # Macintosh, Unix.
    if hasattr(os.path, 'samefile'):
        try:
            return os.path.samefile(src, dst)
        except OSError:
            return False

    # All other platforms: check for same pathname.
    return (os.path.normcase(os.path.abspath(src)) ==
            os.path.normcase(os.path.abspath(dst)))

def copyfile(src: str, dst: str) -> None:
    """Copy data from src to dst"""
    if _samefile(src, dst):
        raise Error("`%s` and `%s` are the same file" % (src, dst))

    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if stat.S_ISFIFO(st.st_mode):
                raise SpecialFileError("`%s` is a named pipe" % fn)

    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            copyfileobj(fsrc, fdst)

def copymode(src: str, dst: str) -> None:
    """Copy mode bits from src to dst"""
    if hasattr(os, 'chmod'):
        st = os.stat(src)
        mode = stat.S_IMODE(st.st_mode)
        os.chmod(dst, mode)

def copystat(src: str, dst: str) -> None:
    """Copy all stat info (mode bits, atime, mtime, flags) from src to dst"""
    st = os.stat(src)
    mode = stat.S_IMODE(st.st_mode)
    if hasattr(os, 'utime'):
        os.utime(dst, (st.st_atime, st.st_mtime))
    if hasattr(os, 'chmod'):
        os.chmod(dst, mode)
    if hasattr(os, 'chflags') and hasattr(st, 'st_flags'):
        try:
            os.chflags(dst, st.st_flags)
        except OSError as why:
            if (not hasattr(errno, 'EOPNOTSUPP') or
                why.errno != errno.EOPNOTSUPP):
                raise

def copy(src: str, dst: str) -> None:
    """Copy data and mode bits ("cp src dst").

    The destination may be a directory.

    """
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    copyfile(src, dst)
    copymode(src, dst)

def copy2(src: str, dst: str) -> None:
    """Copy data and all stat info ("cp -p src dst").

    The destination may be a directory.

    """
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    copyfile(src, dst)
    copystat(src, dst)

def ignore_patterns(*patterns: str) -> Callable[[str, List[str]],
                                                Iterable[str]]:
    """Function that can be used as copytree() ignore parameter.

    Patterns is a sequence of glob-style patterns
    that are used to exclude files"""
    def _ignore_patterns(path: str, names: List[str]) -> Iterable[str]:
        ignored_names = List[str]()
        for pattern in patterns:
            ignored_names.extend(fnmatch.filter(names, pattern))
        return set(ignored_names)
    return _ignore_patterns

def copytree(src: str, dst: str, symlinks: bool = False,
             ignore: Callable[[str, List[str]], Iterable[str]] = None,
             copy_function: Callable[[str, str], None] = copy2,
             ignore_dangling_symlinks: bool = False) -> None:
    """Recursively copy a directory tree.

    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied. If the file pointed by the symlink doesn't
    exist, an exception will be added in the list of errors raised in
    an Error exception at the end of the copy process.

    You can set the optional ignore_dangling_symlinks flag to true if you
    want to silence this exception. Notice that this has no effect on
    platforms that don't support os.symlink.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    The optional copy_function argument is a callable that will be used
    to copy each file. It will be called with the source path and the
    destination path as arguments. By default, copy2() is used, but any
    function that supports the same signature (like copy()) can be used.

    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    os.makedirs(dst)
    errors = List[Tuple[str, str, str]]()
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.islink(srcname):
                linkto = os.readlink(srcname)
                if symlinks:
                    os.symlink(linkto, dstname)
                else:
                    # ignore dangling symlink if the flag is on
                    if not os.path.exists(linkto) and ignore_dangling_symlinks:
                        continue
                    # otherwise let the copy occurs. copy2 will raise an error
                    copy_function(srcname, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore, copy_function)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy_function(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        if _WindowsError is not None and isinstance(why, _WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise Error(errors)

def rmtree(path: str, ignore_errors: bool = False,
           onerror: Callable[[Any, str, Tuple[type, BaseException, Traceback]],
                              None] = None) -> None:
    """Recursively delete a directory tree.

    If ignore_errors is set, errors are ignored; otherwise, if onerror
    is set, it is called to handle the error with arguments (func,
    path, exc_info) where func is os.listdir, os.remove, or os.rmdir;
    path is the argument to that function that caused it to fail; and
    exc_info is a tuple returned by sys.exc_info().  If ignore_errors
    is false and onerror is None, an exception is raised.

    """
    if ignore_errors:
        def _onerror(x: Any, y: str,
                     z: Tuple[type, BaseException, Traceback]) -> None:
            pass
        onerror = _onerror
    elif onerror is None:
        def __onerror(x: Any, y: str,
                      z: Tuple[type, BaseException, Traceback]) -> None:
            raise
        onerror = __onerror
    try:
        if os.path.islink(path):
            # symlinks to directories are forbidden, see bug #1669
            raise OSError("Cannot call rmtree on a symbolic link")
    except OSError:
        onerror(os.path.islink, path, sys.exc_info())
        # can't continue even if onerror hook returns
        return
    names = List[str]()
    try:
        names = os.listdir(path)
    except os.error as err:
        onerror(os.listdir, path, sys.exc_info())
    for name in names:
        fullname = os.path.join(path, name)
        try:
            mode = os.lstat(fullname).st_mode
        except os.error:
            mode = 0
        if stat.S_ISDIR(mode):
            rmtree(fullname, ignore_errors, onerror)
        else:
            try:
                os.remove(fullname)
            except os.error as err:
                onerror(os.remove, fullname, sys.exc_info())
    try:
        os.rmdir(path)
    except os.error:
        onerror(os.rmdir, path, sys.exc_info())


def _basename(path: str) -> str:
    # A basename() variant which first strips the trailing slash, if present.
    # Thus we always get the last component of the path, even for directories.
    return os.path.basename(path.rstrip(os.path.sep))

def move(src: str, dst: str) -> None:
    """Recursively move a file or directory to another location. This is
    similar to the Unix "mv" command.

    If the destination is a directory or a symlink to a directory, the source
    is moved inside the directory. The destination path must not already
    exist.

    If the destination already exists but is not a directory, it may be
    overwritten depending on os.rename() semantics.

    If the destination is on our current filesystem, then rename() is used.
    Otherwise, src is copied to the destination and then removed.
    A lot more could be done here...  A look at a mv.c shows a lot of
    the issues this implementation glosses over.

    """
    real_dst = dst
    if os.path.isdir(dst):
        if _samefile(src, dst):
            # We might be on a case insensitive filesystem,
            # perform the rename anyway.
            os.rename(src, dst)
            return

        real_dst = os.path.join(dst, _basename(src))
        if os.path.exists(real_dst):
            raise Error("Destination path '%s' already exists" % real_dst)
    try:
        os.rename(src, real_dst)
    except OSError as exc:
        if os.path.isdir(src):
            if _destinsrc(src, dst):
                raise Error("Cannot move a directory '%s' into itself '%s'." % (src, dst))
            copytree(src, real_dst, symlinks=True)
            rmtree(src)
        else:
            copy2(src, real_dst)
            os.unlink(src)

def _destinsrc(src: str, dst: str) -> bool:
    src = abspath(src)
    dst = abspath(dst)
    if not src.endswith(os.path.sep):
        src += os.path.sep
    if not dst.endswith(os.path.sep):
        dst += os.path.sep
    return dst.startswith(src)

def _get_gid(name: str) -> int:
    """Returns a gid, given a group name."""
    if getgrnam is None or name is None:
        return None
    try:
        result = getgrnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result.gr_gid
    return None

def _get_uid(name: str) -> int:
    """Returns an uid, given a user name."""
    if getpwnam is None or name is None:
        return None
    try:
        result = getpwnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result.pw_uid
    return None

def _make_tarball(base_name: str, base_dir: str, compress: str = "gzip",
                  verbose: bool = False, dry_run: bool = False,
                  owner: str = None, group: str = None,
                  logger: Any = None) -> str:
    """Create a (possibly compressed) tar file from all the files under
    'base_dir'.

    'compress' must be "gzip" (the default), "bzip2", or None.

    'owner' and 'group' can be used to define an owner and a group for the
    archive that is being built. If not provided, the current owner and group
    will be used.

    The output tar file will be named 'base_name' +  ".tar", possibly plus
    the appropriate compression extension (".gz", or ".bz2").

    Returns the output filename.
    """
    tar_compression = {'gzip': 'gz', None: ''}
    compress_ext = {'gzip': '.gz'}

    if _BZ2_SUPPORTED:
        tar_compression['bzip2'] = 'bz2'
        compress_ext['bzip2'] = '.bz2'

    # flags for compression program, each element of list will be an argument
    if compress is not None and compress not in compress_ext.keys():
        raise ValueError("bad value for 'compress', or compression format not "
                         "supported : {0}".format(compress))

    archive_name = base_name + '.tar' + compress_ext.get(compress, '')
    archive_dir = os.path.dirname(archive_name)

    if not os.path.exists(archive_dir):
        if logger is not None:
            logger.info("creating %s", archive_dir)
        if not dry_run:
            os.makedirs(archive_dir)

    # creating the tarball
    if logger is not None:
        logger.info('Creating tar archive')

    uid = _get_uid(owner)
    gid = _get_gid(group)

    def _set_uid_gid(tarinfo):
        if gid is not None:
            tarinfo.gid = gid
            tarinfo.gname = group
        if uid is not None:
            tarinfo.uid = uid
            tarinfo.uname = owner
        return tarinfo

    if not dry_run:
        tar = tarfile.open(archive_name, 'w|%s' % tar_compression[compress])
        try:
            tar.add(base_dir, filter=_set_uid_gid)
        finally:
            tar.close()

    return archive_name

def _call_external_zip(base_dir: str, zip_filename: str, verbose: bool = False,
                       dry_run: bool = False) -> None:
    # XXX see if we want to keep an external call here
    if verbose:
        zipoptions = "-r"
    else:
        zipoptions = "-rq"
    from distutils.errors import DistutilsExecError
    from distutils.spawn import spawn
    try:
        spawn(["zip", zipoptions, zip_filename, base_dir], dry_run=dry_run)
    except DistutilsExecError:
        # XXX really should distinguish between "couldn't find
        # external 'zip' command" and "zip failed".
        raise ExecError(("unable to create zip file '%s': "
            "could neither import the 'zipfile' module nor "
            "find a standalone zip utility") % zip_filename)

def _make_zipfile(base_name: str, base_dir: str, verbose: bool = False,
                  dry_run: bool = False, logger: Any = None) -> str:
    """Create a zip file from all the files under 'base_dir'.

    The output zip file will be named 'base_name' + ".zip".  Uses either the
    "zipfile" Python module (if available) or the InfoZIP "zip" utility
    (if installed and found on the default search path).  If neither tool is
    available, raises ExecError.  Returns the name of the output zip
    file.
    """
    zip_filename = base_name + ".zip"
    archive_dir = os.path.dirname(base_name)

    if not os.path.exists(archive_dir):
        if logger is not None:
            logger.info("creating %s", archive_dir)
        if not dry_run:
            os.makedirs(archive_dir)

    # If zipfile module is not available, try spawning an external 'zip'
    # command.
    try:
        import zipfile
    except ImportError:
        zipfile = None

    if zipfile is None:
        _call_external_zip(base_dir, zip_filename, verbose, dry_run)
    else:
        if logger is not None:
            logger.info("creating '%s' and adding '%s' to it",
                        zip_filename, base_dir)

        if not dry_run:
            zip = zipfile.ZipFile(zip_filename, "w",
                                  compression=zipfile.ZIP_DEFLATED)

            for dirpath, dirnames, filenames in os.walk(base_dir):
                for name in filenames:
                    path = os.path.normpath(os.path.join(dirpath, name))
                    if os.path.isfile(path):
                        zip.write(path, path)
                        if logger is not None:
                            logger.info("adding '%s'", path)
            zip.close()

    return zip_filename

_ARCHIVE_FORMATS = {
    'gztar': (_make_tarball, [('compress', 'gzip')], "gzip'ed tar-file"),
    'tar':   (_make_tarball, [('compress', None)], "uncompressed tar file"),
    'zip':   (_make_zipfile, [],"ZIP file")
    } # type: Dict[str, Tuple[Any, Sequence[Tuple[str, str]], str]]

if _BZ2_SUPPORTED:
    _ARCHIVE_FORMATS['bztar'] = (_make_tarball, [('compress', 'bzip2')],
                                "bzip2'ed tar-file")

def get_archive_formats() -> List[Tuple[str, str]]:
    """Returns a list of supported formats for archiving and unarchiving.

    Each element of the returned sequence is a tuple (name, description)
    """
    formats = [(name, registry[2]) for name, registry in
               _ARCHIVE_FORMATS.items()]
    formats.sort()
    return formats

def register_archive_format(name: str, function: Any,
                            extra_args: Sequence[Tuple[str, Any]] = None,
                            description: str = '') -> None:
    """Registers an archive format.

    name is the name of the format. function is the callable that will be
    used to create archives. If provided, extra_args is a sequence of
    (name, value) tuples that will be passed as arguments to the callable.
    description can be provided to describe the format, and will be returned
    by the get_archive_formats() function.
    """
    if extra_args is None:
        extra_args = []
    if not callable(function):
        raise TypeError('The %s object is not callable' % function)
    if not isinstance(extra_args, (tuple, list)):
        raise TypeError('extra_args needs to be a sequence')
    for element in extra_args:
        if not isinstance(element, (tuple, list)) or len(cast(tuple, element)) !=2 :
            raise TypeError('extra_args elements are : (arg_name, value)')

    _ARCHIVE_FORMATS[name] = (function, extra_args, description)

def unregister_archive_format(name: str) -> None:
    del _ARCHIVE_FORMATS[name]

def make_archive(base_name: str, format: str, root_dir: str = None,
                 base_dir: str = None, verbose: bool = False,
                 dry_run: bool = False, owner: str = None,
                 group: str = None, logger: Any = None) -> str:
    """Create an archive file (eg. zip or tar).

    'base_name' is the name of the file to create, minus any format-specific
    extension; 'format' is the archive format: one of "zip", "tar", "bztar"
    or "gztar".

    'root_dir' is a directory that will be the root directory of the
    archive; ie. we typically chdir into 'root_dir' before creating the
    archive.  'base_dir' is the directory where we start archiving from;
    ie. 'base_dir' will be the common prefix of all files and
    directories in the archive.  'root_dir' and 'base_dir' both default
    to the current directory.  Returns the name of the archive file.

    'owner' and 'group' are used when creating a tar archive. By default,
    uses the current owner and group.
    """
    save_cwd = os.getcwd()
    if root_dir is not None:
        if logger is not None:
            logger.debug("changing into '%s'", root_dir)
        base_name = os.path.abspath(base_name)
        if not dry_run:
            os.chdir(root_dir)

    if base_dir is None:
        base_dir = os.curdir

    kwargs = {'dry_run': dry_run, 'logger': logger}

    try:
        format_info = _ARCHIVE_FORMATS[format]
    except KeyError:
        raise ValueError("unknown archive format '%s'" % format)

    func = format_info[0]
    for arg, val in format_info[1]:
        kwargs[arg] = val

    if format != 'zip':
        kwargs['owner'] = owner
        kwargs['group'] = group

    try:
        filename = func(base_name, base_dir, **kwargs)
    finally:
        if root_dir is not None:
            if logger is not None:
                logger.debug("changing back to '%s'", save_cwd)
            os.chdir(save_cwd)

    return filename


def get_unpack_formats() -> List[Tuple[str, List[str], str]]:
    """Returns a list of supported formats for unpacking.

    Each element of the returned sequence is a tuple
    (name, extensions, description)
    """
    formats = [(name, info[0], info[3]) for name, info in
               _UNPACK_FORMATS.items()]
    formats.sort()
    return formats

def _check_unpack_options(extensions: List[str], function: Any,
                          extra_args: Sequence[Tuple[str, Any]]) -> None:
    """Checks what gets registered as an unpacker."""
    # first make sure no other unpacker is registered for this extension
    existing_extensions = Dict[str, str]()
    for name, info in _UNPACK_FORMATS.items():
        for ext in info[0]:
            existing_extensions[ext] = name

    for extension in extensions:
        if extension in existing_extensions:
            msg = '%s is already registered for "%s"'
            raise RegistryError(msg % (extension,
                                       existing_extensions[extension]))

    if not callable(function):
        raise TypeError('The registered function must be a callable')


def register_unpack_format(name: str, extensions: List[str], function: Any,
                           extra_args: Sequence[Tuple[str, Any]] = None,
                           description: str = '') -> None:
    """Registers an unpack format.

    `name` is the name of the format. `extensions` is a list of extensions
    corresponding to the format.

    `function` is the callable that will be
    used to unpack archives. The callable will receive archives to unpack.
    If it's unable to handle an archive, it needs to raise a ReadError
    exception.

    If provided, `extra_args` is a sequence of
    (name, value) tuples that will be passed as arguments to the callable.
    description can be provided to describe the format, and will be returned
    by the get_unpack_formats() function.
    """
    if extra_args is None:
        extra_args = []
    _check_unpack_options(extensions, function, extra_args)
    _UNPACK_FORMATS[name] = extensions, function, extra_args, description

def unregister_unpack_format(name: str) -> None:
    """Removes the pack format from the registery."""
    del _UNPACK_FORMATS[name]

def _ensure_directory(path: str) -> None:
    """Ensure that the parent directory of `path` exists"""
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

def _unpack_zipfile(filename: str, extract_dir: str) -> None:
    """Unpack zip `filename` to `extract_dir`
    """
    try:
        import zipfile
    except ImportError:
        raise ReadError('zlib not supported, cannot unpack this archive.')

    if not zipfile.is_zipfile(filename):
        raise ReadError("%s is not a zip file" % filename)

    zip = zipfile.ZipFile(filename)
    try:
        for info in zip.infolist():
            name = info.filename

            # don't extract absolute paths or ones with .. in them
            if name.startswith('/') or '..' in name:
                continue

            target = os.path.join(extract_dir, *name.split('/'))
            if not target:
                continue

            _ensure_directory(target)
            if not name.endswith('/'):
                # file
                data = zip.read(info.filename)
                f = open(target,'wb')
                try:
                    f.write(data)
                finally:
                    f.close()
                    del data
    finally:
        zip.close()

def _unpack_tarfile(filename: str, extract_dir: str) -> None:
    """Unpack tar/tar.gz/tar.bz2 `filename` to `extract_dir`
    """
    try:
        tarobj = tarfile.open(filename)
    except tarfile.TarError:
        raise ReadError(
            "%s is not a compressed or uncompressed tar file" % filename)
    try:
        tarobj.extractall(extract_dir)
    finally:
        tarobj.close()

_UNPACK_FORMATS = {
    'gztar': (['.tar.gz', '.tgz'], _unpack_tarfile, [], "gzip'ed tar-file"),
    'tar':   (['.tar'], _unpack_tarfile, [], "uncompressed tar file"),
    'zip':   (['.zip'], _unpack_zipfile, [], "ZIP file")
    } # type: Dict[str, Tuple[List[str], Any, Sequence[Tuple[str, Any]], str]]

if _BZ2_SUPPORTED:
    _UNPACK_FORMATS['bztar'] = (['.bz2'], _unpack_tarfile, [],
                                "bzip2'ed tar-file")

def _find_unpack_format(filename: str) -> str:
    for name, info in _UNPACK_FORMATS.items():
        for extension in info[0]:
            if filename.endswith(extension):
                return name
    return None

def unpack_archive(filename: str, extract_dir: str = None,
                   format: str = None) -> None:
    """Unpack an archive.

    `filename` is the name of the archive.

    `extract_dir` is the name of the target directory, where the archive
    is unpacked. If not provided, the current working directory is used.

    `format` is the archive format: one of "zip", "tar", or "gztar". Or any
    other registered format. If not provided, unpack_archive will use the
    filename extension and see if an unpacker was registered for that
    extension.

    In case none is found, a ValueError is raised.
    """
    if extract_dir is None:
        extract_dir = os.getcwd()

    if format is not None:
        try:
            format_info = _UNPACK_FORMATS[format]
        except KeyError:
            raise ValueError("Unknown unpack format '{0}'".format(format))

        func = format_info[1]
        func(filename, extract_dir, **dict(format_info[2]))
    else:
        # we need to look at the registered unpackers supported extensions
        format = _find_unpack_format(filename)
        if format is None:
            raise ReadError("Unknown archive format '{0}'".format(filename))

        func = _UNPACK_FORMATS[format][1]
        kwargs = dict(_UNPACK_FORMATS[format][2])
        func(filename, extract_dir, **kwargs)
