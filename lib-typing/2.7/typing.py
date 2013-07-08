u"""Static type checking helpers"""

from abc import ABCMeta, abstractmethod
import inspect
import sys
import re


__all__ = [
    # Type system related
    u'AbstractGeneric',
    u'AbstractGenericMeta',
    u'Any',
    u'BytesMatch',
    u'BytesPattern',
    u'Dict',
    u'Generic',
    u'GenericMeta',
    u'List',
    u'Match',
    u'Pattern',
    u'Protocol',
    u'Set',
    u'Tuple',
    u'Undefined',
    u'cast',
    u'forwardref',
    u'overload',
    u'typevar',
    # Protocols and abstract base classes
    u'Container',
    u'Iterable',
    u'Iterator',
    u'Sequence',
    u'Sized',
    u'AbstractSet',
    u'Mapping',
    u'IO',
    u'TextIO',
]


class GenericMeta(type):
    u"""Metaclass for generic classes that support indexing by types."""
    
    def __getitem__(self, args):
        # Just ignore args; they are for compile-time checks only.
        return self


class Generic():
    __metaclass__ = GenericMeta
    u"""Base class for generic classes."""


class AbstractGenericMeta(ABCMeta):
    u"""Metaclass for abstract generic classes that support type indexing.

    This is used for both protocols and ordinary abstract classes.
    """
    
    def __new__(mcls, name, bases, namespace):
        cls = super(mcls.__class__, mcls).__new__(mcls, name, bases, namespace)
        # 'Protocol' must be an explicit base class in order for a class to
        # be a protocol.
        cls._is_protocol = name == u'Protocol' or Protocol in bases
        return cls
    
    def __getitem__(self, args):
        # Just ignore args; they are for compile-time checks only.
        return self


class Protocol():
    __metaclass__ = AbstractGenericMeta
    u"""Base class for protocol classes."""

    @classmethod
    def __subclasshook__(cls, c):
        if not cls._is_protocol:
            # No structural checks since this isn't a protocol.
            return NotImplemented
        
        if cls is Protocol:
            # Every class is a subclass of the empty protocol.
            return True

        # Find all attributes defined in the protocol.
        attrs = cls._get_protocol_attrs()

        for attr in attrs:
            if not any(attr in d.__dict__ for d in c.__mro__):
                return NotImplemented
        return True

    @classmethod
    def _get_protocol_attrs(cls):
        # Get all Protocol base classes.
        protocol_bases = []
        for c in cls.__mro__:
            if getattr(c, u'_is_protocol', False) and c.__name__ != u'Protocol':
                protocol_bases.append(c)
        
        # Get attributes included in protocol.
        attrs = set()
        for base in protocol_bases:
            for attr in base.__dict__.keys():
                # Include attributes not defined in any non-protocol bases.
                for c in cls.__mro__:
                    if (c is not base and attr in c.__dict__ and
                            not getattr(c, u'_is_protocol', False)):
                        break
                else:
                    if (not attr.startswith(u'_abc_') and
                        attr != u'__abstractmethods__' and
                        attr != u'_is_protocol' and
                        attr != u'__dict__' and
                        attr != u'_get_protocol_attrs' and
                        attr != u'__module__'):
                        attrs.add(attr)
        
        return attrs


class AbstractGeneric():
    __metaclass__ = AbstractGenericMeta
    u"""Base class for abstract generic classes."""


class TypeAlias(object):
    u"""Class for defining generic aliases for library types."""
    
    def __init__(self, target_type):
        self.target_type = target_type
    
    def __getitem__(self, typeargs):
        return self.target_type


# Define aliases for built-in types that support indexing.
List = TypeAlias(list)
Dict = TypeAlias(dict)
Set = TypeAlias(set)
Tuple = TypeAlias(tuple)
Function = TypeAlias(callable)

# Give names to some built-in types.
Pattern = type(re.compile(u''))
BytesPattern = Pattern # TODO Pattern and BytesPattern shouldn't be the same!
Match = type(re.match(u'', u''))
BytesMatch = Match # TODO See above.


class typevar(object):
    def __init__(self, name):
        self.name = name


class forwardref(object):
    def __init__(self, name):
        self.name = name


def Any(x):
    u"""The Any type; can also be used to cast a value to type Any."""
    return x


def cast(type, object):
    u"""Cast a value to a type.

    This only affects static checking; simply return object at runtime.
    """
    return object


