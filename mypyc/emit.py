"""Utilities for emitting C code."""

from typing import List, Set, Dict

from mypyc.common import REG_PREFIX
from mypyc.ops import (
    Environment, Label, Register, RType, ObjectRType, TupleRType, UserRType, OptionalRType,
    IntRType, type_struct_name
)


class HeaderDeclaration:
    def __init__(self, dependencies: Set[str], body: List[str]) -> None:
        self.dependencies = dependencies
        self.body = body


class EmitterContext:
    """Shared emitter state for an entire module."""

    def __init__(self) -> None:
        self.temp_counter = 0

        # A map of a C identifier to whatever the C identifier declares. Currently this is
        # used for declaring structs and the key corresponds to the name of the struct.
        # The declaration contains the body of the struct.
        self.declarations = {} # type: Dict[str, HeaderDeclaration]


class Emitter:
    """Helper for C code generation."""

    def __init__(self, context: EmitterContext, env: Environment = None) -> None:
        self.context = context
        self.env = env or Environment()
        self.fragments = []  # type: List[str]
        self._indent = 0

    # Low-level operations

    def indent(self) -> None:
        self._indent += 4

    def dedent(self) -> None:
        self._indent -= 4
        assert self._indent >= 0

    def label(self, label: Label) -> str:
        return 'CPyL%d' % label

    def reg(self, reg: Register) -> str:
        name = self.env.names[reg]
        return REG_PREFIX + name

    def emit_line(self, line: str = '') -> None:
        if line.startswith('}'):
            self.dedent()
        self.fragments.append(self._indent * ' ' + line + '\n')
        if line.endswith('{'):
            self.indent()

    def emit_lines(self, *lines: str) -> None:
        for line in lines:
            self.emit_line(line)

    def emit_label(self, label: Label) -> None:
        # Extra semicolon prevents an error when the next line declares a tempvar
        self.fragments.append('{}: ;\n'.format(self.label(label)))

    def emit_from_emitter(self, emitter: 'Emitter') -> None:
        self.fragments.extend(emitter.fragments)

    def emit_printf(self, fmt: str, *args: str) -> None:
        fmt = fmt.replace('\n', '\\n')
        self.emit_line('printf(%s);' % ', '.join(['"%s"' % fmt] + list(args)))
        self.emit_line('fflush(stdout);')

    def temp_name(self) -> str:
        self.context.temp_counter += 1
        return '__tmp%d' % self.context.temp_counter

    # Higher-level operations

    def declare_tuple_struct(self, tuple_type: TupleRType) -> None:
        if tuple_type.struct_name not in self.context.declarations:
            dependencies = set()
            for typ in tuple_type.types:
                # XXX other types might eventually need similar behavior
                if isinstance(typ, TupleRType):
                    dependencies.add(typ.struct_name)

            self.context.declarations[tuple_type.struct_name] = HeaderDeclaration(
                dependencies,
                tuple_type.get_c_declaration(),
            )

    def emit_inc_ref(self, dest: str, rtype: RType) -> None:
        """Increment reference count of C expression `dest`.

        For composite unboxed structures (e.g. tuples) recursively
        increment reference counts for each component.
        """
        if rtype.name == 'int':
            self.emit_line('CPyTagged_IncRef(%s);' % dest)
        elif isinstance(rtype, TupleRType):
            for i, item_type in enumerate(rtype.types):
                self.emit_inc_ref('{}.f{}'.format(dest, i), item_type)
        elif not rtype.supports_unbox:
            self.emit_line('Py_INCREF(%s);' % dest)
        # Otherwise assume it's an unboxed, pointerless value and do nothing.

    def emit_dec_ref(self, dest: str, rtype: RType) -> None:
        """Decrement reference count of C expression `dest`.

        For composite unboxed structures (e.g. tuples) recursively
        decrement reference counts for each component.
        """
        if rtype.name == 'int':
            self.emit_line('CPyTagged_DecRef(%s);' % dest)
        elif isinstance(rtype, TupleRType):
            for i, item_type in enumerate(rtype.types):
                self.emit_dec_ref('{}.f{}'.format(dest, i), item_type)
        elif not rtype.supports_unbox:
            self.emit_line('Py_DECREF(%s);' % dest)
        # Otherwise assume it's an unboxed, pointerless value and do nothing.

    def emit_cast(self, src: str, dest: str, typ: RType, failure: str,
                  declare_dest: bool = False) -> None:
        """Emit code for casting a value of given type (works for boxed types only).

        Evaluate C code in 'failure' if the value has an incompatible type.

        Always copy/steal the reference in src.

        Args:
            src: Name of source C variable
            dest: Name of target C variable
            typ: Type of value
            failure: What happens on error
            declare_dest: If True, also declare the variable 'dest'
        """
        # TODO: Verify refcount handling.
        failure = '    ' + failure
        if typ.name in ('list', 'dict'):
            if declare_dest:
                self.emit_line('PyObject *{};'.format(dest))
            if typ.name == 'list':
                prefix = 'PyList'
            elif typ.name == 'dict':
                prefix = 'PyDict'
            else:
                assert False, prefix
            self.emit_lines(
                'if ({}_Check({}))'.format(prefix, src),
                '    {} = {};'.format(dest, src),
                'else',
                failure)
        elif typ.name == 'sequence_tuple':
            self.emit_lines(
                'if (!PyTuple_Check({}))'.format(src),
                failure)
            if declare_dest:
                self.emit_line('{} {} = {};'.format(typ.ctype, dest, src))
            else:
                self.emit_line('{} = {};'.format(dest, src))
        elif isinstance(typ, UserRType):
            if declare_dest:
                self.emit_line('PyObject *{};'.format(dest))
            self.emit_lines(
                'if (PyObject_TypeCheck({}, &{}))'.format(src, type_struct_name(typ.name)),
                '    {} = {};'.format(dest, src),
                'else',
                failure)
        elif typ.name == 'None':
            if declare_dest:
                self.emit_line('PyObject *{};'.format(dest))
            self.emit_lines(
                'if ({} == Py_None)'.format(src),
                '    {} = {};'.format(dest, src),
                'else',
                failure)
        elif isinstance(typ, OptionalRType):
            if declare_dest:
                self.emit_line('PyObject *{};'.format(dest))
            self.emit_lines(
                'if ({} == Py_None)'.format(src),
                '    {} = {};'.format(dest, src),
                'else {')
            self.emit_cast(src, dest, typ.value_type, failure.lstrip())
            self.emit_line('}')
        else:
            assert False, 'Cast not implemented: %s' % typ

    def emit_unbox(self, src: str, dest: str, typ: RType, failure: str,
                   declare_dest: bool = False, borrow: bool = False) -> None:
        """Emit code for unboxing a value of given type (from PyObject *).

        Evaluate C code in 'failure' if the value has an incompatible type.

        Always generate a new reference.

        Args:
            src: Name of source C variable
            dest: Name of target C variable
            typ: Type of value
            failure: What happens on error
            declare_dest: If True, also declare the variable 'dest'
            borrow: If True, create a borrowed reference
        """
        # TODO: Verify refcount handling.
        failure = '    ' + failure
        if typ.name == 'int':
            if declare_dest:
                self.emit_line('CPyTagged {};'.format(dest))
            self.emit_line('if (PyLong_Check({}))'.format(src))
            if borrow:
                self.emit_line('    {} = CPyTagged_BorrowFromObject({});'.format(dest, src))
            else:
                self.emit_line('    {} = CPyTagged_FromObject({});'.format(dest, src))
            self.emit_lines('else',
                            failure)
        elif typ.name == 'bool':
            # Whether we are borrowing or not makes no difference.
            self.emit_lines(
                'if (!PyBool_Check({}))'.format(src),
                failure)
            conversion = 'PyObject_IsTrue({})'.format(src)
            if declare_dest:
                self.emit_line('char {} = {};'.format(dest, conversion))
            else:
                self.emit_line('{} = {};'.format(dest, conversion))
        elif isinstance(typ, TupleRType):
            self.declare_tuple_struct(typ)
            self.emit_lines(
                'if (!PyTuple_Check({}) || PyTuple_Size({}) != {})'.format(src, src,
                                                                           len(typ.types)),
                failure)  # TODO: Decrease refcount?
            if declare_dest:
                self.emit_line('{} {};'.format(typ.ctype, dest))
            for i, item_type in enumerate(typ.types):
                temp = self.temp_name()
                self.emit_line('PyObject *{} = PyTuple_GetItem({}, {});'.format(temp, src, i))
                temp2 = self.temp_name()
                # Unbox or check the item.
                if item_type.supports_unbox:
                    self.emit_unbox(temp, temp2, item_type, failure, declare_dest=True,
                                    borrow=borrow)
                else:
                    if not borrow:
                        self.emit_inc_ref(temp, ObjectRType())
                    self.emit_cast(temp, temp2, item_type, failure, declare_dest=True)
                self.emit_line('{}.f{} = {};'.format(dest, i, temp2))
        else:
            assert False, 'Unboxing not implemented: %s' % typ

    def emit_box(self, src: str, dest: str, typ: RType, failure: str,
                 declare_dest: bool = False) -> None:
        """Emit code for boxing a value of give type.

        Generate a simple assignment if no boxing is needed.

        The source reference count is stolen for the result (no need to decref afterwards).
        """
        if declare_dest:
            declaration = 'PyObject *'
        else:
            declaration = ''
        if typ.name == 'int':
            # Steal the existing reference if it exists.
            self.emit_line('{}{} = CPyTagged_StealAsObject({});'.format(declaration, dest, src))
        elif typ.name == 'bool':
            # TODO: The Py_RETURN macros return the correct PyObject * with reference count
            #       handling. Relevant here?
            self.emit_lines('{}{} = PyBool_FromLong({});'.format(declaration, dest, src))
        elif isinstance(typ, TupleRType):
            self.declare_tuple_struct(typ)
            self.emit_line('{}{} = PyTuple_New({});'.format(declaration, dest, len(typ.types)))
            self.emit_line('if ({} == NULL) {{'.format(dest))
            self.emit_line('{}'.format(failure)) # TODO: Decrease refcounts?
            self.emit_line('}')
            # TODO: Fail if dest is None
            for i in range(0, len(typ.types)):
                if not typ.supports_unbox:
                    self.emit_line('PyTuple_SetItem({}, {}, {}.f{}'.format(dest, i, src, i))
                else:
                    inner_name = self.temp_name()
                    self.emit_box('{}.f{}'.format(src, i), inner_name, typ.types[i], failure,
                                  declare_dest=True)
                    self.emit_line('PyTuple_SetItem({}, {}, {});'.format(dest, i, inner_name, i))
        else:
            assert not typ.supports_unbox
            # Type is boxed -- trivially just assign.
            self.emit_line('{}{} = {};'.format(declaration, dest, src))

    def emit_error_check(self, value: str, rtype: RType, failure: str) -> None:
        """Emit code for checking a native function return value for uncaught exception."""
        if not isinstance(rtype, TupleRType):
            self.emit_line('if ({} == {}) {{'.format(value, rtype.c_error_value))
        else:
            self.emit_line('if ({}.f0 == {}) {{'.format(value, rtype.types[0].c_error_value))
        self.emit_lines(failure, '}')

    def emit_gc_visit(self, target: str, rtype: RType) -> None:
        """Emit code for GC visiting a C variable reference.

        Assume that 'target' represents a C expression that refers to a
        struct member, such as 'self->x'.
        """
        if not rtype.is_refcounted:
            # Not refcounted -> no pointers -> no GC interaction.
            return
        elif isinstance(rtype, IntRType):
            self.emit_line('if (CPyTagged_CheckLong({})) {{'.format(target))
            self.emit_line('Py_VISIT(CPyTagged_LongAsObject({}));'.format(target))
            self.emit_line('}')
        elif isinstance(rtype, TupleRType):
            for i, item_type in enumerate(rtype.types):
                self.emit_gc_visit('{}.f{}'.format(target, i), item_type)
        elif rtype.ctype == 'PyObject *':
            # The simplest case.
            self.emit_line('Py_VISIT({});'.format(target))
        else:
            assert False, 'emit_gc_visit() not implemented for %s' % repr(rtype)

    def emit_gc_clear(self, target: str, rtype: RType) -> None:
        """Emit code for clearing a C attribute reference for GC.

        Assume that 'target' represents a C expression that refers to a
        struct member, such as 'self->x'.
        """
        if not rtype.is_refcounted:
            # Not refcounted -> no pointers -> no GC interaction.
            return
        elif isinstance(rtype, IntRType):
            self.emit_line('if (CPyTagged_CheckLong({})) {{'.format(target))
            self.emit_line('CPyTagged __tmp = {};'.format(target))
            self.emit_line('{} = {};'.format(target, rtype.c_undefined_value))
            self.emit_line('Py_XDECREF(CPyTagged_LongAsObject(__tmp));')
            self.emit_line('}')
        elif isinstance(rtype, TupleRType):
            for i, item_type in enumerate(rtype.types):
                self.emit_gc_clear('{}.f{}'.format(target, i), item_type)
        elif rtype.ctype == 'PyObject *' and rtype.c_undefined_value == 'NULL':
            # The simplest case.
            self.emit_line('Py_CLEAR({});'.format(target))
        else:
            assert False, 'emit_gc_clear() not implemented for %s' % repr(rtype)
