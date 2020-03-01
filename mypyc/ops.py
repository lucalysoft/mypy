"""Representation of low-level opcodes for compiler intermediate representation (IR).

Opcodes operate on abstract registers in a register machine. Each
register has a type and a name, specified in an environment. A register
can hold various things:

- local variables
- intermediate values of expressions
- condition flags (true/false)
- literals (integer literals, True, False, etc.)
"""

from abc import abstractmethod
from typing import (
    List, Sequence, Dict, Generic, TypeVar, Optional, Any, NamedTuple, Tuple, Callable,
    Union, Iterable, Set
)
from collections import OrderedDict

from typing_extensions import Final, Type, ClassVar, TYPE_CHECKING
from mypy_extensions import trait

from mypy.nodes import ARG_NAMED_OPT, ARG_OPT, ARG_POS, Block, FuncDef, SymbolNode

from mypyc.namegen import NameGenerator

if TYPE_CHECKING:
    from mypyc.class_ir import ClassIR

T = TypeVar('T')

JsonDict = Dict[str, Any]


class RType:
    """Abstract base class for runtime types (erased, only concrete; no generics)."""

    name = None  # type: str
    is_unboxed = False
    c_undefined = None  # type: str
    is_refcounted = True  # If unboxed: does the unboxed version use reference counting?
    _ctype = None  # type: str  # C type; use Emitter.ctype() to access

    @abstractmethod
    def accept(self, visitor: 'RTypeVisitor[T]') -> T:
        raise NotImplementedError

    def short_name(self) -> str:
        return short_name(self.name)

    def __str__(self) -> str:
        return short_name(self.name)

    def __repr__(self) -> str:
        return '<%s>' % self.__class__.__name__

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RType) and other.name == self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def serialize(self) -> Union[JsonDict, str]:
        raise NotImplementedError('Cannot serialize {} instance'.format(self.__class__.__name__))


# We do a three-pass deserialization scheme in order to resolve name
# references.
#  1. Create an empty ClassIR for each class in an SCC.
#  2. Deserialize all of the functions, which can contain references
#     to ClassIRs in their types
#  3. Deserialize all of the classes, which contain lots of references
#     to the functions they contain. (And to other classes.)
#
# Note that this approach differs from how we deserialize ASTs in mypy itself,
# where everything is deserialized in one pass then a second pass cleans up
# 'cross_refs'. We don't follow that approach here because it seems to be more
# code for not a lot of gain since it is easy in mypyc to identify all the objects
# we might need to reference.
#
# Because of these references, we need to maintain maps from class
# names to ClassIRs and func names to FuncIRs.
#
# These are tracked in a DeserMaps which is passed to every
# deserialization function.
#
# (Serialization and deserialization *will* be used for incremental
# compilation but so far it is not hooked up to anything.)
DeserMaps = NamedTuple('DeserMaps',
                       [('classes', Dict[str, 'ClassIR']), ('functions', Dict[str, 'FuncIR'])])


def deserialize_type(data: Union[JsonDict, str], ctx: DeserMaps) -> 'RType':
    """Deserialize a JSON-serialized RType.

    Arguments:
        data: The decoded JSON of the serialized type
        ctx: The deserialization maps to use
    """
    # Since there are so few types, we just case on them directly.  If
    # more get added we should switch to a system like mypy.types
    # uses.
    if isinstance(data, str):
        if data in ctx.classes:
            return RInstance(ctx.classes[data])
        elif data in RPrimitive.primitive_map:
            return RPrimitive.primitive_map[data]
        elif data == "void":
            return RVoid()
        else:
            assert False, "Can't find class {}".format(data)
    elif data['.class'] == 'RTuple':
        return RTuple.deserialize(data, ctx)
    elif data['.class'] == 'RUnion':
        return RUnion.deserialize(data, ctx)
    raise NotImplementedError('unexpected .class {}'.format(data['.class']))


class RTypeVisitor(Generic[T]):
    @abstractmethod
    def visit_rprimitive(self, typ: 'RPrimitive') -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_rinstance(self, typ: 'RInstance') -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_runion(self, typ: 'RUnion') -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_rtuple(self, typ: 'RTuple') -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_rvoid(self, typ: 'RVoid') -> T:
        raise NotImplementedError


class RVoid(RType):
    """void"""

    is_unboxed = False
    name = 'void'
    ctype = 'void'

    def accept(self, visitor: 'RTypeVisitor[T]') -> T:
        return visitor.visit_rvoid(self)

    def serialize(self) -> str:
        return 'void'


void_rtype = RVoid()  # type: Final


