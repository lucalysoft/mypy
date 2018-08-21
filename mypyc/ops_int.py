from typing import List

from mypyc.ops import (
    PrimitiveOp, int_rprimitive, bool_rprimitive, float_rprimitive, object_rprimitive,
    RType, EmitterInterface, OpDescription,
    ERR_NEVER, ERR_MAGIC,
)
from mypyc.ops_primitive import name_ref_op, binary_op, unary_op, func_op, simple_emit

# These int constructors produce object_rprimitives that then need to be unboxed
# I guess unboxing ourselves would save a check and branch though?

# For ordinary calls to int() we use a name_ref to the type
name_ref_op('builtins.int',
            result_type=object_rprimitive,
            error_kind=ERR_NEVER,
            emit=simple_emit('{dest} = (PyObject *)&PyLong_Type;'),
            is_borrowed=True)

# Convert from a float. We could do a bit better directly.
func_op(
    name='builtins.int',
    arg_types=[float_rprimitive],
    result_type=object_rprimitive,
    error_kind=ERR_MAGIC,
    emit=simple_emit(
        '{dest} = PyLong_FromDouble(PyFloat_AS_DOUBLE({args[0]}));'),
    priority=1)


def int_binary_op(op: str, c_func_name: str, result_type: RType = int_rprimitive) -> None:
    binary_op(op=op,
              arg_types=[int_rprimitive, int_rprimitive],
              result_type=result_type,
              error_kind=ERR_NEVER,
              format_str='{dest} = {args[0]} %s {args[1]} :: int' % op,
              emit=simple_emit('{dest} = %s({args[0]}, {args[1]});' % c_func_name))


def int_compare_op(op: str, c_func_name: str) -> None:
    int_binary_op(op, c_func_name, bool_rprimitive)


int_binary_op('+', 'CPyTagged_Add')
int_binary_op('-', 'CPyTagged_Subtract')
int_binary_op('*', 'CPyTagged_Multiply')
int_binary_op('//', 'CPyTagged_FloorDivide')
int_binary_op('%', 'CPyTagged_Remainder')

# this should work because assignment operators are parsed differently
# and the code in genops that handles it does the assignment
# regardless of whether or not the operator works in place anyway
int_binary_op('+=', 'CPyTagged_Add')
int_binary_op('-=', 'CPyTagged_Subtract')
int_binary_op('*=', 'CPyTagged_Multiply')
int_binary_op('//=', 'CPyTagged_FloorDivide')
int_binary_op('%=', 'CPyTagged_Remainder')

int_compare_op('==', 'CPyTagged_IsEq')
int_compare_op('!=', 'CPyTagged_IsNe')
int_compare_op('<', 'CPyTagged_IsLt')
int_compare_op('<=', 'CPyTagged_IsLe')
int_compare_op('>', 'CPyTagged_IsGt')
int_compare_op('>=', 'CPyTagged_IsGe')


def int_unary_op(op: str, c_func_name: str) -> OpDescription:
    return unary_op(op=op,
                    arg_type=int_rprimitive,
                    result_type=int_rprimitive,
                    error_kind=ERR_NEVER,
                    format_str='{dest} = %s{args[0]} :: int' % op,
                    emit=simple_emit('{dest} = %s({args[0]});' % c_func_name))


int_neg_op = int_unary_op('-', 'CPyTagged_Negate')
