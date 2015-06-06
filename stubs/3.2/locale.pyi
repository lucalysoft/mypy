# Stubs for locale (Python 3.4)
#
# NOTE: This stub is based on a stub automatically generated by stubgen.

from _locale import *

def format(percent, value, grouping=False, monetary=False, *additional): pass
def format_string(f, val, grouping=False): pass
def currency(val, symbol=True, grouping=False, international=False): pass
def str(val): pass
def atof(string, func=...): pass
def atoi(str): pass
def normalize(localename): pass
def getdefaultlocale(envvars=...): pass
def getlocale(category=...): pass
def resetlocale(category=...): pass
def getpreferredencoding(do_setlocale=True): pass
