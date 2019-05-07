"""Generate CPython API wrapper function for a native function."""

from mypyc.common import PREFIX, NATIVE_PREFIX, DUNDER_PREFIX
from mypyc.emit import Emitter
from mypyc.ops import (
    ClassIR, FuncIR, RType, RuntimeArg,
    is_object_rprimitive, is_int_rprimitive, is_bool_rprimitive,
    bool_rprimitive,
    FUNC_STATICMETHOD,
)
from mypyc.namegen import NameGenerator
from typing import List, Optional


def wrapper_function_header(fn: FuncIR, names: NameGenerator) -> str:
    return 'PyObject *{prefix}{name}(PyObject *self, PyObject *args, PyObject *kw)'.format(
        prefix=PREFIX,
        name=fn.cname(names))


def generate_wrapper_function(fn: FuncIR, emitter: Emitter) -> None:
    """Generates a CPython-compatible wrapper function for a native function.

    In particular, this handles unboxing the arguments, calling the native function, and
    then boxing the return value.
    """
    emitter.emit_line('{} {{'.format(wrapper_function_header(fn, emitter.names)))

    # If fn is a method, then the first argument is a self param
    real_args = list(fn.args)
    if fn.class_name and not fn.decl.kind == FUNC_STATICMETHOD:
        arg = real_args.pop(0)
        emitter.emit_line('PyObject *obj_{} = self;'.format(arg.name))

    optional_args = [arg for arg in fn.args if arg.optional]

    arg_names = ''.join('"{}", '.format(arg.name) for arg in real_args)
    emitter.emit_line('static char *kwlist[] = {{{}0}};'.format(arg_names))
    for arg in real_args:
        emitter.emit_line('PyObject *obj_{}{};'.format(
                          arg.name, ' = NULL' if arg.optional else ''))
    arg_format = '{}{}:{}'.format(
        'O' * (len(real_args) - len(optional_args)),
        '|' + 'O' * len(optional_args) if len(optional_args) > 0 else '',
        fn.name,
    )
    arg_ptrs = ''.join(', &obj_{}'.format(arg.name) for arg in real_args)
    emitter.emit_lines(
        'if (!CPyArg_ParseTupleAndKeywords(args, kw, "{}", kwlist{})) {{'.format(
            arg_format, arg_ptrs),
        'return NULL;',
        '}')
    generate_wrapper_core(fn, emitter, optional_args)
    emitter.emit_line('}')


def generate_dunder_wrapper(cl: ClassIR, fn: FuncIR, emitter: Emitter) -> str:
    """Generates a wrapper for native __dunder__ methods to be able to fit into the mapping
    protocol slot. This specifically means that the arguments are taken as *PyObjects and returned
    as *PyObjects.
    """
    input_args = ', '.join('PyObject *obj_{}'.format(arg.name) for arg in fn.args)
    name = '{}{}{}'.format(DUNDER_PREFIX, fn.name, cl.name_prefix(emitter.names))
    emitter.emit_line('static PyObject *{name}({input_args}) {{'.format(
        name=name,
        input_args=input_args,
    ))
    generate_wrapper_core(fn, emitter)
    emitter.emit_line('}')

    return name


RICHCOMPARE_OPS = {
    '__lt__': 'Py_LT',
    '__gt__': 'Py_GT',
    '__le__': 'Py_LE',
    '__ge__': 'Py_GE',
    '__eq__': 'Py_EQ',
    '__ne__': 'Py_NE',
}


def generate_richcompare_wrapper(cl: ClassIR, emitter: Emitter) -> Optional[str]:
    """Generates a wrapper for richcompare dunder methods."""
    matches = [name for name in RICHCOMPARE_OPS if cl.has_method(name)]
    if not matches:
        return None

    name = '{}_RichCompare_{}'.format(DUNDER_PREFIX, cl.name_prefix(emitter.names))
    emitter.emit_line(
        'static PyObject *{name}(PyObject *obj_lhs, PyObject *obj_rhs, int op) {{'.format(
            name=name)
    )
    emitter.emit_line('switch (op) {')
    for func in matches:
        emitter.emit_line('case {}: {{'.format(RICHCOMPARE_OPS[func]))
        method = cl.get_method(func)
        assert method is not None
        generate_wrapper_core(method, emitter, arg_names=['lhs', 'rhs'])
        emitter.emit_line('}')
    emitter.emit_line('}')

    emitter.emit_line('Py_INCREF(Py_NotImplemented);')
    emitter.emit_line('return Py_NotImplemented;')

    emitter.emit_line('}')

    return name


def generate_get_wrapper(cl: ClassIR, fn: FuncIR, emitter: Emitter) -> str:
    """Generates a wrapper for native __get__ methods."""
    name = '{}{}{}'.format(DUNDER_PREFIX, fn.name, cl.name_prefix(emitter.names))
    emitter.emit_line(
        'static PyObject *{name}(PyObject *self, PyObject *instance, PyObject *owner) {{'.
        format(name=name))
    emitter.emit_line('instance = instance ? instance : Py_None;')
    emitter.emit_line('return {}{}(self, instance, owner);'.format(
        NATIVE_PREFIX,
        fn.cname(emitter.names)))
    emitter.emit_line('}')

    return name


