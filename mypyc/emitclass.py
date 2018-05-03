"""Code generation for native classes and related wrappers."""

import textwrap

from mypyc.common import NATIVE_PREFIX
from mypyc.emit import Emitter
from mypyc.emitfunc import native_function_header
from mypyc.ops import ClassIR, FuncIR, RType, ObjectRType, Environment, type_struct_name


def generate_class(cl: ClassIR, module: str, emitter: Emitter) -> None:
    """Generate C code for a class.

    This is the main entry point to the module.
    """
    name = cl.name
    fullname = '{}.{}'.format(module, name)
    new_name = '{}_new'.format(name)
    traverse_name = '{}_traverse'.format(name)
    clear_name = '{}_clear'.format(name)
    dealloc_name = '{}_dealloc'.format(name)
    getseters_name = '{}_getseters'.format(name)
    vtable_name = '{}_vtable'.format(name)

    def emit_line() -> None:
        emitter.emit_line()

    # Use dummy empty __init__ for now.
    # TODO: Use UserRType
    init = FuncIR(cl.name, [], ObjectRType(), [], Environment())
    emitter.emit_line(native_function_header(init) + ';')
    emit_line()
    generate_object_struct(cl, emitter)
    emit_line()
    generate_new_for_class(cl, new_name, vtable_name, emitter)
    emit_line()
    generate_traverse_for_class(cl, traverse_name, emitter)
    emit_line()
    generate_clear_for_class(cl, clear_name, emitter)
    emit_line()
    generate_dealloc_for_class(cl, dealloc_name, clear_name, emitter)
    emit_line()
    generate_native_getters_and_setters(cl, emitter)
    generate_vtable(cl, vtable_name, emitter)
    emit_line()
    generate_getseter_declarations(cl, emitter)
    emit_line()
    generate_getseters_table(cl, getseters_name, emitter)
    emit_line()

    emitter.emit_line(textwrap.dedent("""\
        static PyTypeObject {type_struct} = {{
            PyVarObject_HEAD_INIT(NULL, 0)
            "{fullname}",              /* tp_name */
            sizeof({struct_name}),     /* tp_basicsize */
            0,                         /* tp_itemsize */
            (destructor){dealloc_name},  /* tp_dealloc */
            0,                         /* tp_print */
            0,                         /* tp_getattr */
            0,                         /* tp_setattr */
            0,                         /* tp_reserved */
            0,                         /* tp_repr */
            0,                         /* tp_as_number */
            0,                         /* tp_as_sequence */
            0,                         /* tp_as_mapping */
            0,                         /* tp_hash  */
            0,                         /* tp_call */
            0,                         /* tp_str */
            0,                         /* tp_getattro */
            0,                         /* tp_setattro */
            0,                         /* tp_as_buffer */
            Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC, /* tp_flags */
            0,                         /* tp_doc */
            (traverseproc){traverse_name}, /* tp_traverse */
            (inquiry){clear_name},     /* tp_clear */
            0,                         /* tp_richcompare */
            0,                         /* tp_weaklistoffset */
            0,                         /* tp_iter */
            0,                         /* tp_iternext */
            0,                         /* tp_methods */
            0,                         /* tp_members */
            {getseters_name},          /* tp_getset */
            0,                         /* tp_base */
            0,                         /* tp_dict */
            0,                         /* tp_descr_get */
            0,                         /* tp_descr_set */
            0,                         /* tp_dictoffset */
            0,                         /* tp_init */
            0,                         /* tp_alloc */
            {new_name},                /* tp_new */
        }};\
        """).format(type_struct=type_struct_name(cl.name),
                    struct_name=cl.struct_name,
                    fullname=fullname,
                    traverse_name=traverse_name,
                    clear_name=clear_name,
                    dealloc_name=dealloc_name,
                    new_name=new_name,
                    getseters_name=getseters_name))
    emitter.emit_line()
    generate_constructor_for_class(cl, new_name, vtable_name, emitter)
    emitter.emit_line()
    generate_getseters(cl, emitter)


def getter_name(cl: str, attribute: str) -> str:
    return '{}_get{}'.format(cl, attribute)


def setter_name(cl: str, attribute: str) -> str:
    return '{}_set{}'.format(cl, attribute)


def native_getter_name(cl: str, attribute: str) -> str:
    return 'native_{}_get{}'.format(cl, attribute)


def native_setter_name(cl: str, attribute: str) -> str:
    return 'native_{}_set{}'.format(cl, attribute)


