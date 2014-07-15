"""Test cases for the infer module"""

import unittest

from pinfer import Instance, Generic, Tuple, Either, Unknown
import pinfer


class TestInfer(unittest.TestCase):
    def setUp(self):
        self.int = Instance(int)
        self.float = Instance(float)

    def tearDown(self):
        pinfer.reset()

    def test_instance(self):
        i = self.int
        self.assertEqual(i.typeobj, int)
        self.assertEqual(str(i), 'int')
        self.assertEqual(repr(i), 'Instance(int)')
        
        self.assertTrue(i == Instance(int))
        self.assertFalse(i != Instance(int))
        self.assertTrue(i != self.float)
        self.assertFalse(i == self.float)
        self.assertNotEqual(i, None)
    
    def test_generic_with_one_arg(self):
        g = Generic('List', [self.int])
        self.assertEqual(g.typename, 'List')
        self.assertEqual(str(g.args), '(Instance(int),)')
        self.assertEqual(str(g), 'List[int]')
        self.assertEqual(repr(g), 'List[int]')

        self.assertEqual(g, Generic('List', [self.int]))
        self.assertNotEqual(g, Generic('Set', [self.int]))
        self.assertNotEqual(g, Generic('List', [self.float]))
        self.assertNotEqual(g, self.int)
    
    def test_generic_with_two_args(self):
        g = Generic('Dict', (self.int, self.float))
        self.assertEqual(g.typename, 'Dict')
        self.assertEqual(str(g), 'Dict[int, float]')

    def test_tuple(self):
        t0 = Tuple(())
        t1 = Tuple([self.int])
        t2 = Tuple((self.float, self.int))
        self.assertEqual(t0.itemtypes, ())
        self.assertEqual(str(t1.itemtypes[0]), 'int')
        self.assertEqual(str(t2.itemtypes[0]), 'float')
        self.assertEqual(str(t2.itemtypes[1]), 'int')
        self.assertEqual(str(t0), 'Tuple[]')
        self.assertEqual(str(t1), 'Tuple[int]')
        self.assertEqual(str(t2), 'Tuple[float, int]')

        self.assertEqual(t1, Tuple([self.int]))
        self.assertNotEqual(t1, Tuple([self.float]))
        self.assertNotEqual(t1, Tuple([self.int, self.int]))
        self.assertNotEqual(t1, self.int)

    def test_either(self):
        i = self.int
        f = self.float
        s = Instance(str)
        
        e2 = Either((i, f))
        self.assertEqual(len(e2.types), 2)
        self.assertEqual(str(e2), 'Either(float, int)')

        self.assertEqual(e2, Either((i, f)))
        self.assertEqual(e2, Either((f, i)))
        self.assertNotEqual(e2, Either((i, s)))
        self.assertNotEqual(e2, Either((i, f, s)))
        self.assertNotEqual(Either((i, f, s)), e2)
        self.assertNotEqual(e2, i)

    def test_either_as_optional(self):
        optint = Either((self.int, None))
        self.assertEqual(str(optint), 'Optional(int)')
        optfloat = Either((None, self.float))
        self.assertEqual(str(optfloat), 'Optional(float)')
        eithernone = Either((self.int, self.float, None))
        self.assertEqual(str(eithernone), 'Either(None, float, int)')

    def test_unknown(self):
        unknown = Unknown()
        self.assertEqual(str(unknown), 'Unknown')
        self.assertEqual(repr(unknown), 'Unknown()')
        
        self.assertEqual(unknown, Unknown())
        self.assertNotEqual(unknown, self.int)

    def test_combine_types(self):
        i = self.int
        f = self.float
        s = Instance(str)
        # Simple types
        self.assert_combine(i, i, i)
        self.assert_combine(f, f, f)
        self.assert_combine(i, f, Either((i, f)))
        self.assert_combine(i, None, Either((i, None)))
        # Unknowns
        self.assert_combine(i, Unknown(), i)
        self.assert_combine(Unknown(), Unknown(), Unknown())
        # Either types
        self.assert_combine(i, Either((f, s)), Either((i, f, s)))
        self.assert_combine(i, Either((i, f)), Either((i, f)))
        self.assert_combine(Either((i, f)), Either((i, s)), Either((i, f, s)))
        # Tuple types
        self.assert_combine(Tuple([i, i]), Tuple([i, i]), Tuple([i, i]))
        self.assert_combine(Tuple([i, i]), Tuple([f, s]),
                            Tuple([Either([f, i]), Either([s, i])]))

    def test_combine_special_cases(self):
        i = self.int
        f = self.float
        u = Unknown()
        def list_(x):
            return Generic('List', [x])
        # Simplify generic types.
        self.assert_combine(list_(i), list_(u), list_(i))

    def assert_combine(self, t, s, combined):
        self.assertEqual(pinfer.combine_types(t, s), combined)
        self.assertEqual(pinfer.combine_types(s, t), combined)

    def test_sample(self):
        sample = pinfer.sample
        self.assertEqual(sample(()), [])
        self.assertEqual(sample((1, 2)), [1, 2])
        self.assertEqual(sample([]), [])
        self.assertEqual(sample([1]), [1])
        self.assertEqual(sample([1, 2]), [1, 2])
        # TODO larger collections
    
    def test_infer_simple_value_type(self):
        self.assert_infer_type(1, 'int')
        self.assert_infer_type('', 'str')
        self.assert_infer_type(None, 'None')

    def test_infer_collection_type(self):
        # List
        self.assert_infer_type([], 'List[Unknown]')
        self.assert_infer_type([1], 'List[int]')
        self.assert_infer_type([1, None], 'List[Optional(int)]')
        # Dict
        self.assert_infer_type({1: 'x', 2: None},
                               'Dict[int, Optional(str)]')
        # Set
        self.assert_infer_type({1, None}, 'Set[Optional(int)]')
        # Tuple
        self.assert_infer_type((1, 'x'), 'Tuple[int, str]')
        self.assert_infer_type((1, None) * 100, 'TupleSequence[Optional(int)]')

    def assert_infer_type(self, value, type):
        self.assertEqual(str(pinfer.infer_value_type(value)), type)

    def test_infer_variables(self):
        pinfer.infer_var('x', 1)
        self.assert_infer_state('x: int')
        pinfer.infer_var('x', 1)
        pinfer.infer_var('x', None)
        pinfer.infer_var('y', 1.1)
        self.assert_infer_state('x: Optional(int)\n'
                                'y: float')

    def test_infer_instance_var(self):
        class A: pass
        a = A()
        a.x = 1
        a.y = 'x'
        pinfer.infer_attrs(a)
        self.assert_infer_state('A.x: int\n'
                                'A.y: str')

    def test_infer_class_var(self):
        class A:
            x = 1.1
        pinfer.infer_attrs(A())
        self.assert_infer_state('A.x: float')

    def test_infer_function_attr(self):        
        class A:
            def f(self): pass
        a = A()
        a.g = lambda x: 1
        pinfer.infer_attrs(a)
        self.assert_infer_state('A.g: function')

    def test_infer_simple_function_signature(self):
        @pinfer.infer_signature
        def f(a):
            return 'x'
        f(1)
        f(None)
        self.assertEqual(f.__name__, 'f')
        self.assert_infer_state('def f(a: Optional(int)) -> str')

    def test_infer_function_with_two_args(self):
        @pinfer.infer_signature
        def f(x, y):
            return x * y
        f(1, 2)
        f(1, 'x')
        self.assert_infer_state(
            'def f(x: int, y: Either(int, str)) -> Either(int, str)')

    def test_infer_method(self):
        class A:
            @pinfer.infer_signature
            def f(self, x): pass
        A().f('x')
        self.assert_infer_state('def f(self, x: str) -> None')

    def test_infer_default_arg_values(self):
        @pinfer.infer_signature
        def f(x=1, y=None): pass
        f()
        self.assert_infer_state('def f(x: int, y: None) -> None')
        f('x')
        f('x', 1.1)
        f()
        self.assert_infer_state(
            'def f(x: Either(int, str), y: Optional(float)) -> None')

    def test_infer_varargs(self):
        @pinfer.infer_signature
        def f(x, *y): pass
        f(1)
        f(1, 'x', None)
        self.assert_infer_state('def f(x: int, y: Optional(str)) -> None')
        f(1)
        self.assert_infer_state('def f(x: int) -> None')

    def test_infer_keyword_args(self):
        @pinfer.infer_signature
        def f(x): pass
        f(x=1)
        self.assert_infer_state('def f(x: int) -> None')
        
        @pinfer.infer_signature
        def f(x='x'): pass
        f(x=1)
        self.assert_infer_state('def f(x: int) -> None')

    def test_infer_keyword_varargs(self):
        @pinfer.infer_signature
        def f(a, **kwargs): pass
        f(None, x=1, y='x')
        self.assert_infer_state(
            'def f(a: None, kwargs: Either(int, str)) -> None')

    def test_infer_keyword_only_args(self):
        @pinfer.infer_signature
        def f(x, *, y=0): pass
        f(1, y='x')
        self.assert_infer_state(
            'def f(x: int, y: str) -> None')
        
        @pinfer.infer_signature
        def f(*, x=None, y=None): pass
        f(y='x')
        self.assert_infer_state(
            'def f(x: None, y: str) -> None')

    def test_infer_class(self):
        @pinfer.infer_class
        class A:
            def f(self, x): return 0
        A().f('x')
        self.assert_infer_state('class A(...):\n'
                                '    def f(self, x: str) -> int')

        @pinfer.infer_class
        class A:
            def f(self, x): return 0
        @pinfer.infer_class
        class B:
            def f(self): pass
            def g(self): pass
        A().f('')
        B().f()
        B().g()
        self.assert_infer_state('class A(...):\n'
                                '    def f(self, x: str) -> int\n'
                                'class B(...):\n'
                                '    def f(self) -> None\n'
                                '    def g(self) -> None')

    def assert_infer_state(self, expected):
        self.assertEqual(pinfer.format_state(), expected)
        pinfer.reset()


if __name__ == '__main__':
    unittest.main()
