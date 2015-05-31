"""Type checker test cases"""

import os.path

import typing

from mypy import build
from mypy.myunit import Suite, run_test
from mypy.test.config import test_temp_dir, test_data_prefix
from mypy.test.data import parse_test_cases
from mypy.test.helpers import assert_string_arrays_equal, testcase_pyversion, update_testcase_output
from mypy.test.testsemanal import normalize_error_messages
from mypy.errors import CompileError

import sys
APPEND_TESTCASES = '.new' if '-u' in sys.argv else ''
UPDATE_TESTCASES = '-i' in sys.argv or '-u' in sys.argv

# List of files that contain test case descriptions.
files = [
    'check-basic.test',
    'check-classes.test',
    'check-expressions.test',
    'check-statements.test',
    'check-generics.test',
    'check-tuples.test',
    'check-dynamic-typing.test',
    'check-functions.test',
    'check-inference.test',
    'check-inference-context.test',
    'check-varargs.test',
    'check-kwargs.test',
    'check-overloading.test',
    'check-type-checks.test',
    'check-abstract.test',
    'check-multiple-inheritance.test',
    'check-super.test',
    'check-modules.test',
    'check-generic-subtyping.test',
    'check-typevar-values.test',
    'check-python2.test',
    'check-unsupported.test',
    'check-unreachable-code.test',
    'check-unions.test',
    'check-isinstance.test',
    'check-lists.test',
    'check-namedtuple.test',
    'check-type-aliases.test',
    'check-ignore.test',
    'check-type-promotion.test',
]


class TypeCheckSuite(Suite):
    def cases(self):
        c = []
        for f in files:
            c += parse_test_cases(os.path.join(test_data_prefix, f),
                                  self.run_test, test_temp_dir, True)
        return c

    def run_test(self, testcase):
        a = []
        pyversion = testcase_pyversion(testcase.file, testcase.name)
        try:
            src = '\n'.join(testcase.input)
            build.build('main',
                        target=build.TYPE_CHECK,
                        program_text=src,
                        pyversion=pyversion,
                        flags=[build.TEST_BUILTINS],
                        alt_lib_path=test_temp_dir)
        except CompileError as e:
            a = normalize_error_messages(e.messages)

        if testcase.output != a and UPDATE_TESTCASES:
            update_testcase_output(testcase, a, APPEND_TESTCASES)

        assert_string_arrays_equal(
            testcase.output, a,
            'Invalid type checker output ({}, line {})'.format(
                testcase.file, testcase.line))


if __name__ == '__main__':
    import sys
    run_test(TypeCheckSuite(), sys.argv[1:])
