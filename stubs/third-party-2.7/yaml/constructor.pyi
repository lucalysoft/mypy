# Stubs for yaml.constructor (Python 2)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any
from yaml.error import *
from yaml.nodes import *

class ConstructorError(MarkedYAMLError): ...

class BaseConstructor:
    yaml_constructors = ... # type: Any
    yaml_multi_constructors = ... # type: Any
    constructed_objects = ... # type: Any
    recursive_objects = ... # type: Any
    state_generators = ... # type: Any
    deep_construct = ... # type: Any
    def __init__(self): ...
    def check_data(self): ...
    def get_data(self): ...
    def get_single_data(self): ...
    def construct_document(self, node): ...
    def construct_object(self, node, deep=False): ...
    def construct_scalar(self, node): ...
    def construct_sequence(self, node, deep=False): ...
    def construct_mapping(self, node, deep=False): ...
    def construct_pairs(self, node, deep=False): ...
    def add_constructor(cls, tag, constructor): ...
    add_constructor = ... # type: Any
    def add_multi_constructor(cls, tag_prefix, multi_constructor): ...
    add_multi_constructor = ... # type: Any

class SafeConstructor(BaseConstructor):
    def construct_scalar(self, node): ...
    def flatten_mapping(self, node): ...
    def construct_mapping(self, node, deep=False): ...
    def construct_yaml_null(self, node): ...
    bool_values = ... # type: Any
    def construct_yaml_bool(self, node): ...
    def construct_yaml_int(self, node): ...
    inf_value = ... # type: Any
    nan_value = ... # type: Any
    def construct_yaml_float(self, node): ...
    def construct_yaml_binary(self, node): ...
    timestamp_regexp = ... # type: Any
    def construct_yaml_timestamp(self, node): ...
    def construct_yaml_omap(self, node): ...
    def construct_yaml_pairs(self, node): ...
    def construct_yaml_set(self, node): ...
    def construct_yaml_str(self, node): ...
    def construct_yaml_seq(self, node): ...
    def construct_yaml_map(self, node): ...
    def construct_yaml_object(self, node, cls): ...
    def construct_undefined(self, node): ...

class Constructor(SafeConstructor):
    def construct_python_str(self, node): ...
    def construct_python_unicode(self, node): ...
    def construct_python_long(self, node): ...
    def construct_python_complex(self, node): ...
    def construct_python_tuple(self, node): ...
    def find_python_module(self, name, mark): ...
    def find_python_name(self, name, mark): ...
    def construct_python_name(self, suffix, node): ...
    def construct_python_module(self, suffix, node): ...
    class classobj: ...
    def make_python_instance(self, suffix, node, args=None, kwds=None, newobj=False): ...
    def set_python_instance_state(self, instance, state): ...
    def construct_python_object(self, suffix, node): ...
    def construct_python_object_apply(self, suffix, node, newobj=False): ...
    def construct_python_object_new(self, suffix, node): ...
