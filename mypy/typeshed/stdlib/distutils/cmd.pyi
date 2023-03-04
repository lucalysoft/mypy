from _typeshed import Incomplete
from abc import abstractmethod
from collections.abc import Callable, Iterable
from distutils.dist import Distribution
from typing import Any

class Command:
    sub_commands: list[tuple[str, Callable[[Command], bool] | None]]
    def __init__(self, dist: Distribution) -> None: ...
    @abstractmethod
    def initialize_options(self) -> None: ...
    @abstractmethod
    def finalize_options(self) -> None: ...
    @abstractmethod
    def run(self) -> None: ...
    def announce(self, msg: str, level: int = 1) -> None: ...
    def debug_print(self, msg: str) -> None: ...
    def ensure_string(self, option: str, default: str | None = None) -> None: ...
    def ensure_string_list(self, option: str | list[str]) -> None: ...
    def ensure_filename(self, option: str) -> None: ...
    def ensure_dirname(self, option: str) -> None: ...
    def get_command_name(self) -> str: ...
    def set_undefined_options(self, src_cmd: str, *option_pairs: tuple[str, str]) -> None: ...
    def get_finalized_command(self, command: str, create: int = 1) -> Command: ...
    def reinitialize_command(self, command: Command | str, reinit_subcommands: int = 0) -> Command: ...
    def run_command(self, command: str) -> None: ...
    def get_sub_commands(self) -> list[str]: ...
    def warn(self, msg: str) -> None: ...
    def execute(self, func: Callable[..., object], args: Iterable[Any], msg: str | None = None, level: int = 1) -> None: ...
    def mkpath(self, name: str, mode: int = 0o777) -> None: ...
    def copy_file(
        self, infile: str, outfile: str, preserve_mode: int = 1, preserve_times: int = 1, link: str | None = None, level: Any = 1
    ) -> tuple[str, bool]: ...  # level is not used
    def copy_tree(
        self,
        infile: str,
        outfile: str,
        preserve_mode: int = 1,
        preserve_times: int = 1,
        preserve_symlinks: int = 0,
        level: Any = 1,
    ) -> list[str]: ...  # level is not used
    def move_file(self, src: str, dst: str, level: Any = 1) -> str: ...  # level is not used
    def spawn(self, cmd: Iterable[str], search_path: int = 1, level: Any = 1) -> None: ...  # level is not used
    def make_archive(
        self,
        base_name: str,
        format: str,
        root_dir: str | None = None,
        base_dir: str | None = None,
        owner: str | None = None,
        group: str | None = None,
    ) -> str: ...
    def make_file(
        self,
        infiles: str | list[str] | tuple[str, ...],
        outfile: str,
        func: Callable[..., object],
        args: list[Any],
        exec_msg: str | None = None,
        skip_msg: str | None = None,
        level: Any = 1,
    ) -> None: ...  # level is not used
    def ensure_finalized(self) -> None: ...
    def dump_options(self, header: Incomplete | None = None, indent: str = "") -> None: ...