def overload(func):
    u"""Function decorator for defining overloaded functions."""
    frame = sys._getframe(1)
    locals = frame.f_locals
    # See if there is a previous overload variant available.  Also verify
    # that the existing function really is overloaded: otherwise, replace
    # the definition.  The latter is actually important if we want to reload
    # a library module such as genericpath with a custom one that uses
    # overloading in the implementation.
    if func.__name__ in locals and hasattr(locals[func.__name__], u'dispatch'):
        orig_func = locals[func.__name__]
        
        def wrapper(*args, **kwargs):
            ret, ok = orig_func.dispatch(*args, **kwargs)
            if ok:
                return ret
            return func(*args, **kwargs)
        wrapper.isoverload = True
        wrapper.dispatch = make_dispatcher(func, orig_func.dispatch)
        wrapper.next = orig_func
        wrapper.__name__ = func.__name__
        if hasattr(func, u'__isabstractmethod__'):
            # Note that we can't reliably check that abstractmethod is
            # used consistently across overload variants, so we let a
            # static checker do it.
            wrapper.__isabstractmethod__ = func.__isabstractmethod__
        return wrapper
    else:
        # Return the initial overload variant.
        func.isoverload = True
        func.dispatch = make_dispatcher(func)
        func.next = None
        return func


def is_erased_type(t):
    return t is Any or isinstance(t, typevar)


def make_dispatcher(func, previous=None):
    u"""Create argument dispatcher for an overloaded function.

    Also handle chaining of multiple overload variants.
    """
    (args, varargs, varkw, defaults,
     kwonlyargs, kwonlydefaults, annotations) = inspect.getargspec(func)
    
    argtypes = []
    for arg in args:
        ann = annotations.get(arg)
        if isinstance(ann, forwardref):
            ann = ann.name
        if is_erased_type(ann):
            ann = None
        elif isinstance(ann, unicode):
            # The annotation is a string => evaluate it lazily when the
            # overloaded function is first called.
            frame = sys._getframe(2)
            t = [None]
            ann_str = ann
            def check(x):
                if not t[0]:
                    # Evaluate string in the context of the overload caller.
                    t[0] = eval(ann_str, frame.f_globals, frame.f_locals)
                    if is_erased_type(t[0]):
                        # Anything goes.
                        t[0] = object
                if isinstance(t[0], type):
                    return isinstance(x, t[0])
                else:
                    return t[0](x)
            ann = check
        argtypes.append(ann)

    maxargs = len(argtypes)
    minargs = maxargs
    if defaults:
        minargs = len(argtypes) - len(defaults)
    
    def dispatch(*args, **kwargs):
        if previous:
            ret, ok = previous(*args, **kwargs)
            if ok:
                return ret, ok

        nargs = len(args)
        if nargs < minargs or nargs > maxargs:
            # Invalid argument count.
            return None, False
        
        for i in xrange(nargs):
            argtype = argtypes[i]
            if argtype:
                if isinstance(argtype, type):
                    if not isinstance(args[i], argtype):
                        break
                else:
                    if not argtype(args[i]):
                        break
        else:
            return func(*args, **kwargs), True
        return None, False
    return dispatch


class Undefined(object):
    u"""Class that represents an undefined value with a specified type.

    At runtime the name Undefined is bound to an instance of this
    class.  The intent is that any operation on an Undefined object
    raises an exception, including use in a boolean context.  Some
    operations cannot be disallowed: Undefined can be used as an
    operand of 'is', and it can be assigned to variables and stored in
    containers.

    'Undefined' makes it possible to declare the static type of a
    variable even if there is no useful default value to initialize it
    with:

      from typing import Undefined
      x = Undefined(int)
      y = Undefined # type: int

    The latter form can be used if efficiency is of utmost importance,
    since it saves a call operation and potentially additional
    operations needed to evaluate a type expression.  Undefined(x)
    just evaluates to Undefined, ignoring the argument value.
    """
    
    def __repr__(self):
        return u'<typing.Undefined>'

    def __setattr__(self, attr, value):
        raise AttributeError(u"'Undefined' object has no attribute '%s'" % attr)

    def __eq__(self, other):
        raise TypeError(u"'Undefined' object cannot be compared")

    def __call__(self, type):
        return self

    def __nonzero__(self):
        raise TypeError(u"'Undefined' object is not valid as a boolean")


Undefined = Undefined()


# Abstract classes


T = typevar(u'T')
KT = typevar(u'KT')
VT = typevar(u'VT')


class SupportsInt(Protocol):
    @abstractmethod
    def __int__(self): pass


class SupportsFloat(Protocol):
    @abstractmethod
    def __float__(self): pass


class SupportsAbs(Protocol[T]):
    @abstractmethod
    def __abs__(self): pass


class SupportsRound(Protocol[T]):
    @abstractmethod
    def __round__(self, ndigits = 0): pass


class Reversible(Protocol[T]):
    @abstractmethod
    def __reversed__(self): pass


class Sized(Protocol):
    @abstractmethod
    def __len__(self): pass


class Container(Protocol[T]):
    @abstractmethod
    def __contains__(self, x): pass


