"""Tests for parse tree pretty printing that preserves formatting

Test case descriptions are in file test/data/output.test."""

import os.path
import re

from mypy import build
from mypy.myunit import Suite, run_test
from mypy.testhelpers import assert_string_arrays_equal
from mypy.testdata import parse_test_cases
from mypy.testconfig import test_data_prefix, test_temp_dir
from mypy.parse import parse
from mypy.output import OutputVisitor
from mypy.errors import CompileError
from typing import Undefined, Any


# Files which contain test case descriptions.
output_files = ['output.test']


class OutputSuite(Suite):
    def cases(self):
        c = []
        for f in output_files:
            c += parse_test_cases(os.path.join(test_data_prefix, f),
                                  test_output, test_temp_dir, True)
        return c


def test_output(testcase):
    """Perform an identity source code transformation test case."""
    expected = testcase.output
    if expected == []:
        expected = testcase.input
    try:
        src = '\n'.join(testcase.input)
        # Parse and analyze the source program.
        # Parse and semantically analyze the source program.
        trees, symtable, infos, types = Undefined, Undefined, Undefined, Undefined # type: (Any, Any, Any, Any)
        
        # Test case names with a special suffix get semantically analyzed. This
        # lets us test that semantic analysis does not break source code pretty
        # printing.
        if testcase.name.endswith('_SemanticAnalyzer'):
            result = build.build('main',
                                 target=build.SEMANTIC_ANALYSIS,
                                 program_text=src,
                                 flags=[build.TEST_BUILTINS],
                                 alt_lib_path=test_temp_dir)
            files = result.files
        else:
            files = {'main': parse(src, 'main')}
        a = []
        first = True
        # Produce an output containing the pretty-printed forms (with original
        # formatting) of all the relevant source files.
        for fnam in sorted(files.keys()):
            f = files[fnam]
            # Omit the builtins and files marked for omission.
            if (not f.path.endswith(os.sep + 'builtins.py') and
                    '-skip.' not in f.path):
                # Add file name + colon for files other than the first.
                if not first:
                    a.append('{}:'.format(fix_path(remove_prefix(
                        f.path, test_temp_dir))))
                
                v = OutputVisitor()
                f.accept(v)
                s = v.output()
                if s != '':
                    a += s.split('\n')
            first = False
    except CompileError as e:
        a = e.messages
    assert_string_arrays_equal(
        expected, a, 'Invalid source code output ({}, line {})'.format(
            testcase.file, testcase.line))


def remove_prefix(path, prefix):
    regexp = '^' + prefix.replace('\\', '\\\\')
    np = re.sub(regexp, '', path)
    if np.startswith(os.sep):
        np = np[1:]
    return np


def fix_path(path):
    return path.replace('\\', '/')


if __name__ == '__main__':
    import sys
    run_test(OutputSuite(), sys.argv[1:])
