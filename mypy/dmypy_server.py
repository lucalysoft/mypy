"""Server for mypy daemon mode.

This implements a daemon process which keeps useful state in memory
to enable fine-grained incremental reprocessing of changes.
"""

import argparse
import base64
import io
import json
import os
import pickle
import subprocess
import sys
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout

from typing import AbstractSet, Any, Callable, Dict, List, Optional, Sequence, Tuple
from typing_extensions import Final

import mypy.build
import mypy.errors
import mypy.main
from mypy.find_sources import create_source_list, InvalidSourceList
from mypy.server.update import FineGrainedBuildManager
from mypy.dmypy_util import receive
from mypy.ipc import IPCServer
from mypy.fscache import FileSystemCache
from mypy.fswatcher import FileSystemWatcher, FileData
from mypy.modulefinder import BuildSource, compute_search_paths
from mypy.options import Options
from mypy.suggestions import SuggestionFailure, SuggestionEngine
from mypy.typestate import reset_global_state
from mypy.version import __version__
from mypy.util import FancyFormatter, count_stats

MEM_PROFILE = False  # type: Final  # If True, dump memory profile after initialization

if sys.platform == 'win32':
    from subprocess import STARTUPINFO

    def daemonize(options: Options,
                  status_file: str,
                  timeout: Optional[int] = None,
                  log_file: Optional[str] = None) -> int:
        """Create the daemon process via "dmypy daemon" and pass options via command line

        When creating the daemon grandchild, we create it in a new console, which is
        started hidden. We cannot use DETACHED_PROCESS since it will cause console windows
        to pop up when starting. See
        https://github.com/python/cpython/pull/4150#issuecomment-340215696
        for more on why we can't have nice things.

        It also pickles the options to be unpickled by mypy.
        """
        command = [sys.executable, '-m', 'mypy.dmypy', '--status-file', status_file, 'daemon']
        pickeled_options = pickle.dumps((options.snapshot(), timeout, log_file))
        command.append('--options-data="{}"'.format(base64.b64encode(pickeled_options).decode()))
        info = STARTUPINFO()
        info.dwFlags = 0x1  # STARTF_USESHOWWINDOW aka use wShowWindow's value
        info.wShowWindow = 0  # SW_HIDE aka make the window invisible
        try:
            subprocess.Popen(command,
                             creationflags=0x10,  # CREATE_NEW_CONSOLE
                             startupinfo=info)
            return 0
        except subprocess.CalledProcessError as e:
            return e.returncode

else:
    def _daemonize_cb(func: Callable[[], None], log_file: Optional[str] = None) -> int:
        """Arrange to call func() in a grandchild of the current process.

        Return 0 for success, exit status for failure, negative if
        subprocess killed by signal.
        """
        # See https://stackoverflow.com/questions/473620/how-do-you-create-a-daemon-in-python
        sys.stdout.flush()
        sys.stderr.flush()
        pid = os.fork()
        if pid:
            # Parent process: wait for child in case things go bad there.
            npid, sts = os.waitpid(pid, 0)
            sig = sts & 0xff
            if sig:
                print("Child killed by signal", sig)
                return -sig
            sts = sts >> 8
            if sts:
                print("Child exit status", sts)
            return sts
        # Child process: do a bunch of UNIX stuff and then fork a grandchild.
        try:
            os.setsid()  # Detach controlling terminal
            os.umask(0o27)
            devnull = os.open('/dev/null', os.O_RDWR)
            os.dup2(devnull, 0)
            os.dup2(devnull, 1)
            os.dup2(devnull, 2)
            os.close(devnull)
            pid = os.fork()
            if pid:
                # Child is done, exit to parent.
                os._exit(0)
            # Grandchild: run the server.
            if log_file:
                sys.stdout = sys.stderr = open(log_file, 'a', buffering=1)
                fd = sys.stdout.fileno()
                os.dup2(fd, 2)
                os.dup2(fd, 1)
            func()
        finally:
            # Make sure we never get back into the caller.
            os._exit(1)

    def daemonize(options: Options,
                  status_file: str,
                  timeout: Optional[int] = None,
                  log_file: Optional[str] = None) -> int:
        """Run the mypy daemon in a grandchild of the current process

        Return 0 for success, exit status for failure, negative if
        subprocess killed by signal.
        """
        return _daemonize_cb(Server(options, status_file, timeout).serve, log_file)

# Server code.

CONNECTION_NAME = 'dmypy'  # type: Final