def generate_object_struct(cl: ClassIR, emitter: Emitter) -> None:
    emitter.emit_lines('typedef struct {',
                       'PyObject_HEAD',
                       'CPyVTableItem *vtable;')
    for attr, rtype in cl.attributes:
        emitter.emit_line('{}{};'.format(rtype.ctype_spaced, attr))
    emitter.emit_line('}} {};'.format(cl.struct_name))


def generate_native_getters_and_setters(cl: ClassIR,
                                        emitter: Emitter) -> None:
    for attr, rtype in cl.attributes:
        # Native getter
        emitter.emit_line('{}{}({} *self)'.format(rtype.ctype_spaced,
                                               native_getter_name(cl.name, attr),
                                               cl.struct_name))
        emitter.emit_line('{')
        if rtype.is_refcounted:
            emitter.emit_lines(
                'if (self->{} == {}) {{'.format(attr, rtype.c_undefined_value),
                'PyErr_SetString(PyExc_AttributeError, "attribute {} of {} undefined");'.format(
                    repr(attr), repr(cl.name)),
                '} else {')
            emitter.emit_inc_ref('self->{}'.format(attr), rtype)
            emitter.emit_line('}')
        emitter.emit_line('return self->{};'.format(attr))
        emitter.emit_line('}')
        emitter.emit_line()

        # Native setter
        emitter.emit_line('bool {}({} *self, {}value)'.format(native_setter_name(cl.name, attr),
                                                          cl.struct_name,
                                                          rtype.ctype_spaced))
        emitter.emit_line('{')
        if rtype.is_refcounted:
            emitter.emit_line('if (self->{} != {}) {{'.format(attr, rtype.c_undefined_value))
            emitter.emit_dec_ref('self->{}'.format(attr), rtype)
            emitter.emit_line('}')
        emitter.emit_inc_ref('value'.format(attr), rtype)
        emitter.emit_lines('self->{} = value;'.format(attr),
                           'return 1;',
                           '}')
        emitter.emit_line()


def generate_vtable(cl: ClassIR,
                    vtable_name: str,
                    emitter: Emitter) -> None:
    emitter.emit_line('static CPyVTableItem {}[] = {{'.format(vtable_name))
    for attr, rtype in cl.attributes:
        emitter.emit_line('(CPyVTableItem){},'.format(native_getter_name(cl.name, attr)))
        emitter.emit_line('(CPyVTableItem){},'.format(native_setter_name(cl.name, attr)))
    emitter.emit_line('};')


def generate_constructor_for_class(cl: ClassIR,
                                   func_name: str,
                                   vtable_name: str,
                                   emitter: Emitter) -> None:
    """Generate a native function that constructs an instance of a class."""
    emitter.emit_line('static PyObject *')
    emitter.emit_line('{}{}(void)'.format(NATIVE_PREFIX, cl.name))
    emitter.emit_line('{')
    emitter.emit_line('{} *self;'.format(cl.struct_name))
    emitter.emit_line('self = ({} *){}.tp_alloc(&{}, 0);'.format(cl.struct_name,
                                                                 cl.type_struct,
                                                                 cl.type_struct))
    emitter.emit_line('if (self == NULL)')
    emitter.emit_line('    return NULL;')
    emitter.emit_line('self->vtable = {};'.format(vtable_name))
    for attr, rtype in cl.attributes:
        emitter.emit_line('self->{} = {};'.format(attr, rtype.c_undefined_value))
    emitter.emit_line('return (PyObject *)self;')
    emitter.emit_line('}')


def generate_new_for_class(cl: ClassIR,
                           func_name: str,
                           vtable_name: str,
                           emitter: Emitter) -> None:
    emitter.emit_line('static PyObject *')
    emitter.emit_line(
        '{}(PyTypeObject *type, PyObject *args, PyObject *kwds)'.format(func_name))
    emitter.emit_line('{')
    # TODO: Check and unbox arguments
    emitter.emit_line('return {}{}();'.format(NATIVE_PREFIX, cl.name))
    emitter.emit_line('}')


def generate_traverse_for_class(cl: ClassIR,
                                func_name: str,
                                emitter: Emitter) -> None:
    """Emit function that performs cycle GC traversal of an instance."""
    emitter.emit_line('static int')
    emitter.emit_line('{}({} *self, visitproc visit, void *arg)'.format(func_name,
                                                                        cl.struct_name))
    emitter.emit_line('{')
    for attr, rtype in cl.attributes:
        emitter.emit_gc_visit('self->{}'.format(attr), rtype)
    emitter.emit_line('return 0;')
    emitter.emit_line('}')


