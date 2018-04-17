"""Test runner for reference count opcode insertion transform test cases.

The transform inserts needed reference count increment/decrement
operations to IR.
"""

import os.path
from typing import List

from mypy.test.config import test_temp_dir
from mypy.test.data import parse_test_cases, DataDrivenTestCase
from mypy.errors import CompileError
from mypy.test.helpers import assert_string_arrays_equal

from mypyc.ops import format_func
from mypyc.refcount import insert_ref_count_opcodes
from mypyc.test.testutil import (
    ICODE_GEN_BUILTINS,
    build_ir_for_single_file,
    use_custom_builtins,
    MypycDataSuite,
)

files = [
    'refcount.test'
]


class TestRefCountTransform(MypycDataSuite):
    files = files
    base_path = test_temp_dir
    optional_out = True

    def run_case(self, testcase: DataDrivenTestCase) -> None:
        """Perform a reference count opcode insertion transform test case."""

        with use_custom_builtins(os.path.join(self.data_prefix, ICODE_GEN_BUILTINS), testcase):
            try:
                ir = build_ir_for_single_file(testcase.input)
            except CompileError as e:
                actual = e.messages
            else:
                assert len(ir) == 1, "Only 1 function definition expected per test case"
                fn = ir[0]
                insert_ref_count_opcodes(fn)
                actual = format_func(fn)
                actual = actual[actual.index('L0:'):]

            expected_output = testcase.output
            assert_string_arrays_equal(
                expected_output, actual,
                'Invalid source code output ({}, line {})'.format(testcase.file,
                                                                  testcase.line))