def generate_hash_wrapper(cl: ClassIR, fn: FuncIR, emitter: Emitter) -> str:
    """Generates a wrapper for native __hash__ methods."""
    name = '{}{}{}'.format(DUNDER_PREFIX, fn.name, cl.name_prefix(emitter.names))
    emitter.emit_line('static Py_ssize_t {name}(PyObject *self) {{'.format(
        name=name
    ))
    emitter.emit_line('{}retval = {}{}(self);'.format(emitter.ctype_spaced(fn.ret_type),
                                                      NATIVE_PREFIX,
                                                      fn.cname(emitter.names)))
    emitter.emit_error_check('retval', fn.ret_type, 'return -1;')
    if is_int_rprimitive(fn.ret_type):
        emitter.emit_line('Py_ssize_t val = CPyTagged_AsSsize_t(retval);')
    else:
        emitter.emit_line('Py_ssize_t val = PyLong_AsSsize_t(retval);')
    emitter.emit_dec_ref('retval', fn.ret_type)
    emitter.emit_line('if (PyErr_Occurred()) return -1;')
    # We can't return -1 from a hash function..
    emitter.emit_line('if (val == -1) return -2;')
    emitter.emit_line('return val;')
    emitter.emit_line('}')

    return name


def generate_bool_wrapper(cl: ClassIR, fn: FuncIR, emitter: Emitter) -> str:
    """Generates a wrapper for native __bool__ methods."""
    name = '{}{}{}'.format(DUNDER_PREFIX, fn.name, cl.name_prefix(emitter.names))
    emitter.emit_line('static int {name}(PyObject *self) {{'.format(
        name=name
    ))
    emitter.emit_line('{}val = {}{}(self);'.format(emitter.ctype_spaced(fn.ret_type),
                                                   NATIVE_PREFIX,
                                                   fn.cname(emitter.names)))
    emitter.emit_error_check('val', fn.ret_type, 'return -1;')
    # This wouldn't be that hard to fix but it seems unimportant and
    # getting error handling and unboxing right would be fiddly. (And
    # way easier to do in IR!)
    assert is_bool_rprimitive(fn.ret_type), "Only bool return supported for __bool__"
    emitter.emit_line('return val;')
    emitter.emit_line('}')

    return name


def generate_wrapper_core(fn: FuncIR, emitter: Emitter,
                          optional_args: List[RuntimeArg] = [],
                          arg_names: Optional[List[str]] = None) -> None:
    """Generates the core part of a wrapper function for a native function.
    This expects each argument as a PyObject * named obj_{arg} as a precondition.
    It converts the PyObject *s to the necessary types, checking and unboxing if necessary,
    makes the call, then boxes the result if necessary and returns it.
    """
    arg_names = arg_names or [arg.name for arg in fn.args]
    for arg_name, arg in zip(arg_names, fn.args):
        generate_arg_check(arg_name, arg.type, emitter, arg in optional_args)
    native_args = ', '.join('arg_{}'.format(arg) for arg in arg_names)
    if fn.ret_type.is_unboxed:
        # TODO: The Py_RETURN macros return the correct PyObject * with reference count handling.
        #       Are they relevant?
        emitter.emit_line('{}retval = {}{}({});'.format(emitter.ctype_spaced(fn.ret_type),
                                                        NATIVE_PREFIX,
                                                        fn.cname(emitter.names),
                                                        native_args))
        emitter.emit_error_check('retval', fn.ret_type, 'return NULL;')
        emitter.emit_box('retval', 'retbox', fn.ret_type, declare_dest=True)
        emitter.emit_line('return retbox;')
    else:
        emitter.emit_line('return {}{}({});'.format(NATIVE_PREFIX,
                                                    fn.cname(emitter.names),
                                                    native_args))
        # TODO: Tracebacks?


def generate_arg_check(name: str, typ: RType, emitter: Emitter, optional: bool = False) -> None:
    """Insert a runtime check for argument and unbox if necessary.

    The object is named PyObject *obj_{}. This is expected to generate
    a value of name arg_{} (unboxed if necessary). For each primitive a runtime
    check ensures the correct type.
    """
    if typ.is_unboxed:
        # Borrow when unboxing to avoid reference count manipulation.
        emitter.emit_unbox('obj_{}'.format(name), 'arg_{}'.format(name), typ,
                           'return NULL;', declare_dest=True, borrow=True, optional=optional)
    elif is_object_rprimitive(typ):
        # Trivial, since any object is valid.
        if optional:
            emitter.emit_line('PyObject *arg_{};'.format(name))
            emitter.emit_line('if (obj_{} == NULL) {{'.format(name))
            emitter.emit_line('arg_{} = {};'.format(name, emitter.c_error_value(typ)))
            emitter.emit_lines('} else {', 'arg_{} = obj_{}; '.format(name, name), '}')
        else:
            emitter.emit_line('PyObject *arg_{} = obj_{};'.format(name, name))
    else:
        emitter.emit_cast('obj_{}'.format(name), 'arg_{}'.format(name), typ,
                          declare_dest=True, optional=optional)
        if optional:
            emitter.emit_line('if (obj_{} != NULL && arg_{} == NULL) return NULL;'.format(
                              name, name))
        else:
            emitter.emit_line('if (arg_{} == NULL) return NULL;'.format(name, name))