def generate_clear_for_class(cl: ClassIR,
                             func_name: str,
                             emitter: Emitter) -> None:
    emitter.emit_line('static int')
    emitter.emit_line('{}({} *self)'.format(func_name, cl.struct_name))
    emitter.emit_line('{')
    for attr, rtype in cl.attributes:
        emitter.emit_gc_clear('self->{}'.format(attr), rtype)
    emitter.emit_line('return 0;')
    emitter.emit_line('}')


def generate_dealloc_for_class(cl: ClassIR,
                               dealloc_func_name: str,
                               clear_func_name: str,
                               emitter: Emitter) -> None:
    emitter.emit_line('static void')
    emitter.emit_line('{}({} *self)'.format(dealloc_func_name, cl.struct_name))
    emitter.emit_line('{')
    emitter.emit_line('PyObject_GC_UnTrack(self);')
    emitter.emit_line('{}(self);'.format(clear_func_name))
    emitter.emit_line('Py_TYPE(self)->tp_free((PyObject *)self);')
    emitter.emit_line('}')


def generate_getseter_declarations(cl: ClassIR, emitter: Emitter) -> None:
    for attr, rtype in cl.attributes:
        emitter.emit_line('static PyObject *')
        emitter.emit_line('{}({} *self, void *closure);'.format(getter_name(cl.name, attr),
                                                            cl.struct_name))
        emitter.emit_line('static int')
        emitter.emit_line('{}({} *self, PyObject *value, void *closure);'.format(
            setter_name(cl.name, attr),
            cl.struct_name))


def generate_getseters_table(cl: ClassIR,
                             name: str,
                             emitter: Emitter) -> None:

    emitter.emit_line('static PyGetSetDef {}[] = {{'.format(name))
    for attr, rtype in cl.attributes:
        emitter.emit_line('{{"{}",'.format(attr))
        emitter.emit_line(' (getter){}, (setter){},'.format(getter_name(cl.name, attr),
                                                            setter_name(cl.name, attr)))
        emitter.emit_line(' NULL, NULL},')
    emitter.emit_line('{NULL}  /* Sentinel */')
    emitter.emit_line('};')


def generate_getseters(cl: ClassIR, emitter: Emitter) -> None:
    for i, (attr, rtype) in enumerate(cl.attributes):
        generate_getter(cl, attr, rtype, emitter)
        emitter.emit_line('')
        generate_setter(cl, attr, rtype, emitter)
        if i < len(cl.attributes) - 1:
            emitter.emit_line('')


def generate_getter(cl: ClassIR,
                    attr: str,
                    rtype: RType,
                    emitter: Emitter) -> None:
    emitter.emit_line('static PyObject *')
    emitter.emit_line('{}({} *self, void *closure)'.format(getter_name(cl.name, attr),
                                                                        cl.struct_name))
    emitter.emit_line('{')
    emitter.emit_line('if (self->{} == {}) {{'.format(attr, rtype.c_undefined_value))
    emitter.emit_line('PyErr_SetString(PyExc_AttributeError,')
    emitter.emit_line('    "attribute {} of {} undefined");'.format(repr(attr),
                                                                        repr(cl.name)))
    emitter.emit_line('return NULL;')
    emitter.emit_line('}')
    emitter.emit_inc_ref('self->{}'.format(attr), rtype)
    emitter.emit_box('self->{}'.format(attr), 'retval', rtype, declare_dest=True)
    emitter.emit_line('return retval;')
    emitter.emit_line('}')


def generate_setter(cl: ClassIR,
                    attr: str,
                    rtype: RType,
                    emitter: Emitter) -> None:
    emitter.emit_line('static int')
    emitter.emit_line('{}({} *self, PyObject *value, void *closure)'.format(
        setter_name(cl.name, attr),
        cl.struct_name))
    emitter.emit_line('{')
    if rtype.is_refcounted:
        emitter.emit_line('if (self->{} != {}) {{'.format(attr, rtype.c_undefined_value))
        emitter.emit_dec_ref('self->{}'.format(attr), rtype)
        emitter.emit_line('}')
    emitter.emit_line('if (value != NULL) {')
    if rtype.supports_unbox:
        emitter.emit_unbox('value', 'tmp', rtype, custom_failure='return -1;', declare_dest=True)
    else:
        emitter.emit_cast('value', 'tmp', rtype, declare_dest=True)
        emitter.emit_lines('if (!tmp)',
                           '    return -1;')
        emitter.emit_inc_ref('tmp', rtype)
    emitter.emit_line('self->{} = tmp;'.format(attr))
    emitter.emit_line('} else')
    emitter.emit_line('    self->{} = {};'.format(attr, rtype.c_undefined_value))
    emitter.emit_line('return 0;')
    emitter.emit_line('}')