class RPrimitive(RType):
    """Primitive type such as 'object' or 'int'.

    These often have custom ops associated with them.
    """

    # Map from primitive names to primitive types and is used by deserialization
    primitive_map = {}  # type: ClassVar[Dict[str, RPrimitive]]

    def __init__(self,
                 name: str,
                 is_unboxed: bool,
                 is_refcounted: bool,
                 ctype: str = 'PyObject *') -> None:
        RPrimitive.primitive_map[name] = self

        self.name = name
        self.is_unboxed = is_unboxed
        self._ctype = ctype
        self.is_refcounted = is_refcounted
        if ctype == 'CPyTagged':
            self.c_undefined = 'CPY_INT_TAG'
        elif ctype == 'PyObject *':
            self.c_undefined = 'NULL'
        elif ctype == 'char':
            self.c_undefined = '2'
        else:
            assert False, 'Unrecognized ctype: %r' % ctype

    def accept(self, visitor: 'RTypeVisitor[T]') -> T:
        return visitor.visit_rprimitive(self)

    def serialize(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return '<RPrimitive %s>' % self.name


# Used to represent arbitrary objects and dynamically typed values
object_rprimitive = RPrimitive('builtins.object', is_unboxed=False,
                               is_refcounted=True)  # type: Final

int_rprimitive = RPrimitive('builtins.int', is_unboxed=True, is_refcounted=True,
                            ctype='CPyTagged')  # type: Final

short_int_rprimitive = RPrimitive('short_int', is_unboxed=True, is_refcounted=False,
                                  ctype='CPyTagged')  # type: Final

float_rprimitive = RPrimitive('builtins.float', is_unboxed=False,
                              is_refcounted=True)  # type: Final

bool_rprimitive = RPrimitive('builtins.bool', is_unboxed=True, is_refcounted=False,
                             ctype='char')  # type: Final

none_rprimitive = RPrimitive('builtins.None', is_unboxed=True, is_refcounted=False,
                             ctype='char')  # type: Final

list_rprimitive = RPrimitive('builtins.list', is_unboxed=False, is_refcounted=True)  # type: Final

dict_rprimitive = RPrimitive('builtins.dict', is_unboxed=False, is_refcounted=True)  # type: Final

set_rprimitive = RPrimitive('builtins.set', is_unboxed=False, is_refcounted=True)  # type: Final

# At the C layer, str is refered to as unicode (PyUnicode)
str_rprimitive = RPrimitive('builtins.str', is_unboxed=False, is_refcounted=True)  # type: Final

# Tuple of an arbitrary length (corresponds to Tuple[t, ...], with explicit '...')
tuple_rprimitive = RPrimitive('builtins.tuple', is_unboxed=False,
                              is_refcounted=True)  # type: Final


def is_int_rprimitive(rtype: RType) -> bool:
    return rtype is int_rprimitive


def is_short_int_rprimitive(rtype: RType) -> bool:
    return rtype is short_int_rprimitive


def is_float_rprimitive(rtype: RType) -> bool:
    return isinstance(rtype, RPrimitive) and rtype.name == 'builtins.float'


def is_bool_rprimitive(rtype: RType) -> bool:
    return isinstance(rtype, RPrimitive) and rtype.name == 'builtins.bool'


def is_object_rprimitive(rtype: RType) -> bool:
    return isinstance(rtype, RPrimitive) and rtype.name == 'builtins.object'


def is_none_rprimitive(rtype: RType) -> bool:
    return isinstance(rtype, RPrimitive) and rtype.name == 'builtins.None'


def is_list_rprimitive(rtype: RType) -> bool:
    return isinstance(rtype, RPrimitive) and rtype.name == 'builtins.list'


def is_dict_rprimitive(rtype: RType) -> bool:
    return isinstance(rtype, RPrimitive) and rtype.name == 'builtins.dict'


def is_set_rprimitive(rtype: RType) -> bool:
    return isinstance(rtype, RPrimitive) and rtype.name == 'builtins.set'


def is_str_rprimitive(rtype: RType) -> bool:
    return isinstance(rtype, RPrimitive) and rtype.name == 'builtins.str'


def is_tuple_rprimitive(rtype: RType) -> bool:
    return isinstance(rtype, RPrimitive) and rtype.name == 'builtins.tuple'


class TupleNameVisitor(RTypeVisitor[str]):
    """Produce a tuple name based on the concrete representations of types."""

    def visit_rinstance(self, t: 'RInstance') -> str:
        return "O"

    def visit_runion(self, t: 'RUnion') -> str:
        return "O"

    def visit_rprimitive(self, t: 'RPrimitive') -> str:
        if t._ctype == 'CPyTagged':
            return 'I'
        elif t._ctype == 'char':
            return 'C'
        assert not t.is_unboxed, "{} unexpected unboxed type".format(t)
        return 'O'

    def visit_rtuple(self, t: 'RTuple') -> str:
        parts = [elem.accept(self) for elem in t.types]
        return 'T{}{}'.format(len(parts), ''.join(parts))

    def visit_rvoid(self, t: 'RVoid') -> str:
        assert False, "rvoid in tuple?"


class RTuple(RType):
    """Fixed-length unboxed tuple (represented as a C struct)."""

    is_unboxed = True

    def __init__(self, types: List[RType]) -> None:
        self.name = 'tuple'
        self.types = tuple(types)
        self.is_refcounted = any(t.is_refcounted for t in self.types)
        # Generate a unique id which is used in naming corresponding C identifiers.
        # This is necessary since C does not have anonymous structural type equivalence
        # in the same way python can just assign a Tuple[int, bool] to a Tuple[int, bool].
        self.unique_id = self.accept(TupleNameVisitor())
        # Nominally the max c length is 31 chars, but I'm not honestly worried about this.
        self.struct_name = 'tuple_{}'.format(self.unique_id)
        self._ctype = '{}'.format(self.struct_name)

    def accept(self, visitor: 'RTypeVisitor[T]') -> T:
        return visitor.visit_rtuple(self)

    def __str__(self) -> str:
        return 'tuple[%s]' % ', '.join(str(typ) for typ in self.types)

    def __repr__(self) -> str:
        return '<RTuple %s>' % ', '.join(repr(typ) for typ in self.types)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RTuple) and self.types == other.types

    def __hash__(self) -> int:
        return hash((self.name, self.types))

    def serialize(self) -> JsonDict:
        types = [x.serialize() for x in self.types]
        return {'.class': 'RTuple', 'types': types}

    @classmethod
    def deserialize(cls, data: JsonDict, ctx: DeserMaps) -> 'RTuple':
        types = [deserialize_type(t, ctx) for t in data['types']]
        return RTuple(types)


exc_rtuple = RTuple([object_rprimitive, object_rprimitive, object_rprimitive])


class RInstance(RType):
    """Instance of user-defined class (compiled to C extension class)."""

    is_unboxed = False

    def __init__(self, class_ir: 'ClassIR') -> None:
        # name is used for formatting the name in messages and debug output
        # so we want the fullname for precision.
        self.name = class_ir.fullname
        self.class_ir = class_ir
        self._ctype = 'PyObject *'

    def accept(self, visitor: 'RTypeVisitor[T]') -> T:
        return visitor.visit_rinstance(self)

    def struct_name(self, names: NameGenerator) -> str:
        return self.class_ir.struct_name(names)

    def getter_index(self, name: str) -> int:
        return self.class_ir.vtable_entry(name)

    def setter_index(self, name: str) -> int:
        return self.getter_index(name) + 1

    def method_index(self, name: str) -> int:
        return self.class_ir.vtable_entry(name)

    def attr_type(self, name: str) -> RType:
        return self.class_ir.attr_type(name)

    def __repr__(self) -> str:
        return '<RInstance %s>' % self.name

    def serialize(self) -> str:
        return self.name


