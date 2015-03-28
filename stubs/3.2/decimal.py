# Stubs for _decimal (Python 3.4)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any, Undefined

BasicContext = Undefined(Any)
DefaultContext = Undefined(Any)
ExtendedContext = Undefined(Any)
HAVE_THREADS = Undefined(bool)
MAX_EMAX = Undefined(int)
MAX_PREC = Undefined(int)
MIN_EMIN = Undefined(int)
MIN_ETINY = Undefined(int)
ROUND_05UP = Undefined(str)
ROUND_CEILING = Undefined(str)
ROUND_DOWN = Undefined(str)
ROUND_FLOOR = Undefined(str)
ROUND_HALF_DOWN = Undefined(str)
ROUND_HALF_EVEN = Undefined(str)
ROUND_HALF_UP = Undefined(str)
ROUND_UP = Undefined(str)

def getcontext(): pass
def localcontext(ctx=None): pass
def setcontext(c): pass

class Clamped(DecimalException): pass

class Context:
    Emax = Undefined(Any)
    Emin = Undefined(Any)
    capitals = Undefined(Any)
    clamp = Undefined(Any)
    prec = Undefined(Any)
    rounding = Undefined(Any)
    def __init__(self, *args, **kwargs): pass
    def __init__(self, *args, **kwargs): pass
    def Etiny(self): pass
    def Etop(self): pass
    def _apply(self, *args, **kwargs): pass
    def abs(self, x): pass
    def add(self, x, y): pass
    def canonical(self, x): pass
    def clear_flags(self): pass
    def clear_traps(self): pass
    def compare(self, x, y): pass
    def compare_signal(self, x, y): pass
    def compare_total(self, x, y): pass
    def compare_total_mag(self, x, y): pass
    def copy(self): pass
    def copy_abs(self, x): pass
    def copy_decimal(self, x): pass
    def copy_negate(self, x): pass
    def copy_sign(self, x, y): pass
    def create_decimal(self, x): pass
    def create_decimal_from_float(self, f): pass
    def divide(self, x, y): pass
    def divide_int(self, x, y): pass
    def divmod(self, x, y): pass
    def exp(self, x): pass
    def fma(self, x, y, z): pass
    def is_canonical(self, x): pass
    def is_finite(self, x): pass
    def is_infinite(self, x): pass
    def is_nan(self, x): pass
    def is_normal(self, x): pass
    def is_qnan(self, x): pass
    def is_signed(self, x): pass
    def is_snan(self): pass
    def is_subnormal(self, x): pass
    def is_zero(self, x): pass
    def ln(self, x): pass
    def log10(self, x): pass
    def logb(self, x): pass
    def logical_and(self, x, y): pass
    def logical_invert(self, x): pass
    def logical_or(self, x, y): pass
    def logical_xor(self, x, y): pass
    def max(self, x, y): pass
    def max_mag(self, x, y): pass
    def min(self, x, y): pass
    def min_mag(self, x, y): pass
    def minus(self, x): pass
    def multiply(self, x, y): pass
    def next_minus(self, x): pass
    def next_plus(self, x): pass
    def next_toward(self, x): pass
    def normalize(self, x): pass
    def number_class(self, x): pass
    def plus(self, x): pass
    def power(self, x, y): pass
    def quantize(self, x, y): pass
    def radix(self): pass
    def remainder(self, x, y): pass
    def remainder_near(self, x, y): pass
    def rotate(self, x, y): pass
    def same_quantum(self, x, y): pass
    def scaleb(self, x, y): pass
    def shift(self, x, y): pass
    def sqrt(self, x): pass
    def subtract(self, x, y): pass
    def to_eng_string(self, x): pass
    def to_integral(self, x): pass
    def to_integral_exact(self, x): pass
    def to_integral_value(self, x): pass
    def to_sci_string(self, x): pass
    def __copy__(self): pass
    def __delattr__(self, name): pass
    def __reduce__(self): pass
    def __setattr__(self, name, value): pass

class ConversionSyntax(InvalidOperation): pass

