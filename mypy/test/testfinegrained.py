"""Test cases for fine-grained incremental checking.

Each test cases runs a batch build followed by one or more fine-grained
incremental steps. We verify that each step produces the expected output.

See the comment at the top of test-data/unit/fine-grained.test for more
information.

N.B.: Unlike most of the other test suites, testfinegrained does not
rely on an alt_lib_path for finding source files. This means that they
can test interactions with the lib_path that is built implicitly based
on specified sources.
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from typing import Any, cast

import pytest

from mypy import build
from mypy.config_parser import parse_config_file
from mypy.dmypy_server import Server
from mypy.dmypy_util import DEFAULT_STATUS_FILE
from mypy.errors import CompileError
from mypy.find_sources import create_source_list
from mypy.modulefinder import BuildSource
from mypy.options import Options
from mypy.server.mergecheck import check_consistency
from mypy.server.update import sort_messages_preserving_file_order
from mypy.test.config import test_temp_dir
from mypy.test.data import DataDrivenTestCase, DataSuite, DeleteFile, UpdateFile
from mypy.test.helpers import (
    assert_module_equivalence,
    assert_string_arrays_equal,
    assert_target_equivalence,
    find_test_files,
    parse_options,
    perform_file_operations,
)

# Set to True to perform (somewhat expensive) checks for duplicate AST nodes after merge
CHECK_CONSISTENCY = False


class FineGrainedSuite(DataSuite):
    files = find_test_files(
        pattern="fine-grained*.test", exclude=["fine-grained-cache-incremental.test"]
    )

    # Whether to use the fine-grained cache in the testing. This is overridden
    # by a trivial subclass to produce a suite that uses the cache.
    use_cache = False

    def should_skip(self, testcase: DataDrivenTestCase) -> bool:
        # Decide whether to skip the test. This could have been structured
        # as a filter() classmethod also, but we want the tests reported
        # as skipped, not just elided.
        if self.use_cache:
            if testcase.only_when == "-only_when_nocache":
                return True
            # TODO: In caching mode we currently don't well support
            # starting from cached states with errors in them.
            if testcase.output and testcase.output[0] != "==":
                return True
        else:
            if testcase.only_when == "-only_when_cache":
                return True

        if "Inspect" in testcase.name and sys.version_info < (3, 8):
            return True
        return False

    def run_case(self, testcase: DataDrivenTestCase) -> None:
        if self.should_skip(testcase):
            pytest.skip()
            return

        main_src = "\n".join(testcase.input)
        main_path = os.path.join(test_temp_dir, "main")
        with open(main_path, "w", encoding="utf8") as f:
            f.write(main_src)

        options = self.get_options(main_src, testcase, build_cache=False)
        build_options = self.get_options(main_src, testcase, build_cache=True)
        server = Server(options, DEFAULT_STATUS_FILE)

        num_regular_incremental_steps = self.get_build_steps(main_src)
        step = 1
        sources = self.parse_sources(main_src, step, options)
        if step <= num_regular_incremental_steps:
            messages = self.build(build_options, sources)
        else:
            messages = self.run_check(server, sources)

        a = []
        if messages:
            a.extend(normalize_messages(messages))

        assert testcase.tmpdir
        a.extend(self.maybe_suggest(step, server, main_src, testcase.tmpdir.name))
        a.extend(self.maybe_inspect(step, server, main_src))

        if server.fine_grained_manager:
            if CHECK_CONSISTENCY:
                check_consistency(server.fine_grained_manager)

        steps = testcase.find_steps()
        all_triggered = []

        for operations in steps:
            step += 1
            output, triggered = self.perform_step(
                operations,
                server,
                options,
                build_options,
                testcase,
                main_src,
                step,
                num_regular_incremental_steps,
            )
            a.append("==")
            a.extend(output)
            all_triggered.extend(triggered)

        # Normalize paths in test output (for Windows).
        a = [line.replace("\\", "/") for line in a]

        assert_string_arrays_equal(
            testcase.output, a, f"Invalid output ({testcase.file}, line {testcase.line})"
        )

        if testcase.triggered:
            assert_string_arrays_equal(
                testcase.triggered,
                self.format_triggered(all_triggered),
                f"Invalid active triggers ({testcase.file}, line {testcase.line})",
            )

    def get_options(self, source: str, testcase: DataDrivenTestCase, build_cache: bool) -> Options:
        # This handles things like '# flags: --foo'.
        options = parse_options(source, testcase, incremental_step=1)
        options.incremental = True
        options.use_builtins_fixtures = True
        options.show_traceback = True
        options.error_summary = False
        options.fine_grained_incremental = not build_cache
        options.use_fine_grained_cache = self.use_cache and not build_cache
        options.cache_fine_grained = self.use_cache
        options.local_partial_types = True
        options.enable_incomplete_features = True
        # Treat empty bodies safely for these test cases.
        options.allow_empty_bodies = not testcase.name.endswith("_no_empty")
        if re.search("flags:.*--follow-imports", source) is None:
            # Override the default for follow_imports
            options.follow_imports = "error"

        for name, _ in testcase.files:
            if "mypy.ini" in name or "pyproject.toml" in name:
                parse_config_file(options, lambda: None, name)
                break

        return options

    def run_check(self, server: Server, sources: list[BuildSource]) -> list[str]:
        response = server.check(sources, export_types=True, is_tty=False, terminal_width=-1)
        out = cast(str, response["out"] or response["err"])
        return out.splitlines()

    def build(self, options: Options, sources: list[BuildSource]) -> list[str]:
        try:
            result = build.build(sources=sources, options=options)
        except CompileError as e:
            return e.messages
        return result.errors

    def format_triggered(self, triggered: list[list[str]]) -> list[str]:
        result = []
        for n, triggers in enumerate(triggered):
            filtered = [trigger for trigger in triggers if not trigger.endswith("__>")]
            filtered = sorted(filtered)
            result.append(("%d: %s" % (n + 2, ", ".join(filtered))).strip())
        return result

    def get_build_steps(self, program_text: str) -> int:
        """Get the number of regular incremental steps to run, from the test source"""
        if not self.use_cache:
            return 0
        m = re.search("# num_build_steps: ([0-9]+)$", program_text, flags=re.MULTILINE)
        if m is not None:
            return int(m.group(1))
        return 1

    def perform_step(
        self,
        operations: list[UpdateFile | DeleteFile],
        server: Server,
        options: Options,
        build_options: Options,
        testcase: DataDrivenTestCase,
        main_src: str,
        step: int,
        num_regular_incremental_steps: int,
    ) -> tuple[list[str], list[list[str]]]:
        """Perform one fine-grained incremental build step (after some file updates/deletions).

        Return (mypy output, triggered targets).
        """
        perform_file_operations(operations)
        sources = self.parse_sources(main_src, step, options)

        if step <= num_regular_incremental_steps:
            new_messages = self.build(build_options, sources)
        else:
            new_messages = self.run_check(server, sources)

        updated: list[str] = []
        changed: list[str] = []
        targets: list[str] = []
        triggered = []
        if server.fine_grained_manager:
            if CHECK_CONSISTENCY:
                check_consistency(server.fine_grained_manager)
            triggered.append(server.fine_grained_manager.triggered)

            updated = server.fine_grained_manager.updated_modules
            changed = [mod for mod, file in server.fine_grained_manager.changed_modules]
            targets = server.fine_grained_manager.processed_targets

        expected_stale = testcase.expected_stale_modules.get(step - 1)
        if expected_stale is not None:
            assert_module_equivalence("stale" + str(step - 1), expected_stale, changed)

        expected_rechecked = testcase.expected_rechecked_modules.get(step - 1)
        if expected_rechecked is not None:
            assert_module_equivalence("rechecked" + str(step - 1), expected_rechecked, updated)

        expected = testcase.expected_fine_grained_targets.get(step)
        if expected:
            assert_target_equivalence("targets" + str(step), expected, targets)

        new_messages = normalize_messages(new_messages)

        a = new_messages
        assert testcase.tmpdir
        a.extend(self.maybe_suggest(step, server, main_src, testcase.tmpdir.name))
        a.extend(self.maybe_inspect(step, server, main_src))

        return a, triggered

    def parse_sources(
        self, program_text: str, incremental_step: int, options: Options
    ) -> list[BuildSource]:
        """Return target BuildSources for a test case.

        Normally, the unit tests will check all files included in the test
        case. This differs from how testcheck works by default, as dmypy
        doesn't currently support following imports.

        You can override this behavior and instruct the tests to check
        multiple modules by using a comment like this in the test case
        input:

          # cmd: main a.py

        You can also use `# cmdN:` to have a different cmd for incremental
        step N (2, 3, ...).

        """
        m = re.search("# cmd: mypy ([a-zA-Z0-9_./ ]+)$", program_text, flags=re.MULTILINE)
        regex = f"# cmd{incremental_step}: mypy ([a-zA-Z0-9_./ ]+)$"
        alt_m = re.search(regex, program_text, flags=re.MULTILINE)
        if alt_m is not None:
            # Optionally return a different command if in a later step
            # of incremental mode, otherwise default to reusing the
            # original cmd.
            m = alt_m

        if m:
            # The test case wants to use a non-default set of files.
            paths = [os.path.join(test_temp_dir, path) for path in m.group(1).strip().split()]
            return create_source_list(paths, options)
        else:
            base = BuildSource(os.path.join(test_temp_dir, "main"), "__main__", None)
            # Use expand_dir instead of create_source_list to avoid complaints
            # when there aren't any .py files in an increment
            return [base] + create_source_list([test_temp_dir], options, allow_empty_dir=True)

    def maybe_suggest(self, step: int, server: Server, src: str, tmp_dir: str) -> list[str]:
        output: list[str] = []
        targets = self.get_suggest(src, step)
        for flags, target in targets:
            json = "--json" in flags
            callsites = "--callsites" in flags
            no_any = "--no-any" in flags
            no_errors = "--no-errors" in flags
            m = re.match("--flex-any=([0-9.]+)", flags)
            flex_any = float(m.group(1)) if m else None
            m = re.match(r"--use-fixme=(\w+)", flags)
            use_fixme = m.group(1) if m else None
            m = re.match("--max-guesses=([0-9]+)", flags)
            max_guesses = int(m.group(1)) if m else None
            res: dict[str, Any] = server.cmd_suggest(
                target.strip(),
                json=json,
                no_any=no_any,
                no_errors=no_errors,
                flex_any=flex_any,
                use_fixme=use_fixme,
                callsites=callsites,
                max_guesses=max_guesses,
            )
            val = res["error"] if "error" in res else res["out"] + res["err"]
            if json:
                # JSON contains already escaped \ on Windows, so requires a bit of care.
                val = val.replace("\\\\", "\\")
                val = val.replace(os.path.realpath(tmp_dir) + os.path.sep, "")
            output.extend(val.strip().split("\n"))
        return normalize_messages(output)

    def maybe_inspect(self, step: int, server: Server, src: str) -> list[str]:
        output: list[str] = []
        targets = self.get_inspect(src, step)
        for flags, location in targets:
            m = re.match(r"--show=(\w+)", flags)
            show = m.group(1) if m else "type"
            verbosity = 0
            if "-v" in flags:
                verbosity = 1
            if "-vv" in flags:
                verbosity = 2
            m = re.match(r"--limit=([0-9]+)", flags)
            limit = int(m.group(1)) if m else 0
            include_span = "--include-span" in flags
            include_kind = "--include-kind" in flags
            include_object_attrs = "--include-object-attrs" in flags
            union_attrs = "--union-attrs" in flags
            force_reload = "--force-reload" in flags
            res: dict[str, Any] = server.cmd_inspect(
                show,
                location,
                verbosity=verbosity,
                limit=limit,
                include_span=include_span,
                include_kind=include_kind,
                include_object_attrs=include_object_attrs,
                union_attrs=union_attrs,
                force_reload=force_reload,
            )
            val = res["error"] if "error" in res else res["out"] + res["err"]
            output.extend(val.strip().split("\n"))
        return normalize_messages(output)

    def get_suggest(self, program_text: str, incremental_step: int) -> list[tuple[str, str]]:
        step_bit = "1?" if incremental_step == 1 else str(incremental_step)
        regex = f"# suggest{step_bit}: (--[a-zA-Z0-9_\\-./=?^ ]+ )*([a-zA-Z0-9_.:/?^ ]+)$"
        m = re.findall(regex, program_text, flags=re.MULTILINE)
        return m

    def get_inspect(self, program_text: str, incremental_step: int) -> list[tuple[str, str]]:
        step_bit = "1?" if incremental_step == 1 else str(incremental_step)
        regex = f"# inspect{step_bit}: (--[a-zA-Z0-9_\\-=?^ ]+ )*([a-zA-Z0-9_.:/?^ ]+)$"
        m = re.findall(regex, program_text, flags=re.MULTILINE)
        return m


def normalize_messages(messages: list[str]) -> list[str]:
    return [re.sub("^tmp" + re.escape(os.sep), "", message) for message in messages]


class TestMessageSorting(unittest.TestCase):
    def test_simple_sorting(self) -> None:
        msgs = ['x.py:1: error: "int" not callable', 'foo/y.py:123: note: "X" not defined']
        old_msgs = ['foo/y.py:12: note: "Y" not defined', 'x.py:8: error: "str" not callable']
        assert sort_messages_preserving_file_order(msgs, old_msgs) == list(reversed(msgs))
        assert sort_messages_preserving_file_order(list(reversed(msgs)), old_msgs) == list(
            reversed(msgs)
        )

    def test_long_form_sorting(self) -> None:
        # Multi-line errors should be sorted together and not split.
        msg1 = [
            'x.py:1: error: "int" not callable',
            "and message continues (x: y)",
            "    1()",
            "    ^~~",
        ]
        msg2 = [
            'foo/y.py: In function "f":',
            'foo/y.py:123: note: "X" not defined',
            "and again message continues",
        ]
        old_msgs = ['foo/y.py:12: note: "Y" not defined', 'x.py:8: error: "str" not callable']
        assert sort_messages_preserving_file_order(msg1 + msg2, old_msgs) == msg2 + msg1
        assert sort_messages_preserving_file_order(msg2 + msg1, old_msgs) == msg2 + msg1

    def test_mypy_error_prefix(self) -> None:
        # Some errors don't have a file and start with "mypy: ". These
        # shouldn't be sorted together with file-specific errors.
        msg1 = 'x.py:1: error: "int" not callable'
        msg2 = 'foo/y:123: note: "X" not defined'
        msg3 = "mypy: Error not associated with a file"
        old_msgs = [
            "mypy: Something wrong",
            'foo/y:12: note: "Y" not defined',
            'x.py:8: error: "str" not callable',
        ]
        assert sort_messages_preserving_file_order([msg1, msg2, msg3], old_msgs) == [
            msg2,
            msg1,
            msg3,
        ]
        assert sort_messages_preserving_file_order([msg3, msg2, msg1], old_msgs) == [
            msg2,
            msg1,
            msg3,
        ]

    def test_new_file_at_the_end(self) -> None:
        msg1 = 'x.py:1: error: "int" not callable'
        msg2 = 'foo/y.py:123: note: "X" not defined'
        new1 = "ab.py:3: error: Problem: error"
        new2 = "aaa:3: error: Bad"
        old_msgs = ['foo/y.py:12: note: "Y" not defined', 'x.py:8: error: "str" not callable']
        assert sort_messages_preserving_file_order([msg1, msg2, new1], old_msgs) == [
            msg2,
            msg1,
            new1,
        ]
        assert sort_messages_preserving_file_order([new1, msg1, msg2, new2], old_msgs) == [
            msg2,
            msg1,
            new1,
            new2,
        ]