class RUnion(RType):
    """union[x, ..., y]"""

    is_unboxed = False

    def __init__(self, items: List[RType]) -> None:
        self.name = 'union'
        self.items = items
        self.items_set = frozenset(items)
        self._ctype = 'PyObject *'

    def accept(self, visitor: 'RTypeVisitor[T]') -> T:
        return visitor.visit_runion(self)

    def __repr__(self) -> str:
        return '<RUnion %s>' % ', '.join(str(item) for item in self.items)

    def __str__(self) -> str:
        return 'union[%s]' % ', '.join(str(item) for item in self.items)

    # We compare based on the set because order in a union doesn't matter
    def __eq__(self, other: object) -> bool:
        return isinstance(other, RUnion) and self.items_set == other.items_set

    def __hash__(self) -> int:
        return hash(('union', self.items_set))

    def serialize(self) -> JsonDict:
        types = [x.serialize() for x in self.items]
        return {'.class': 'RUnion', 'types': types}

    @classmethod
    def deserialize(cls, data: JsonDict, ctx: DeserMaps) -> 'RUnion':
        types = [deserialize_type(t, ctx) for t in data['types']]
        return RUnion(types)


def optional_value_type(rtype: RType) -> Optional[RType]:
    if isinstance(rtype, RUnion) and len(rtype.items) == 2:
        if rtype.items[0] == none_rprimitive:
            return rtype.items[1]
        elif rtype.items[1] == none_rprimitive:
            return rtype.items[0]
    return None


def is_optional_type(rtype: RType) -> bool:
    return optional_value_type(rtype) is not None


class AssignmentTarget(object):
    type = None  # type: RType

    @abstractmethod
    def to_str(self, env: 'Environment') -> str:
        raise NotImplementedError


class AssignmentTargetRegister(AssignmentTarget):
    """Register as assignment target"""

    def __init__(self, register: 'Register') -> None:
        self.register = register
        self.type = register.type

    def to_str(self, env: 'Environment') -> str:
        return self.register.name


class AssignmentTargetIndex(AssignmentTarget):
    """base[index] as assignment target"""

    def __init__(self, base: 'Value', index: 'Value') -> None:
        self.base = base
        self.index = index
        # TODO: This won't be right for user-defined classes. Store the
        #       lvalue type in mypy and remove this special case.
        self.type = object_rprimitive

    def to_str(self, env: 'Environment') -> str:
        return '{}[{}]'.format(self.base.name, self.index.name)


class AssignmentTargetAttr(AssignmentTarget):
    """obj.attr as assignment target"""

    def __init__(self, obj: 'Value', attr: str) -> None:
        self.obj = obj
        self.attr = attr
        if isinstance(obj.type, RInstance) and obj.type.class_ir.has_attr(attr):
            self.obj_type = obj.type  # type: RType
            self.type = obj.type.attr_type(attr)
        else:
            self.obj_type = object_rprimitive
            self.type = object_rprimitive

    def to_str(self, env: 'Environment') -> str:
        return '{}.{}'.format(self.obj.to_str(env), self.attr)


class AssignmentTargetTuple(AssignmentTarget):
    """x, ..., y as assignment target"""

    def __init__(self, items: List[AssignmentTarget],
                 star_idx: Optional[int] = None) -> None:
        self.items = items
        self.star_idx = star_idx
        # The shouldn't be relevant, but provide it just in case.
        self.type = object_rprimitive

    def to_str(self, env: 'Environment') -> str:
        return '({})'.format(', '.join(item.to_str(env) for item in self.items))


class Environment:
    """Maintain the register symbol table and manage temp generation"""

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name
        self.indexes = OrderedDict()  # type: Dict[Value, int]
        self.symtable = OrderedDict()  # type: OrderedDict[SymbolNode, AssignmentTarget]
        self.temp_index = 0
        self.names = {}  # type: Dict[str, int]
        self.vars_needing_init = set()  # type: Set[Value]

    def regs(self) -> Iterable['Value']:
        return self.indexes.keys()

    def add(self, reg: 'Value', name: str) -> None:
        # Ensure uniqueness of variable names in this environment.
        # This is needed for things like list comprehensions, which are their own scope--
        # if we don't do this and two comprehensions use the same variable, we'd try to
        # declare that variable twice.
        unique_name = name
        while unique_name in self.names:
            unique_name = name + str(self.names[name])
            self.names[name] += 1
        self.names[unique_name] = 0
        reg.name = unique_name

        self.indexes[reg] = len(self.indexes)

    def add_local(self, symbol: SymbolNode, typ: RType, is_arg: bool = False) -> 'Register':
        assert isinstance(symbol, SymbolNode)
        reg = Register(typ, symbol.line, is_arg=is_arg)
        self.symtable[symbol] = AssignmentTargetRegister(reg)
        self.add(reg, symbol.name)
        return reg

    def add_local_reg(self, symbol: SymbolNode,
                      typ: RType, is_arg: bool = False) -> AssignmentTargetRegister:
        self.add_local(symbol, typ, is_arg)
        target = self.symtable[symbol]
        assert isinstance(target, AssignmentTargetRegister)
        return target

    def add_target(self, symbol: SymbolNode, target: AssignmentTarget) -> AssignmentTarget:
        self.symtable[symbol] = target
        return target

    def lookup(self, symbol: SymbolNode) -> AssignmentTarget:
        return self.symtable[symbol]

    def add_temp(self, typ: RType, is_arg: bool = False) -> 'Register':
        assert isinstance(typ, RType)
        reg = Register(typ, is_arg=is_arg)
        self.add(reg, 'r%d' % self.temp_index)
        self.temp_index += 1
        return reg

    def add_op(self, reg: 'RegisterOp') -> None:
        if reg.is_void:
            return
        self.add(reg, 'r%d' % self.temp_index)
        self.temp_index += 1

    def format(self, fmt: str, *args: Any) -> str:
        result = []
        i = 0
        arglist = list(args)
        while i < len(fmt):
            n = fmt.find('%', i)
            if n < 0:
                n = len(fmt)
            result.append(fmt[i:n])
            if n < len(fmt):
                typespec = fmt[n + 1]
                arg = arglist.pop(0)
                if typespec == 'r':
                    result.append(arg.name)
                elif typespec == 'd':
                    result.append('%d' % arg)
                elif typespec == 'f':
                    result.append('%f' % arg)
                elif typespec == 'l':
                    if isinstance(arg, BasicBlock):
                        arg = arg.label
                    result.append('L%s' % arg)
                elif typespec == 's':
                    result.append(str(arg))
                else:
                    raise ValueError('Invalid format sequence %{}'.format(typespec))
                i = n + 2
            else:
                i = n
        return ''.join(result)

    def to_lines(self) -> List[str]:
        result = []
        i = 0
        regs = list(self.regs())

        while i < len(regs):
            i0 = i
            group = [regs[i0].name]
            while i + 1 < len(regs) and regs[i + 1].type == regs[i0].type:
                i += 1
                group.append(regs[i].name)
            i += 1
            result.append('%s :: %s' % (', '.join(group), regs[i0].type))
        return result


