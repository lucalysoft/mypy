# Stubs for requests.packages.urllib3.filepost (Python 3.4)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any
from . import packages
#from .packages import six
from . import fields

#six = packages.six
#b = six.b
RequestField = fields.RequestField

writer = ...  # type: Any

def choose_boundary(): pass
def iter_field_objects(fields): pass
def iter_fields(fields): pass
def encode_multipart_formdata(fields, boundary=None): pass