class Iterable(Protocol[T]):
    @abstractmethod
    def __iter__(self): pass


class Iterator(Iterable[T], Protocol[T]):
    @abstractmethod
    def __next__(self): pass


class Sequence(Sized, Iterable[T], Container[T], AbstractGeneric[T]):
    @abstractmethod
    @overload
    def __getitem__(self, i): pass
    
    @abstractmethod
    @overload
    def __getitem__(self, s): pass
    
    @abstractmethod
    def __reversed__(self, s): pass
    
    @abstractmethod
    def index(self, x): pass
    
    @abstractmethod
    def count(self, x): pass


for t in list, tuple, unicode, str, range:
    Sequence.register(t)


class AbstractSet(Sized, Iterable[T], AbstractGeneric[T]):
    @abstractmethod
    def __contains__(self, x): pass
    @abstractmethod
    def __and__(self, s): pass
    @abstractmethod
    def __or__(self, s): pass
    @abstractmethod
    def __sub__(self, s): pass
    @abstractmethod
    def __xor__(self, s): pass
    @abstractmethod
    def isdisjoint(self, s): pass


for t in set, frozenset, type({}.keys()), type({}.items()):
    AbstractSet.register(t)


class Mapping(Sized, Iterable[KT], AbstractGeneric[KT, VT]):
    @abstractmethod
    def __getitem__(self, k): pass
    @abstractmethod
    def __setitem__(self, k, v): pass
    @abstractmethod
    def __delitem__(self, v): pass
    @abstractmethod
    def __contains__(self, o): pass

    @abstractmethod
    def clear(self): pass
    @abstractmethod
    def copy(self): pass
    @overload
    @abstractmethod
    def get(self, k): pass
    @overload
    @abstractmethod
    def get(self, k, default): pass
    @overload
    @abstractmethod
    def pop(self, k): pass
    @overload
    @abstractmethod
    def pop(self, k, default): pass
    @abstractmethod
    def popitem(self): pass
    @overload
    @abstractmethod
    def setdefault(self, k): pass
    @overload
    @abstractmethod
    def setdefault(self, k, default): pass
    
    @overload
    @abstractmethod
    def update(self, m): pass
    @overload
    @abstractmethod
    def update(self, m): pass
    
    @abstractmethod
    def keys(self): pass
    @abstractmethod
    def values(self): pass
    @abstractmethod
    def items(self): pass


# TODO Consider more types: os.environ, etc. However, these add dependencies.
Mapping.register(dict)


# Note that the IO and TextIO classes must be in sync with typing module stubs.


class IO():
    __metaclass__ = ABCMeta
    @abstractmethod
    def close(self): pass
    @abstractmethod
    def closed(self): pass
    @abstractmethod
    def fileno(self): pass
    @abstractmethod
    def flush(self): pass
    @abstractmethod
    def isatty(self): pass
    @abstractmethod
    def read(self, n = -1): pass
    @abstractmethod
    def readable(self): pass
    @abstractmethod
    def readline(self, limit = -1): pass
    @abstractmethod
    def readlines(self, hint = -1): pass
    @abstractmethod
    def seek(self, offset, whence = 0): pass
    @abstractmethod
    def seekable(self): pass
    @abstractmethod
    def tell(self): pass
    @abstractmethod
    def truncate(self, size = None): pass
    @abstractmethod
    def writable(self): pass
    @overload
    @abstractmethod
    def write(self, s): pass
    @overload
    @abstractmethod
    def write(self, s): pass
    @abstractmethod
    def writelines(self, lines): pass

    @abstractmethod
    def __enter__(self): pass
    @abstractmethod
    def __exit__(self, type, value, traceback): pass


class TextIO():
    __metaclass__ = ABCMeta
    @abstractmethod
    def close(self): pass
    @abstractmethod
    def closed(self): pass
    @abstractmethod
    def fileno(self): pass
    @abstractmethod
    def flush(self): pass
    @abstractmethod
    def isatty(self): pass
    @abstractmethod
    def read(self, n = -1): pass
    @abstractmethod
    def readable(self): pass
    @abstractmethod
    def readline(self, limit = -1): pass
    @abstractmethod
    def readlines(self, hint = -1): pass
    @abstractmethod
    def seek(self, offset, whence = 0): pass
    @abstractmethod
    def seekable(self): pass
    @abstractmethod
    def tell(self): pass
    @abstractmethod
    def truncate(self, size = None): pass
    @abstractmethod
    def writable(self): pass
    @abstractmethod
    def write(self, s): pass
    @abstractmethod
    def writelines(self, lines): pass

    @abstractmethod
    def __enter__(self): pass
    @abstractmethod
    def __exit__(self, type, value, traceback): pass


# TODO Register [Text]IO as the base class of file-like types.


del t