class BasicBlock:
    """Basic IR block.

    Ends with a jump, branch, or return.

    When building the IR, ops that raise exceptions can be included in
    the middle of a basic block, but the exceptions aren't checked.
    Afterwards we perform a transform that inserts explicit checks for
    all error conditions and splits basic blocks accordingly to preserve
    the invariant that a jump, branch or return can only ever appear
    as the final op in a block. Manually inserting error checking ops
    would be boring and error-prone.

    BasicBlocks have an error_handler attribute that determines where
    to jump if an error occurs. If none is specified, an error will
    propagate up out of the function. This is compiled away by the
    `exceptions` module.

    Block labels are used for pretty printing and emitting C code, and get
    filled in by those passes.

    Ops that may terminate the program aren't treated as exits.
    """

    def __init__(self, label: int = -1) -> None:
        self.label = label
        self.ops = []  # type: List[Op]
        self.error_handler = None  # type: Optional[BasicBlock]

    @property
    def terminated(self) -> bool:
        return bool(self.ops) and isinstance(self.ops[-1], ControlOp)


# Never generates an exception
ERR_NEVER = 0  # type: Final
# Generates magic value (c_error_value) based on target RType on exception
ERR_MAGIC = 1  # type: Final
# Generates false (bool) on exception
ERR_FALSE = 2  # type: Final

# Hack: using this line number for an op will supress it in tracebacks
NO_TRACEBACK_LINE_NO = -10000


class Value:
    # Source line number
    line = -1
    name = '?'
    type = void_rtype  # type: RType
    is_borrowed = False

    def __init__(self, line: int) -> None:
        self.line = line

    @property
    def is_void(self) -> bool:
        return isinstance(self.type, RVoid)

    @abstractmethod
    def to_str(self, env: Environment) -> str:
        raise NotImplementedError


class Register(Value):
    def __init__(self, type: RType, line: int = -1, is_arg: bool = False, name: str = '') -> None:
        super().__init__(line)
        self.name = name
        self.type = type
        self.is_arg = is_arg
        self.is_borrowed = is_arg

    def to_str(self, env: Environment) -> str:
        return self.name

    @property
    def is_void(self) -> bool:
        return False


class Op(Value):
    def __init__(self, line: int) -> None:
        super().__init__(line)

    def can_raise(self) -> bool:
        # Override this is if Op may raise an exception. Note that currently the fact that
        # only RegisterOps may raise an exception in hard coded in some places.
        return False

    @abstractmethod
    def sources(self) -> List[Value]:
        pass

    def stolen(self) -> List[Value]:
        """Return arguments that have a reference count stolen by this op"""
        return []

    def unique_sources(self) -> List[Value]:
        result = []  # type: List[Value]
        for reg in self.sources():
            if reg not in result:
                result.append(reg)
        return result

    @abstractmethod
    def accept(self, visitor: 'OpVisitor[T]') -> T:
        pass


class ControlOp(Op):
    # Basically just for hierarchy organization.
    # We could plausibly have a targets() method if we wanted.
    pass


class Goto(ControlOp):
    """Unconditional jump."""

    error_kind = ERR_NEVER

    def __init__(self, label: BasicBlock, line: int = -1) -> None:
        super().__init__(line)
        self.label = label

    def __repr__(self) -> str:
        return '<Goto %s>' % self.label.label

    def sources(self) -> List[Value]:
        return []

    def to_str(self, env: Environment) -> str:
        return env.format('goto %l', self.label)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_goto(self)


class Branch(ControlOp):
    """if [not] r1 goto 1 else goto 2"""

    # Branch ops must *not* raise an exception. If a comparison, for example, can raise an
    # exception, it needs to split into two opcodes and only the first one may fail.
    error_kind = ERR_NEVER

    BOOL_EXPR = 100  # type: Final
    IS_ERROR = 101  # type: Final

    op_names = {
        BOOL_EXPR: ('%r', 'bool'),
        IS_ERROR: ('is_error(%r)', ''),
    }  # type: Final

    def __init__(self, left: Value, true_label: BasicBlock,
                 false_label: BasicBlock, op: int, line: int = -1, *, rare: bool = False) -> None:
        super().__init__(line)
        self.left = left
        self.true = true_label
        self.false = false_label
        self.op = op
        self.negated = False
        # If not None, the true label should generate a traceback entry (func name, line number)
        self.traceback_entry = None  # type: Optional[Tuple[str, int]]
        self.rare = rare

    def sources(self) -> List[Value]:
        return [self.left]

    def to_str(self, env: Environment) -> str:
        fmt, typ = self.op_names[self.op]
        if self.negated:
            fmt = 'not {}'.format(fmt)

        cond = env.format(fmt, self.left)
        tb = ''
        if self.traceback_entry:
            tb = ' (error at %s:%d)' % self.traceback_entry
        fmt = 'if {} goto %l{} else goto %l'.format(cond, tb)
        if typ:
            fmt += ' :: {}'.format(typ)
        return env.format(fmt, self.true, self.false)

    def invert(self) -> None:
        self.negated = not self.negated

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_branch(self)


class Return(ControlOp):
    error_kind = ERR_NEVER

    def __init__(self, reg: Value, line: int = -1) -> None:
        super().__init__(line)
        self.reg = reg

    def sources(self) -> List[Value]:
        return [self.reg]

    def stolen(self) -> List[Value]:
        return [self.reg]

    def to_str(self, env: Environment) -> str:
        return env.format('return %r', self.reg)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_return(self)


class Unreachable(ControlOp):
    """Added to the end of non-None returning functions.

    Mypy statically guarantees that the end of the function is not unreachable
    if there is not a return statement.

    This prevents the block formatter from being confused due to lack of a leave
    and also leaves a nifty note in the IR. It is not generally processed by visitors.
    """

    error_kind = ERR_NEVER

    def __init__(self, line: int = -1) -> None:
        super().__init__(line)

    def to_str(self, env: Environment) -> str:
        return "unreachable"

    def sources(self) -> List[Value]:
        return []

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_unreachable(self)


