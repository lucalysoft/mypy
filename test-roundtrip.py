import os.path
import re
from unittest import Suite
from test.helpers import parse_test_cases, assert_string_arrays_equal
from build import build
from parser import parse
from os import separator
from output import OutputVisitor
from errors import CompileError


# Files which contain test case descriptions.
roundtrip_files = ['roundtrip.test']


class RoundtripSuite(Suite):
    def cases(self):
        c = []
        for f in roundtrip_files:
            c += parse_test_cases(os.path.join(test_data_prefix, f), test_roundtrip, test_temp_dir, True)
        return c


# Perform an identity source code transformation test case.
def test_roundtrip(testcase):
    any a
    expected = testcase.output
    if expected == []:
        expected = testcase.input
    try:
        src = '\n'.join(testcase.input)
        # Parse and analyze the source program.
        # Parse and semantically analyze the source program.
        any trees, any symtable, any infos, any types
        
        # Test case names with a special suffix get semantically analyzed. This
        # lets us test that semantic analysis does not break source code pretty
        # printing.
        if testcase.name.endswith('_SemanticAnalysis'):
            trees, symtable, infos, types = build(src, 'main', True, test_temp_dir)
        else:
            trees = [parse(src, 'main')]
        a = []
        first = True
        # Produce an output containing the pretty-printed forms (with original
        # formatting) of all the relevant source files.
        for t in trees:
            # Omit the builtins and files marked for omission.
            if not t.path.endswith(separator + 'builtins.py') and '-skip.' not in t.path:
                # Add file name + colon for files other than the first.
                if not first:
                    a.append('{}:'.format(fix_path(remove_prefix(t.path, test_temp_dir))))
                
                v = OutputVisitor()
                t.accept(v)
                s = v.output()
                if s != '':
                    a += s.split('\n')
            first = False
    except CompileError as e:
        a = e.messages
    assert_string_arrays_equal(expected, a, 'Invalid source code output ({}, line {})'.format(testcase.file, testcase.line))


def remove_prefix(path, prefix):
    regexp = '^' + prefix.replace('\\', '\\\\')
    np = re.sub(path, regexp, '')
    if np.startswith(separator):
        np = np[1:]
    return np


def fix_path(path):
    return path.replace('\\', '/')