def process_start_options(flags: List[str], allow_sources: bool) -> Options:
    sources, options = mypy.main.process_options(['-i'] + flags,
                                                 require_targets=False,
                                                 server_options=True)
    if sources and not allow_sources:
        sys.exit("dmypy: start/restart does not accept sources")
    if options.report_dirs:
        sys.exit("dmypy: start/restart cannot generate reports")
    if options.junit_xml:
        sys.exit("dmypy: start/restart does not support --junit-xml; "
                 "pass it to check/recheck instead")
    if not options.incremental:
        sys.exit("dmypy: start/restart should not disable incremental mode")
    # Our file change tracking can't yet handle changes to files that aren't
    # specified in the sources list.
    if options.follow_imports not in ('skip', 'error'):
        sys.exit("dmypy: follow-imports must be 'skip' or 'error'")
    return options


ModulePathPair = Tuple[str, str]
ModulePathPairs = List[ModulePathPair]
ChangesAndRemovals = Tuple[ModulePathPairs, ModulePathPairs]


class Server:

    # NOTE: the instance is constructed in the parent process but
    # serve() is called in the grandchild (by daemonize()).

    def __init__(self, options: Options,
                 status_file: str,
                 timeout: Optional[int] = None) -> None:
        """Initialize the server with the desired mypy flags."""
        self.options = options
        # Snapshot the options info before we muck with it, to detect changes
        self.options_snapshot = options.snapshot()
        self.timeout = timeout
        self.fine_grained_manager = None  # type: Optional[FineGrainedBuildManager]

        if os.path.isfile(status_file):
            os.unlink(status_file)

        self.fscache = FileSystemCache()

        options.raise_exceptions = True
        options.incremental = True
        options.fine_grained_incremental = True
        options.show_traceback = True
        if options.use_fine_grained_cache:
            # Using fine_grained_cache implies generating and caring
            # about the fine grained cache
            options.cache_fine_grained = True
        else:
            options.cache_dir = os.devnull
        # Fine-grained incremental doesn't support general partial types
        # (details in https://github.com/python/mypy/issues/4492)
        options.local_partial_types = True
        self.status_file = status_file

        # Since the object is created in the parent process we can check
        # the output terminal options here.
        self.formatter = FancyFormatter(sys.stdout, sys.stderr, options.show_error_codes)

    def _response_metadata(self) -> Dict[str, str]:
        py_version = '{}_{}'.format(self.options.python_version[0], self.options.python_version[1])
        return {
            'platform': self.options.platform,
            'python_version': py_version,
        }

    def serve(self) -> None:
        """Serve requests, synchronously (no thread or fork)."""
        command = None
        try:
            server = IPCServer(CONNECTION_NAME, self.timeout)
            with open(self.status_file, 'w') as f:
                json.dump({'pid': os.getpid(), 'connection_name': server.connection_name}, f)
                f.write('\n')  # I like my JSON with a trailing newline
            while True:
                with server:
                    data = receive(server)
                    resp = {}  # type: Dict[str, Any]
                    if 'command' not in data:
                        resp = {'error': "No command found in request"}
                    else:
                        command = data['command']
                        if not isinstance(command, str):
                            resp = {'error': "Command is not a string"}
                        else:
                            command = data.pop('command')
                            try:
                                resp = self.run_command(command, data)
                            except Exception:
                                # If we are crashing, report the crash to the client
                                tb = traceback.format_exception(*sys.exc_info())
                                resp = {'error': "Daemon crashed!\n" + "".join(tb)}
                                resp.update(self._response_metadata())
                                server.write(json.dumps(resp).encode('utf8'))
                                raise
                    try:
                        resp.update(self._response_metadata())
                        server.write(json.dumps(resp).encode('utf8'))
                    except OSError:
                        pass  # Maybe the client hung up
                    if command == 'stop':
                        reset_global_state()
                        sys.exit(0)
        finally:
            # If the final command is something other than a clean
            # stop, remove the status file. (We can't just
            # simplify the logic and always remove the file, since
            # that could cause us to remove a future server's
            # status file.)
            if command != 'stop':
                os.unlink(self.status_file)
            try:
                server.cleanup()  # try to remove the socket dir on Linux
            except OSError:
                pass
            exc_info = sys.exc_info()
            if exc_info[0] and exc_info[0] is not SystemExit:
                traceback.print_exception(*exc_info)

    def run_command(self, command: str, data: Dict[str, object]) -> Dict[str, object]:
        """Run a specific command from the registry."""
        key = 'cmd_' + command
        method = getattr(self.__class__, key, None)
        if method is None:
            return {'error': "Unrecognized command '%s'" % command}
        else:
            if command not in {'check', 'recheck', 'run'}:
                # Only the above commands use some error formatting.
                del data['is_tty']
                del data['terminal_width']
            return method(self, **data)

    # Command functions (run in the server via RPC).

    def cmd_status(self, fswatcher_dump_file: Optional[str] = None) -> Dict[str, object]:
        """Return daemon status."""
        res = {}  # type: Dict[str, object]
        res.update(get_meminfo())
        if fswatcher_dump_file:
            data = self.fswatcher.dump_file_data() if hasattr(self, 'fswatcher') else {}
            # Using .dumps and then writing was noticably faster than using dump
            s = json.dumps(data)
            with open(fswatcher_dump_file, 'w') as f:
                f.write(s)
        return res

    def cmd_stop(self) -> Dict[str, object]:
        """Stop daemon."""
        # We need to remove the status file *before* we complete the
        # RPC. Otherwise a race condition exists where a subsequent
        # command can see a status file from a dying server and think
        # it is a live one.
        os.unlink(self.status_file)
        return {}

    def cmd_run(self, version: str, args: Sequence[str],
                is_tty: bool, terminal_width: int) -> Dict[str, object]:
        """Check a list of files, triggering a restart if needed."""
        try:
            # Process options can exit on improper arguments, so we need to catch that and
            # capture stderr so the client can report it
            stderr = io.StringIO()
            stdout = io.StringIO()
            with redirect_stderr(stderr):
                with redirect_stdout(stdout):
                    sources, options = mypy.main.process_options(
                        ['-i'] + list(args),
                        require_targets=True,
                        server_options=True,
                        fscache=self.fscache,
                        program='mypy-daemon',
                        header=argparse.SUPPRESS)
            # Signal that we need to restart if the options have changed
            if self.options_snapshot != options.snapshot():
                return {'restart': 'configuration changed'}
            if __version__ != version:
                return {'restart': 'mypy version changed'}
            if self.fine_grained_manager:
                manager = self.fine_grained_manager.manager
                start_plugins_snapshot = manager.plugins_snapshot
                _, current_plugins_snapshot = mypy.build.load_plugins(options,
                                                                      manager.errors,
                                                                      sys.stdout)
                if current_plugins_snapshot != start_plugins_snapshot:
                    return {'restart': 'plugins changed'}
        except InvalidSourceList as err:
            return {'out': '', 'err': str(err), 'status': 2}
        except SystemExit as e:
            return {'out': stdout.getvalue(), 'err': stderr.getvalue(), 'status': e.code}
        return self.check(sources, is_tty, terminal_width)

    def cmd_check(self, files: Sequence[str],
                  is_tty: bool, terminal_width: int) -> Dict[str, object]:
        """Check a list of files."""
        try:
            sources = create_source_list(files, self.options, self.fscache)
        except InvalidSourceList as err:
            return {'out': '', 'err': str(err), 'status': 2}
        return self.check(sources, is_tty, terminal_width)

    def cmd_recheck(self,
                    is_tty: bool,
                    terminal_width: int,
                    remove: Optional[List[str]] = None,
                    update: Optional[List[str]] = None) -> Dict[str, object]:
        """Check the same list of files we checked most recently.

        If remove/update is given, they modify the previous list;
        if all are None, stat() is called for each file in the previous list.
        """
        t0 = time.time()
        if not self.fine_grained_manager:
            return {'error': "Command 'recheck' is only valid after a 'check' command"}
        sources = self.previous_sources
        if remove:
            removals = set(remove)
            sources = [s for s in sources if s.path and s.path not in removals]
        if update:
            known = {s.path for s in sources if s.path}
            added = [p for p in update if p not in known]
            try:
                added_sources = create_source_list(added, self.options, self.fscache)
            except InvalidSourceList as err:
                return {'out': '', 'err': str(err), 'status': 2}
            sources = sources + added_sources  # Make a copy!
        t1 = time.time()
        manager = self.fine_grained_manager.manager
        manager.log("fine-grained increment: cmd_recheck: {:.3f}s".format(t1 - t0))
        res = self.fine_grained_increment(sources, is_tty, terminal_width,
                                          remove, update)
        self.fscache.flush()
        self.update_stats(res)
        return res

    def check(self, sources: List[BuildSource],
              is_tty: bool, terminal_width: int) -> Dict[str, Any]:
        """Check using fine-grained incremental mode.

        If is_tty is True format the output nicely with colors and summary line
        (unless disabled in self.options). Also pass the terminal_width to formatter.
        """
        if not self.fine_grained_manager:
            res = self.initialize_fine_grained(sources, is_tty, terminal_width)
        else:
            res = self.fine_grained_increment(sources, is_tty, terminal_width)
        self.fscache.flush()
        self.update_stats(res)
        return res

    def update_stats(self, res: Dict[str, Any]) -> None:
        if self.fine_grained_manager:
            manager = self.fine_grained_manager.manager
            manager.dump_stats()
            res['stats'] = manager.stats
            manager.stats = {}

    def initialize_fine_grained(self, sources: List[BuildSource],
                                is_tty: bool, terminal_width: int) -> Dict[str, Any]:
        self.fswatcher = FileSystemWatcher(self.fscache)
        t0 = time.time()
        self.update_sources(sources)
        t1 = time.time()
        try:
            result = mypy.build.build(sources=sources,
                                      options=self.options,
                                      fscache=self.fscache)
        except mypy.errors.CompileError as e:
            output = ''.join(s + '\n' for s in e.messages)
            if e.use_stdout:
                out, err = output, ''
            else:
                out, err = '', output
            return {'out': out, 'err': err, 'status': 2}
        messages = result.errors
        self.fine_grained_manager = FineGrainedBuildManager(result)
        self.previous_sources = sources

        # If we are using the fine-grained cache, build hasn't actually done
        # the typechecking on the updated files yet.
        # Run a fine-grained update starting from the cached data
        if result.used_cache:
            t2 = time.time()
            # Pull times and hashes out of the saved_cache and stick them into
            # the fswatcher, so we pick up the changes.
            for state in self.fine_grained_manager.graph.values():
                meta = state.meta
                if meta is None: continue
                assert state.path is not None
                self.fswatcher.set_file_data(
                    state.path,
                    FileData(st_mtime=float(meta.mtime), st_size=meta.size, md5=meta.hash))

            changed, removed = self.find_changed(sources)

            # Find anything that has had its dependency list change
            for state in self.fine_grained_manager.graph.values():
                if not state.is_fresh():
                    assert state.path is not None
                    changed.append((state.id, state.path))

            t3 = time.time()
            # Run an update
            messages = self.fine_grained_manager.update(changed, removed)
            t4 = time.time()
            self.fine_grained_manager.manager.add_stats(
                update_sources_time=t1 - t0,
                build_time=t2 - t1,
                find_changes_time=t3 - t2,
                fg_update_time=t4 - t3,
                files_changed=len(removed) + len(changed))
        else:
            # Stores the initial state of sources as a side effect.
            self.fswatcher.find_changed()

        if MEM_PROFILE:
            from mypy.memprofile import print_memory_profile
            print_memory_profile(run_gc=False)

        status = 1 if messages else 0
        messages = self.pretty_messages(messages, len(sources), is_tty, terminal_width)
        return {'out': ''.join(s + '\n' for s in messages), 'err': '', 'status': status}

    def fine_grained_increment(self,
                               sources: List[BuildSource],
                               is_tty: bool,
                               terminal_width: int,
                               remove: Optional[List[str]] = None,
                               update: Optional[List[str]] = None,
                               ) -> Dict[str, Any]:
        assert self.fine_grained_manager is not None
        manager = self.fine_grained_manager.manager

        t0 = time.time()
        if remove is None and update is None:
            # Use the fswatcher to determine which files were changed
            # (updated or added) or removed.
            self.update_sources(sources)
            changed, removed = self.find_changed(sources)
        else:
            # Use the remove/update lists to update fswatcher.
            # This avoids calling stat() for unchanged files.
            changed, removed = self.update_changed(sources, remove or [], update or [])
        manager.search_paths = compute_search_paths(sources, manager.options, manager.data_dir)
        t1 = time.time()
        manager.log("fine-grained increment: find_changed: {:.3f}s".format(t1 - t0))
        messages = self.fine_grained_manager.update(changed, removed)
        t2 = time.time()
        manager.log("fine-grained increment: update: {:.3f}s".format(t2 - t1))
        manager.add_stats(
            find_changes_time=t1 - t0,
            fg_update_time=t2 - t1,
            files_changed=len(removed) + len(changed))

        status = 1 if messages else 0
        self.previous_sources = sources
        messages = self.pretty_messages(messages, len(sources), is_tty, terminal_width)
        return {'out': ''.join(s + '\n' for s in messages), 'err': '', 'status': status}

    def pretty_messages(self, messages: List[str], n_sources: int,
                        is_tty: bool = False, terminal_width: Optional[int] = None) -> List[str]:
        use_color = self.options.color_output and is_tty
        fit_width = self.options.pretty and is_tty
        if fit_width:
            messages = self.formatter.fit_in_terminal(messages,
                                                      fixed_terminal_width=terminal_width)
        if self.options.error_summary:
            summary = None  # type: Optional[str]
            if messages:
                n_errors, n_files = count_stats(messages)
                if n_errors:
                    summary = self.formatter.format_error(n_errors, n_files, n_sources,
                                                          use_color)
            else:
                summary = self.formatter.format_success(n_sources, use_color)
            if summary:
                # Create new list to avoid appending multiple summaries on successive runs.
                messages = messages + [summary]
        if use_color:
            messages = [self.formatter.colorize(m) for m in messages]
        return messages

    def update_sources(self, sources: List[BuildSource]) -> None:
        paths = [source.path for source in sources if source.path is not None]
        self.fswatcher.add_watched_paths(paths)

    def update_changed(self,
                       sources: List[BuildSource],
                       remove: List[str],
                       update: List[str],
                       ) -> ChangesAndRemovals:

        changed_paths = self.fswatcher.update_changed(remove, update)
        return self._find_changed(sources, changed_paths)

    def find_changed(self, sources: List[BuildSource]) -> ChangesAndRemovals:
        changed_paths = self.fswatcher.find_changed()
        return self._find_changed(sources, changed_paths)

    def _find_changed(self, sources: List[BuildSource],
                      changed_paths: AbstractSet[str]) -> ChangesAndRemovals:
        # Find anything that has been added or modified
        changed = [(source.module, source.path)
                   for source in sources
                   if source.path and source.path in changed_paths]

        # Now find anything that has been removed from the build
        modules = {source.module for source in sources}
        omitted = [source for source in self.previous_sources if source.module not in modules]
        removed = []
        for source in omitted:
            path = source.path
            assert path
            removed.append((source.module, path))

        # Find anything that has had its module path change because of added or removed __init__s
        last = {s.path: s.module for s in self.previous_sources}
        for s in sources:
            assert s.path
            if s.path in last and last[s.path] != s.module:
                # Mark it as removed from its old name and changed at its new name
                removed.append((last[s.path], s.path))
                changed.append((s.module, s.path))

        return changed, removed

    def cmd_suggest(self,
                    function: str,
                    callsites: bool,
                    **kwargs: Any) -> Dict[str, object]:
        """Suggest a signature for a function."""
        if not self.fine_grained_manager:
            return {'error': "Command 'suggest' is only valid after a 'check' command"}
        engine = SuggestionEngine(self.fine_grained_manager, **kwargs)
        try:
            if callsites:
                out = engine.suggest_callsites(function)
            else:
                out = engine.suggest(function)
        except SuggestionFailure as err:
            return {'error': str(err)}
        else:
            if not out:
                out = "No suggestions\n"
            elif not out.endswith("\n"):
                out += "\n"
            return {'out': out, 'err': "", 'status': 0}
        finally:
            self.fscache.flush()

    def cmd_hang(self) -> Dict[str, object]:
        """Hang for 100 seconds, as a debug hack."""
        time.sleep(100)
        return {}


# Misc utilities.


MiB = 2**20  # type: Final


def get_meminfo() -> Dict[str, Any]:
    res = {}  # type: Dict[str, Any]
    try:
        import psutil  # type: ignore  # It's not in typeshed yet
    except ImportError:
        res['memory_psutil_missing'] = (
            'psutil not found, run pip install mypy[dmypy] '
            'to install the needed components for dmypy'
        )
    else:
        process = psutil.Process()
        meminfo = process.memory_info()
        res['memory_rss_mib'] = meminfo.rss / MiB
        res['memory_vms_mib'] = meminfo.vms / MiB
        if sys.platform == 'win32':
            res['memory_maxrss_mib'] = meminfo.peak_wset / MiB
        else:
            # See https://stackoverflow.com/questions/938733/total-memory-used-by-python-process
            import resource  # Since it doesn't exist on Windows.
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            if sys.platform == 'darwin':
                factor = 1
            else:
                factor = 1024  # Linux
            res['memory_maxrss_mib'] = rusage.ru_maxrss * factor / MiB
    return res
