# Stubs for email.utils (Python 3.4)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from email._parseaddr import mktime_tz
from email._parseaddr import parsedate, parsedate_tz

mktime_tz = mktime_tz
parsedate = parsedate
parsedate_tz = parsedate_tz

def formataddr(pair, charset=''): pass
def getaddresses(fieldvalues): pass
def formatdate(timeval=None, localtime=False, usegmt=False): pass
def format_datetime(dt, usegmt=False): pass
def make_msgid(idstring=None, domain=None): pass
def parsedate_to_datetime(data): pass
def parseaddr(addr): pass
def unquote(str): pass
def decode_rfc2231(s): pass
def encode_rfc2231(s, charset=None, language=None): pass
def decode_params(params): pass
def collapse_rfc2231_value(value, errors='', fallback_charset=''): pass
