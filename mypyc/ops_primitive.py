"""Primitive types and utilities for defining primitive ops.

Most of the ops can be automatically generated by matching against AST
nodes and types. For example, a func_op is automatically generated when
a specific function is called with the specific positional argument
count and argument types.
"""

from typing import Dict, List, Callable, Optional

from mypyc.ops import (
    OpDescription, PrimitiveOp, RType, EmitterInterface, EmitCallback, StealsDescription,
    short_name, bool_rprimitive
)


# Primitive binary ops (key is operator such as '+')
binary_ops = {}  # type: Dict[str, List[OpDescription]]
# Primitive unary ops (key is operator such as '-')
unary_ops = {}  # type: Dict[str, List[OpDescription]]
# Primitive ops for built-in functions (key is function name such as 'builtins.len')
func_ops = {}  # type: Dict[str, List[OpDescription]]
# Primitive ops for built-in methods (key is method name such as 'builtins.list.append')
method_ops = {}  # type: Dict[str, List[OpDescription]]
# Primitive ops for reading module attributes (key is name such as 'builtins.None')
name_ref_ops = {}  # type: Dict[str, OpDescription]


def simple_emit(template: str) -> EmitCallback:
    """Construct a simple PrimitiveOp emit callback function.

    It just applies a str.format template to
    'args', 'dest', 'comma_args', 'num_args', 'pre_comma_args'.

    For more complex cases you need to define a custom function.
    """

    def emit(emitter: EmitterInterface, args: List[str], dest: str) -> None:
        comma_args = ', '.join(args)
        pre_comma_args = ', ' + comma_args if comma_args else ''

        emitter.emit_line(template.format(
            args=args,
            dest=dest,
            comma_args=comma_args,
            pre_comma_args=pre_comma_args,
            num_args=len(args)))

    return emit


def name_emit(name: str) -> EmitCallback:
    return simple_emit('{dest} = %s;' % name)


def call_emit(func: str) -> EmitCallback:
    return simple_emit('{dest} = %s({comma_args});' % func)


def call_negative_bool_emit(func: str) -> EmitCallback:
    return simple_emit('{dest} = %s({comma_args}) >= 0;' % func)


def negative_int_emit(template: str) -> EmitCallback:
    """Construct a simple PrimitiveOp emit callback function that checks for -1 return."""

    def emit(emitter: EmitterInterface, args: List[str], dest: str) -> None:
        temp = emitter.temp_name()
        emitter.emit_line(template.format(args=args, dest='int %s' % temp,
                                          comma_args=', '.join(args)))
        emitter.emit_lines('if (%s < 0)' % temp,
                           '    %s = %s;' % (dest, emitter.c_error_value(bool_rprimitive)),
                           'else',
                           '    %s = %s;' % (dest, temp))

    return emit


def call_negative_magic_emit(func: str) -> EmitCallback:
    return negative_int_emit('{dest} = %s({comma_args});' % func)


def binary_op(op: str,
              arg_types: List[RType],
              result_type: RType,
              error_kind: int,
              emit: EmitCallback,
              format_str: Optional[str] = None,
              steals: StealsDescription = False,
              is_borrowed: bool = False,
              priority: int = 1) -> None:
    assert len(arg_types) == 2
    ops = binary_ops.setdefault(op, [])
    if format_str is None:
        format_str = '{dest} = {args[0]} %s {args[1]}' % op
    desc = OpDescription(op, arg_types, result_type, False, error_kind, format_str, emit,
                         steals, is_borrowed, priority)
    ops.append(desc)


def unary_op(op: str,
             arg_type: RType,
             result_type: RType,
             error_kind: int,
             emit: EmitCallback,
             format_str: Optional[str] = None,
             steals: StealsDescription = False,
             is_borrowed: bool = False,
             priority: int = 1) -> OpDescription:
    ops = unary_ops.setdefault(op, [])
    if format_str is None:
        format_str = '{dest} = %s{args[0]}' % op
    desc = OpDescription(op, [arg_type], result_type, False, error_kind, format_str, emit,
                         steals, is_borrowed, priority)
    ops.append(desc)
    return desc


def func_op(name: str,
            arg_types: List[RType],
            result_type: RType,
            error_kind: int,
            emit: EmitCallback,
            format_str: Optional[str] = None,
            steals: StealsDescription = False,
            is_borrowed: bool = False,
            priority: int = 1) -> OpDescription:
    ops = func_ops.setdefault(name, [])
    typename = ''
    if len(arg_types) == 1:
        typename = ' :: %s' % short_name(arg_types[0].name)
    if format_str is None:
        format_str = '{dest} = %s %s%s' % (short_name(name),
                                           ', '.join('{args[%d]}' % i
                                                     for i in range(len(arg_types))),
                                           typename)
    desc = OpDescription(name, arg_types, result_type, False, error_kind, format_str, emit,
                         steals, is_borrowed, priority)
    ops.append(desc)
    return desc


def method_op(name: str,
              arg_types: List[RType],
              result_type: Optional[RType],
              error_kind: int,
              emit: EmitCallback,
              steals: StealsDescription = False,
              is_borrowed: bool = False,
              priority: int = 1) -> OpDescription:
    """Define a primitive op that replaces a method call.

    Args:
        name: short name of the method (for example, 'append')
        arg_types: argument typess; the receiver is always the first argument
        result_type: type of the result, None if void
    """
    ops = method_ops.setdefault(name, [])
    assert len(arg_types) > 0
    args = ', '.join('{args[%d]}' % i
                     for i in range(1, len(arg_types)))
    type_name = short_name(arg_types[0].name)
    if name == '__getitem__':
        format_str = '{dest} = {args[0]}[{args[1]}] :: %s' % type_name
    else:
        format_str = '{dest} = {args[0]}.%s(%s) :: %s' % (name, args, type_name)
    desc = OpDescription(name, arg_types, result_type, False, error_kind, format_str, emit,
                         steals, is_borrowed, priority)
    ops.append(desc)
    return desc


def name_ref_op(name: str,
                result_type: RType,
                error_kind: int,
                emit: EmitCallback,
                is_borrowed: bool = False) -> OpDescription:
    """Define an op that is used to implement reading a module attribute.

    Args:
        name: fully-qualified name (e.g. 'builtins.None')
    """
    assert name not in name_ref_ops, 'already defined: %s' % name
    format_str = '{dest} = %s' % short_name(name)
    desc = OpDescription(name, [], result_type, False, error_kind, format_str, emit,
                         False, is_borrowed, 0)
    name_ref_ops[name] = desc
    return desc


def custom_op(arg_types: List[RType],
              result_type: RType,
              error_kind: int,
              emit: EmitCallback,
              name: Optional[str] = None,
              format_str: Optional[str] = None,
              steals: StealsDescription = False,
              is_borrowed: bool = False,
              is_var_arg: bool = False) -> OpDescription:
    """
    Create a one-off op that can't be automatically generated from the AST.

    Note that if the format_str argument is not provided, then a format_str is generated using the
    name argument. The name argument only needs to be provided if the format_str argument is not
    provided.
    """
    if name is not None and format_str is None:
        typename = ''
        if len(arg_types) == 1:
            typename = ' :: %s' % short_name(arg_types[0].name)
        format_str = '{dest} = %s %s%s' % (short_name(name),
                                       ', '.join('{args[%d]}' % i for i in range(len(arg_types))),
                                       typename)
    assert format_str is not None
    return OpDescription('<custom>', arg_types, result_type, is_var_arg, error_kind, format_str,
                         emit, steals, is_borrowed, 0)