class RegisterOp(Op):
    """An operation that can be written as r1 = f(r2, ..., rn).

    Takes some registers, performs an operation and generates an output.
    Doesn't do any control flow, but can raise an error.
    """

    error_kind = -1  # Can this raise exception and how is it signalled; one of ERR_*

    _type = None  # type: Optional[RType]

    def __init__(self, line: int) -> None:
        super().__init__(line)
        assert self.error_kind != -1, 'error_kind not defined'

    def can_raise(self) -> bool:
        return self.error_kind != ERR_NEVER


class IncRef(RegisterOp):
    """inc_ref r"""

    error_kind = ERR_NEVER

    def __init__(self, src: Value, line: int = -1) -> None:
        assert src.type.is_refcounted
        super().__init__(line)
        self.src = src

    def to_str(self, env: Environment) -> str:
        s = env.format('inc_ref %r', self.src)
        if is_bool_rprimitive(self.src.type) or is_int_rprimitive(self.src.type):
            s += ' :: {}'.format(short_name(self.src.type.name))
        return s

    def sources(self) -> List[Value]:
        return [self.src]

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_inc_ref(self)


class DecRef(RegisterOp):
    """dec_ref r

    The is_xdec flag says to use an XDECREF, which checks if the
    pointer is NULL first.
    """

    error_kind = ERR_NEVER

    def __init__(self, src: Value, is_xdec: bool = False, line: int = -1) -> None:
        assert src.type.is_refcounted
        super().__init__(line)
        self.src = src
        self.is_xdec = is_xdec

    def __repr__(self) -> str:
        return '<%sDecRef %r>' % ('X' if self.is_xdec else '', self.src)

    def to_str(self, env: Environment) -> str:
        s = env.format('%sdec_ref %r', 'x' if self.is_xdec else '', self.src)
        if is_bool_rprimitive(self.src.type) or is_int_rprimitive(self.src.type):
            s += ' :: {}'.format(short_name(self.src.type.name))
        return s

    def sources(self) -> List[Value]:
        return [self.src]

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_dec_ref(self)


class Call(RegisterOp):
    """Native call f(arg, ...)

    The call target can be a module-level function or a class.
    """

    error_kind = ERR_MAGIC

    def __init__(self, fn: 'FuncDecl', args: Sequence[Value], line: int) -> None:
        super().__init__(line)
        self.fn = fn
        self.args = list(args)
        self.type = fn.sig.ret_type

    def to_str(self, env: Environment) -> str:
        args = ', '.join(env.format('%r', arg) for arg in self.args)
        # TODO: Display long name?
        short_name = self.fn.shortname
        s = '%s(%s)' % (short_name, args)
        if not self.is_void:
            s = env.format('%r = ', self) + s
        return s

    def sources(self) -> List[Value]:
        return list(self.args[:])

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_call(self)


class MethodCall(RegisterOp):
    """Native method call obj.m(arg, ...) """

    error_kind = ERR_MAGIC

    def __init__(self,
                 obj: Value,
                 method: str,
                 args: List[Value],
                 line: int = -1) -> None:
        super().__init__(line)
        self.obj = obj
        self.method = method
        self.args = args
        assert isinstance(obj.type, RInstance), "Methods can only be called on instances"
        self.receiver_type = obj.type
        method_ir = self.receiver_type.class_ir.method_sig(method)
        assert method_ir is not None, "{} doesn't have method {}".format(
            self.receiver_type.name, method)
        self.type = method_ir.ret_type

    def to_str(self, env: Environment) -> str:
        args = ', '.join(env.format('%r', arg) for arg in self.args)
        s = env.format('%r.%s(%s)', self.obj, self.method, args)
        if not self.is_void:
            s = env.format('%r = ', self) + s
        return s

    def sources(self) -> List[Value]:
        return self.args[:] + [self.obj]

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_method_call(self)