class Decimal:
    imag = Undefined(Any)
    real = Undefined(Any)
    def __init__(self, *args, **kwargs): pass
    def adjusted(self): pass
    def as_tuple(self): pass
    def canonical(self): pass
    def compare(self, other, context=None): pass
    def compare_signal(self, other, context=None): pass
    def compare_total(self, other, context=None): pass
    def compare_total_mag(self, other, context=None): pass
    def conjugate(self): pass
    def copy_abs(self): pass
    def copy_negate(self): pass
    def copy_sign(self, other, context=None): pass
    def exp(self, context=None): pass
    def fma(self, other, third, context=None): pass
    @classmethod
    def from_float(cls, f): pass
    def is_canonical(self): pass
    def is_finite(self): pass
    def is_infinite(self): pass
    def is_nan(self): pass
    def is_normal(self, context=None): pass
    def is_qnan(self): pass
    def is_signed(self): pass
    def is_snan(self): pass
    def is_subnormal(self, context=None): pass
    def is_zero(self): pass
    def ln(self, context=None): pass
    def log10(self, context=None): pass
    def logb(self, context=None): pass
    def logical_and(self, other, context=None): pass
    def logical_invert(self, context=None): pass
    def logical_or(self, other, context=None): pass
    def logical_xor(self, other, context=None): pass
    def max(self, other, context=None): pass
    def max_mag(self, other, context=None): pass
    def min(self, other, context=None): pass
    def min_mag(self, other, context=None): pass
    def next_minus(self, context=None): pass
    def next_plus(self, context=None): pass
    def next_toward(self, other, context=None): pass
    def normalize(self, context=None): pass
    def number_class(self, context=None): pass
    def quantize(self, exp, rounding=None, context=None): pass
    def radix(self): pass
    def remainder_near(self, other, context=None): pass
    def rotate(self, other, context=None): pass
    def same_quantum(self, other, context=None): pass
    def scaleb(self, other, context=None): pass
    def shift(self, other, context=None): pass
    def sqrt(self, context=None): pass
    def to_eng_string(self, context=None): pass
    def to_integral(self, rounding=None, context=None): pass
    def to_integral_exact(self, rounding=None, context=None): pass
    def to_integral_value(self, rounding=None, context=None): pass
    def __abs__(self, *args, **kwargs): pass
    def __add__(self, other): pass
    def __bool__(self): pass
    def __ceil__(self, *args, **kwargs): pass
    def __complex__(self): pass
    def __copy__(self): pass
    def __deepcopy__(self): pass
    def __divmod__(self, other): pass
    def __eq__(self, other): pass
    def __float__(self): pass
    def __floor__(self, *args, **kwargs): pass
    def __floordiv__(self, other): pass
    def __format__(self, *args, **kwargs): pass
    def __ge__(self, other): pass
    def __gt__(self, other): pass
    def __hash__(self): pass
    def __int__(self): pass
    def __le__(self, other): pass
    def __lt__(self, other): pass
    def __mod__(self, other): pass
    def __mul__(self, other): pass
    def __ne__(self, other): pass
    def __neg__(self): pass
    def __pos__(self): pass
    def __pow__(self, other): pass
    def __radd__(self, other): pass
    def __rdivmod__(self, other): pass
    def __reduce__(self): pass
    def __rfloordiv__(self, other): pass
    def __rmod__(self, other): pass
    def __rmul__(self, other): pass
    def __round__(self, *args, **kwargs): pass
    def __rpow__(self, other): pass
    def __rsub__(self, other): pass
    def __rtruediv__(self, other): pass
    def __sizeof__(self): pass
    def __sub__(self, other): pass
    def __truediv__(self, other): pass
    def __trunc__(self): pass

class DecimalException(ArithmeticError): pass

class DecimalTuple(tuple):
    __new__ = Undefined(Any)
    _asdict = Undefined(Any)
    _fields = Undefined(Any)
    _make = Undefined(Any)
    _replace = Undefined(Any)
    _source = Undefined(Any)
    digits = Undefined(Any)
    exponent = Undefined(Any)
    sign = Undefined(Any)
    __getnewargs__ = Undefined(Any)
    __getstate__ = Undefined(Any)
    __slots__ = Undefined(Any)

class DivisionByZero(DecimalException, ZeroDivisionError): pass

class DivisionImpossible(InvalidOperation): pass

class DivisionUndefined(InvalidOperation, ZeroDivisionError): pass

class FloatOperation(DecimalException, TypeError): pass

class Inexact(DecimalException): pass

class InvalidContext(InvalidOperation): pass

class InvalidOperation(DecimalException): pass

class Overflow(Inexact, Rounded): pass

class Rounded(DecimalException): pass

class Subnormal(DecimalException): pass

class Underflow(Inexact, Rounded, Subnormal): pass