@trait
class EmitterInterface():
    @abstractmethod
    def reg(self, name: Value) -> str:
        raise NotImplementedError

    @abstractmethod
    def c_error_value(self, rtype: RType) -> str:
        raise NotImplementedError

    @abstractmethod
    def temp_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def emit_line(self, line: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def emit_lines(self, *lines: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def emit_declaration(self, line: str) -> None:
        raise NotImplementedError


EmitCallback = Callable[[EmitterInterface, List[str], str], None]

# True steals all arguments, False steals none, a list steals those in matching positions
StealsDescription = Union[bool, List[bool]]

OpDescription = NamedTuple(
    'OpDescription', [('name', str),
                      ('arg_types', List[RType]),
                      ('result_type', Optional[RType]),
                      ('is_var_arg', bool),
                      ('error_kind', int),
                      ('format_str', str),
                      ('emit', EmitCallback),
                      ('steals', StealsDescription),
                      ('is_borrowed', bool),
                      ('priority', int)])  # To resolve ambiguities, highest priority wins


class PrimitiveOp(RegisterOp):
    """reg = op(reg, ...)

    These are register-based primitive operations that work on specific
    operand types.

    The details of the operation are defined by the 'desc'
    attribute. The modules under mypyc.primitives define the supported
    operations. mypyc.irbuild uses the descriptions to look for suitable
    primitive ops.
    """

    def __init__(self,
                 args: List[Value],
                 desc: OpDescription,
                 line: int) -> None:
        if not desc.is_var_arg:
            assert len(args) == len(desc.arg_types)
        self.error_kind = desc.error_kind
        super().__init__(line)
        self.args = args
        self.desc = desc
        if desc.result_type is None:
            assert desc.error_kind == ERR_FALSE  # TODO: No-value ops not supported yet
            self.type = bool_rprimitive
        else:
            self.type = desc.result_type

        self.is_borrowed = desc.is_borrowed

    def sources(self) -> List[Value]:
        return list(self.args)

    def stolen(self) -> List[Value]:
        if isinstance(self.desc.steals, list):
            assert len(self.desc.steals) == len(self.args)
            return [arg for arg, steal in zip(self.args, self.desc.steals) if steal]
        else:
            return [] if not self.desc.steals else self.sources()

    def __repr__(self) -> str:
        return '<PrimitiveOp name=%r args=%s>' % (self.desc.name,
                                                  self.args)

    def to_str(self, env: Environment) -> str:
        params = {}  # type: Dict[str, Any]
        if not self.is_void:
            params['dest'] = env.format('%r', self)
        args = [env.format('%r', arg) for arg in self.args]
        params['args'] = args
        params['comma_args'] = ', '.join(args)
        params['colon_args'] = ', '.join(
            '{}: {}'.format(k, v) for k, v in zip(args[::2], args[1::2])
        )
        return self.desc.format_str.format(**params).strip()

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_primitive_op(self)


class Assign(Op):
    """dest = int"""

    error_kind = ERR_NEVER

    def __init__(self, dest: Register, src: Value, line: int = -1) -> None:
        super().__init__(line)
        self.src = src
        self.dest = dest

    def sources(self) -> List[Value]:
        return [self.src]

    def stolen(self) -> List[Value]:
        return [self.src]

    def to_str(self, env: Environment) -> str:
        return env.format('%r = %r', self.dest, self.src)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_assign(self)


class LoadInt(RegisterOp):
    """dest = int"""

    error_kind = ERR_NEVER

    def __init__(self, value: int, line: int = -1) -> None:
        super().__init__(line)
        self.value = value
        self.type = short_int_rprimitive

    def sources(self) -> List[Value]:
        return []

    def to_str(self, env: Environment) -> str:
        return env.format('%r = %d', self, self.value)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_load_int(self)


class LoadErrorValue(RegisterOp):
    """dest = <error value for type>"""

    error_kind = ERR_NEVER

    def __init__(self, rtype: RType, line: int = -1,
                 is_borrowed: bool = False,
                 undefines: bool = False) -> None:
        super().__init__(line)
        self.type = rtype
        self.is_borrowed = is_borrowed
        # Undefines is true if this should viewed by the definedness
        # analysis pass as making the register it is assigned to
        # undefined (and thus checks should be added on uses).
        self.undefines = undefines

    def sources(self) -> List[Value]:
        return []

    def to_str(self, env: Environment) -> str:
        return env.format('%r = <error> :: %s', self, self.type)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_load_error_value(self)


class GetAttr(RegisterOp):
    """dest = obj.attr (for a native object)"""

    error_kind = ERR_MAGIC

    def __init__(self, obj: Value, attr: str, line: int) -> None:
        super().__init__(line)
        self.obj = obj
        self.attr = attr
        assert isinstance(obj.type, RInstance), 'Attribute access not supported: %s' % obj.type
        self.class_type = obj.type
        self.type = obj.type.attr_type(attr)

    def sources(self) -> List[Value]:
        return [self.obj]

    def to_str(self, env: Environment) -> str:
        return env.format('%r = %r.%s', self, self.obj, self.attr)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_get_attr(self)


class SetAttr(RegisterOp):
    """obj.attr = src (for a native object)

    Steals the reference to src.
    """

    error_kind = ERR_FALSE

    def __init__(self, obj: Value, attr: str, src: Value, line: int) -> None:
        super().__init__(line)
        self.obj = obj
        self.attr = attr
        self.src = src
        assert isinstance(obj.type, RInstance), 'Attribute access not supported: %s' % obj.type
        self.class_type = obj.type
        self.type = bool_rprimitive

    def sources(self) -> List[Value]:
        return [self.obj, self.src]

    def stolen(self) -> List[Value]:
        return [self.src]

    def to_str(self, env: Environment) -> str:
        return env.format('%r.%s = %r; %r = is_error', self.obj, self.attr, self.src, self)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_set_attr(self)


NAMESPACE_STATIC = 'static'  # type: Final # Default name space for statics, variables
NAMESPACE_TYPE = 'type'  # type: Final # Static namespace for pointers to native type objects
NAMESPACE_MODULE = 'module'  # type: Final # Namespace for modules


class LoadStatic(RegisterOp):
    """dest = name :: static

    Load a C static variable/pointer. The namespace for statics is shared
    for the entire compilation group. You can optionally provide a module
    name and a sub-namespace identifier for additional namespacing to avoid
    name conflicts. The static namespace does not overlap with other C names,
    since the final C name will get a prefix, so conflicts only must be
    avoided with other statics.
    """

    error_kind = ERR_NEVER
    is_borrowed = True

    def __init__(self,
                 type: RType,
                 identifier: str,
                 module_name: Optional[str] = None,
                 namespace: str = NAMESPACE_STATIC,
                 line: int = -1,
                 ann: object = None) -> None:
        super().__init__(line)
        self.identifier = identifier
        self.module_name = module_name
        self.namespace = namespace
        self.type = type
        self.ann = ann  # An object to pretty print with the load

    def sources(self) -> List[Value]:
        return []

    def to_str(self, env: Environment) -> str:
        ann = '  ({})'.format(repr(self.ann)) if self.ann else ''
        name = self.identifier
        if self.module_name is not None:
            name = '{}.{}'.format(self.module_name, name)
        return env.format('%r = %s :: %s%s', self, name, self.namespace, ann)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_load_static(self)


class InitStatic(RegisterOp):
    """static = value :: static

    Initialize a C static variable/pointer. See everything in LoadStatic.
    """

    error_kind = ERR_NEVER

    def __init__(self,
                 value: Value,
                 identifier: str,
                 module_name: Optional[str] = None,
                 namespace: str = NAMESPACE_STATIC,
                 line: int = -1) -> None:
        super().__init__(line)
        self.identifier = identifier
        self.module_name = module_name
        self.namespace = namespace
        self.value = value

    def sources(self) -> List[Value]:
        return [self.value]

    def to_str(self, env: Environment) -> str:
        name = self.identifier
        if self.module_name is not None:
            name = '{}.{}'.format(self.module_name, name)
        return env.format('%s = %r :: %s', name, self.value, self.namespace)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_init_static(self)


class TupleSet(RegisterOp):
    """dest = (reg, ...) (for fixed-length tuple)"""

    error_kind = ERR_NEVER

    def __init__(self, items: List[Value], line: int) -> None:
        super().__init__(line)
        self.items = items
        # Don't keep track of the fact that an int is short after it
        # is put into a tuple, since we don't properly implement
        # runtime subtyping for tuples.
        self.tuple_type = RTuple(
            [arg.type if not is_short_int_rprimitive(arg.type) else int_rprimitive
             for arg in items])
        self.type = self.tuple_type

    def sources(self) -> List[Value]:
        return self.items[:]

    def to_str(self, env: Environment) -> str:
        item_str = ', '.join(env.format('%r', item) for item in self.items)
        return env.format('%r = (%s)', self, item_str)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_tuple_set(self)


class TupleGet(RegisterOp):
    """dest = src[n] (for fixed-length tuple)"""

    error_kind = ERR_NEVER

    def __init__(self, src: Value, index: int, line: int) -> None:
        super().__init__(line)
        self.src = src
        self.index = index
        assert isinstance(src.type, RTuple), "TupleGet only operates on tuples"
        self.type = src.type.types[index]

    def sources(self) -> List[Value]:
        return [self.src]

    def to_str(self, env: Environment) -> str:
        return env.format('%r = %r[%d]', self, self.src, self.index)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_tuple_get(self)


class Cast(RegisterOp):
    """dest = cast(type, src)

    Perform a runtime type check (no representation or value conversion).

    DO NOT increment reference counts.
    """

    error_kind = ERR_MAGIC

    def __init__(self, src: Value, typ: RType, line: int) -> None:
        super().__init__(line)
        self.src = src
        self.type = typ

    def sources(self) -> List[Value]:
        return [self.src]

    def stolen(self) -> List[Value]:
        return [self.src]

    def to_str(self, env: Environment) -> str:
        return env.format('%r = cast(%s, %r)', self, self.type, self.src)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_cast(self)


class Box(RegisterOp):
    """dest = box(type, src)

    This converts from a potentially unboxed representation to a straight Python object.
    Only supported for types with an unboxed representation.
    """

    error_kind = ERR_NEVER

    def __init__(self, src: Value, line: int = -1) -> None:
        super().__init__(line)
        self.src = src
        self.type = object_rprimitive
        # When we box None and bool values, we produce a borrowed result
        if is_none_rprimitive(self.src.type) or is_bool_rprimitive(self.src.type):
            self.is_borrowed = True

    def sources(self) -> List[Value]:
        return [self.src]

    def stolen(self) -> List[Value]:
        return [self.src]

    def to_str(self, env: Environment) -> str:
        return env.format('%r = box(%s, %r)', self, self.src.type, self.src)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_box(self)


class Unbox(RegisterOp):
    """dest = unbox(type, src)

    This is similar to a cast, but it also changes to a (potentially) unboxed runtime
    representation. Only supported for types with an unboxed representation.
    """

    error_kind = ERR_MAGIC

    def __init__(self, src: Value, typ: RType, line: int) -> None:
        super().__init__(line)
        self.src = src
        self.type = typ

    def sources(self) -> List[Value]:
        return [self.src]

    def to_str(self, env: Environment) -> str:
        return env.format('%r = unbox(%s, %r)', self, self.type, self.src)

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_unbox(self)


class RaiseStandardError(RegisterOp):
    """Raise built-in exception with an optional error string.

    We have a separate opcode for this for convenience and to
    generate smaller, more idiomatic C code.
    """

    # TODO: Make it more explicit at IR level that this always raises

    error_kind = ERR_FALSE

    VALUE_ERROR = 'ValueError'  # type: Final
    ASSERTION_ERROR = 'AssertionError'  # type: Final
    STOP_ITERATION = 'StopIteration'  # type: Final
    UNBOUND_LOCAL_ERROR = 'UnboundLocalError'  # type: Final
    RUNTIME_ERROR = 'RuntimeError'  # type: Final

    def __init__(self, class_name: str, value: Optional[Union[str, Value]], line: int) -> None:
        super().__init__(line)
        self.class_name = class_name
        self.value = value
        self.type = bool_rprimitive

    def to_str(self, env: Environment) -> str:
        if self.value is not None:
            if isinstance(self.value, str):
                return 'raise %s(%r)' % (self.class_name, self.value)
            elif isinstance(self.value, Value):
                return env.format('raise %s(%r)', self.class_name, self.value)
            else:
                assert False, 'value type must be either str or Value'
        else:
            return 'raise %s' % self.class_name

    def sources(self) -> List[Value]:
        return []

    def accept(self, visitor: 'OpVisitor[T]') -> T:
        return visitor.visit_raise_standard_error(self)


class RuntimeArg:
    def __init__(self, name: str, typ: RType, kind: int = ARG_POS) -> None:
        self.name = name
        self.type = typ
        self.kind = kind

    @property
    def optional(self) -> bool:
        return self.kind == ARG_OPT or self.kind == ARG_NAMED_OPT

    def __repr__(self) -> str:
        return 'RuntimeArg(name=%s, type=%s, optional=%r)' % (self.name, self.type, self.optional)

    def serialize(self) -> JsonDict:
        return {'name': self.name, 'type': self.type.serialize(), 'kind': self.kind}

    @classmethod
    def deserialize(cls, data: JsonDict, ctx: DeserMaps) -> 'RuntimeArg':
        return RuntimeArg(
            data['name'],
            deserialize_type(data['type'], ctx),
            data['kind'],
        )


class FuncSignature:
    # TODO: track if method?
    def __init__(self, args: Sequence[RuntimeArg], ret_type: RType) -> None:
        self.args = tuple(args)
        self.ret_type = ret_type

    def __repr__(self) -> str:
        return 'FuncSignature(args=%r, ret=%r)' % (self.args, self.ret_type)

    def serialize(self) -> JsonDict:
        return {'args': [t.serialize() for t in self.args], 'ret_type': self.ret_type.serialize()}

    @classmethod
    def deserialize(cls, data: JsonDict, ctx: DeserMaps) -> 'FuncSignature':
        return FuncSignature(
            [RuntimeArg.deserialize(arg, ctx) for arg in data['args']],
            deserialize_type(data['ret_type'], ctx),
        )


FUNC_NORMAL = 0  # type: Final
FUNC_STATICMETHOD = 1  # type: Final
FUNC_CLASSMETHOD = 2  # type: Final


class FuncDecl:
    def __init__(self,
                 name: str,
                 class_name: Optional[str],
                 module_name: str,
                 sig: FuncSignature,
                 kind: int = FUNC_NORMAL,
                 is_prop_setter: bool = False,
                 is_prop_getter: bool = False) -> None:
        self.name = name
        self.class_name = class_name
        self.module_name = module_name
        self.sig = sig
        self.kind = kind
        self.is_prop_setter = is_prop_setter
        self.is_prop_getter = is_prop_getter
        if class_name is None:
            self.bound_sig = None  # type: Optional[FuncSignature]
        else:
            if kind == FUNC_STATICMETHOD:
                self.bound_sig = sig
            else:
                self.bound_sig = FuncSignature(sig.args[1:], sig.ret_type)

    @staticmethod
    def compute_shortname(class_name: Optional[str], name: str) -> str:
        return class_name + '.' + name if class_name else name

    @property
    def shortname(self) -> str:
        return FuncDecl.compute_shortname(self.class_name, self.name)

    @property
    def fullname(self) -> str:
        return self.module_name + '.' + self.shortname

    def cname(self, names: NameGenerator) -> str:
        return names.private_name(self.module_name, self.shortname)

    def serialize(self) -> JsonDict:
        return {
            'name': self.name,
            'class_name': self.class_name,
            'module_name': self.module_name,
            'sig': self.sig.serialize(),
            'kind': self.kind,
            'is_prop_setter': self.is_prop_setter,
            'is_prop_getter': self.is_prop_getter,
        }

    @staticmethod
    def get_name_from_json(f: JsonDict) -> str:
        return f['module_name'] + '.' + FuncDecl.compute_shortname(f['class_name'], f['name'])

    @classmethod
    def deserialize(cls, data: JsonDict, ctx: DeserMaps) -> 'FuncDecl':
        return FuncDecl(
            data['name'],
            data['class_name'],
            data['module_name'],
            FuncSignature.deserialize(data['sig'], ctx),
            data['kind'],
            data['is_prop_setter'],
            data['is_prop_getter'],
        )


class FuncIR:
    """Intermediate representation of a function with contextual information."""

    def __init__(self,
                 decl: FuncDecl,
                 blocks: List[BasicBlock],
                 env: Environment,
                 line: int = -1,
                 traceback_name: Optional[str] = None) -> None:
        self.decl = decl
        self.blocks = blocks
        self.env = env
        self.line = line
        # The name that should be displayed for tracebacks that
        # include this function. Function will be omitted from
        # tracebacks if None.
        self.traceback_name = traceback_name

    @property
    def args(self) -> Sequence[RuntimeArg]:
        return self.decl.sig.args

    @property
    def ret_type(self) -> RType:
        return self.decl.sig.ret_type

    @property
    def class_name(self) -> Optional[str]:
        return self.decl.class_name

    @property
    def sig(self) -> FuncSignature:
        return self.decl.sig

    @property
    def name(self) -> str:
        return self.decl.name

    @property
    def fullname(self) -> str:
        return self.decl.fullname

    def cname(self, names: NameGenerator) -> str:
        return self.decl.cname(names)

    def __str__(self) -> str:
        return '\n'.join(format_func(self))

    def serialize(self) -> JsonDict:
        # We don't include blocks or env in the serialized version
        return {
            'decl': self.decl.serialize(),
            'line': self.line,
            'traceback_name': self.traceback_name,
        }

    @classmethod
    def deserialize(cls, data: JsonDict, ctx: DeserMaps) -> 'FuncIR':
        return FuncIR(
            FuncDecl.deserialize(data['decl'], ctx),
            [],
            Environment(),
            data['line'],
            data['traceback_name'],
        )


INVALID_FUNC_DEF = FuncDef('<INVALID_FUNC_DEF>', [], Block([]))  # type: Final


LiteralsMap = Dict[Tuple[Type[object], Union[int, float, str, bytes, complex]], str]


@trait
class OpVisitor(Generic[T]):
    @abstractmethod
    def visit_goto(self, op: Goto) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_branch(self, op: Branch) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_return(self, op: Return) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_unreachable(self, op: Unreachable) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_primitive_op(self, op: PrimitiveOp) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_assign(self, op: Assign) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_load_int(self, op: LoadInt) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_load_error_value(self, op: LoadErrorValue) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_get_attr(self, op: GetAttr) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_set_attr(self, op: SetAttr) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_load_static(self, op: LoadStatic) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_init_static(self, op: InitStatic) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_tuple_get(self, op: TupleGet) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_tuple_set(self, op: TupleSet) -> T:
        raise NotImplementedError

    def visit_inc_ref(self, op: IncRef) -> T:
        raise NotImplementedError

    def visit_dec_ref(self, op: DecRef) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_call(self, op: Call) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_method_call(self, op: MethodCall) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_cast(self, op: Cast) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_box(self, op: Box) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_unbox(self, op: Unbox) -> T:
        raise NotImplementedError

    @abstractmethod
    def visit_raise_standard_error(self, op: RaiseStandardError) -> T:
        raise NotImplementedError


def format_blocks(blocks: List[BasicBlock], env: Environment) -> List[str]:
    # First label all of the blocks
    for i, block in enumerate(blocks):
        block.label = i

    handler_map = {}  # type: Dict[BasicBlock, List[BasicBlock]]
    for b in blocks:
        if b.error_handler:
            handler_map.setdefault(b.error_handler, []).append(b)

    lines = []
    for i, block in enumerate(blocks):
        i == len(blocks) - 1

        handler_msg = ''
        if block in handler_map:
            labels = sorted(env.format('%l', b.label) for b in handler_map[block])
            handler_msg = ' (handler for {})'.format(', '.join(labels))

        lines.append(env.format('%l:%s', block.label, handler_msg))
        ops = block.ops
        if (isinstance(ops[-1], Goto) and i + 1 < len(blocks)
                and ops[-1].label == blocks[i + 1]):
            # Hide the last goto if it just goes to the next basic block.
            ops = ops[:-1]
        for op in ops:
            line = '    ' + op.to_str(env)
            lines.append(line)

        if not isinstance(block.ops[-1], (Goto, Branch, Return, Unreachable)):
            # Each basic block needs to exit somewhere.
            lines.append('    [MISSING BLOCK EXIT OPCODE]')
    return lines


def format_func(fn: FuncIR) -> List[str]:
    lines = []
    cls_prefix = fn.class_name + '.' if fn.class_name else ''
    lines.append('def {}{}({}):'.format(cls_prefix, fn.name,
                                        ', '.join(arg.name for arg in fn.args)))
    for line in fn.env.to_lines():
        lines.append('    ' + line)
    code = format_blocks(fn.blocks, fn.env)
    lines.extend(code)
    return lines


def short_name(name: str) -> str:
    if name.startswith('builtins.'):
        return name[9:]
    return name


# Import mypyc.primitives.registry that will set up set up global primitives tables.
import mypyc.primitives.registry  # noqa
