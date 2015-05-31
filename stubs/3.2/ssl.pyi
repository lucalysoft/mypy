# Stubs for ssl (Python 3.4)

from typing import Any
from enum import Enum as _Enum
from socket import socket
from collections import namedtuple

class SSLError(OSError): pass
class SSLEOFError(SSLError): pass
class SSLSyscallError(SSLError): pass
class SSLWantReadError(SSLError): pass
class SSLWantWriteError(SSLError): pass
class SSLZeroReturnError(SSLError): pass

OPENSSL_VERSION = ... # type: str
OPENSSL_VERSION_INFO = ... # type: Any
OPENSSL_VERSION_NUMBER = ... # type: int

VERIFY_CRL_CHECK_CHAIN = ... # type: int
VERIFY_CRL_CHECK_LEAF = ... # type: int
VERIFY_DEFAULT = ... # type: int
VERIFY_X509_STRICT = ... # type: int

ALERT_DESCRIPTION_ACCESS_DENIED = ... # type: int
ALERT_DESCRIPTION_BAD_CERTIFICATE = ... # type: int
ALERT_DESCRIPTION_BAD_CERTIFICATE_HASH_VALUE = ... # type: int
ALERT_DESCRIPTION_BAD_CERTIFICATE_STATUS_RESPONSE = ... # type: int
ALERT_DESCRIPTION_BAD_RECORD_MAC = ... # type: int
ALERT_DESCRIPTION_CERTIFICATE_EXPIRED = ... # type: int
ALERT_DESCRIPTION_CERTIFICATE_REVOKED = ... # type: int
ALERT_DESCRIPTION_CERTIFICATE_UNKNOWN = ... # type: int
ALERT_DESCRIPTION_CERTIFICATE_UNOBTAINABLE = ... # type: int
ALERT_DESCRIPTION_CLOSE_NOTIFY = ... # type: int
ALERT_DESCRIPTION_DECODE_ERROR = ... # type: int
ALERT_DESCRIPTION_DECOMPRESSION_FAILURE = ... # type: int
ALERT_DESCRIPTION_DECRYPT_ERROR = ... # type: int
ALERT_DESCRIPTION_HANDSHAKE_FAILURE = ... # type: int
ALERT_DESCRIPTION_ILLEGAL_PARAMETER = ... # type: int
ALERT_DESCRIPTION_INSUFFICIENT_SECURITY = ... # type: int
ALERT_DESCRIPTION_INTERNAL_ERROR = ... # type: int
ALERT_DESCRIPTION_NO_RENEGOTIATION = ... # type: int
ALERT_DESCRIPTION_PROTOCOL_VERSION = ... # type: int
ALERT_DESCRIPTION_RECORD_OVERFLOW = ... # type: int
ALERT_DESCRIPTION_UNEXPECTED_MESSAGE = ... # type: int
ALERT_DESCRIPTION_UNKNOWN_CA = ... # type: int
ALERT_DESCRIPTION_UNKNOWN_PSK_IDENTITY = ... # type: int
ALERT_DESCRIPTION_UNRECOGNIZED_NAME = ... # type: int
ALERT_DESCRIPTION_UNSUPPORTED_CERTIFICATE = ... # type: int
ALERT_DESCRIPTION_UNSUPPORTED_EXTENSION = ... # type: int
ALERT_DESCRIPTION_USER_CANCELLED = ... # type: int

OP_ALL = ... # type: int
OP_CIPHER_SERVER_PREFERENCE = ... # type: int
OP_NO_COMPRESSION = ... # type: int
OP_NO_SSLv2 = ... # type: int
OP_NO_SSLv3 = ... # type: int
OP_NO_TLSv1 = ... # type: int
OP_NO_TLSv1_1 = ... # type: int
OP_NO_TLSv1_2 = ... # type: int
OP_SINGLE_DH_USE = ... # type: int
OP_SINGLE_ECDH_USE = ... # type: int

SSL_ERROR_EOF = ... # type: int
SSL_ERROR_INVALID_ERROR_CODE = ... # type: int
SSL_ERROR_SSL = ... # type: int
SSL_ERROR_SYSCALL = ... # type: int
SSL_ERROR_WANT_CONNECT = ... # type: int
SSL_ERROR_WANT_READ = ... # type: int
SSL_ERROR_WANT_WRITE = ... # type: int
SSL_ERROR_WANT_X509_LOOKUP = ... # type: int
SSL_ERROR_ZERO_RETURN = ... # type: int

CERT_NONE = ... # type: int
CERT_OPTIONAL = ... # type: int
CERT_REQUIRED = ... # type: int

PROTOCOL_SSLv23 = ... # type: int
PROTOCOL_SSLv3 = ... # type: int
PROTOCOL_TLSv1 = ... # type: int
PROTOCOL_TLSv1_1 = ... # type: int
PROTOCOL_TLSv1_2 = ... # type: int

HAS_ECDH = ... # type: bool
HAS_NPN = ... # type: bool
HAS_SNI = ... # type: bool

def RAND_add(string, entropy): pass
def RAND_bytes(n): pass
def RAND_egd(path): pass
def RAND_pseudo_bytes(n): pass
def RAND_status(): pass

socket_error = OSError

CHANNEL_BINDING_TYPES = ... # type: Any

class CertificateError(ValueError): pass

def match_hostname(cert, hostname): pass

DefaultVerifyPaths = namedtuple(
    'DefaultVerifyPaths',
    'cafile capath openssl_cafile_env openssl_cafile openssl_capath_env openssl_capath')

def get_default_verify_paths(): pass

class _ASN1Object:
    def __new__(cls, oid): pass
    @classmethod
    def fromnid(cls, nid): pass
    @classmethod
    def fromname(cls, name): pass

class Purpose(_ASN1Object, _Enum):
    SERVER_AUTH = ... # type: Any
    CLIENT_AUTH = ... # type: Any

class _SSLContext:
    check_hostname = ... # type: Any
    options = ... # type: Any
    verify_flags = ... # type: Any
    verify_mode = ... # type: Any
    def __init__(self, *args, **kwargs): pass
    def _set_npn_protocols(self, *args, **kwargs): pass
    def _wrap_socket(self, *args, **kwargs): pass
    def cert_store_stats(self): pass
    def get_ca_certs(self, binary_form=False): pass
    def load_cert_chain(self, *args, **kwargs): pass
    def load_dh_params(self, *args, **kwargs): pass
    def load_verify_locations(self, *args, **kwargs): pass
    def session_stats(self, *args, **kwargs): pass
    def set_ciphers(self, *args, **kwargs): pass
    def set_default_verify_paths(self, *args, **kwargs): pass
    def set_ecdh_curve(self, *args, **kwargs): pass
    def set_servername_callback(self, method): pass

class SSLContext(_SSLContext):
    def __new__(cls, protocol, *args, **kwargs): pass
    protocol = ... # type: Any
    def __init__(self, protocol): pass
    def wrap_socket(self, sock, server_side=False, do_handshake_on_connect=True,
                    suppress_ragged_eofs=True, server_hostname=None): pass
    def set_npn_protocols(self, npn_protocols): pass
    def load_default_certs(self, purpose=...): pass

def create_default_context(purpose=..., *, cafile=None, capath=None, cadata=None): pass

class SSLSocket(socket):
    keyfile = ... # type: Any
    certfile = ... # type: Any
    cert_reqs = ... # type: Any
    ssl_version = ... # type: Any
    ca_certs = ... # type: Any
    ciphers = ... # type: Any
    server_side = ... # type: Any
    server_hostname = ... # type: Any
    do_handshake_on_connect = ... # type: Any
    suppress_ragged_eofs = ... # type: Any
    context = ... # type: Any  # TODO: This should be a property.
    def __init__(self, sock=None, keyfile=None, certfile=None, server_side=False,
                 cert_reqs=..., ssl_version=..., ca_certs=None,
                 do_handshake_on_connect=True, family=..., type=..., proto=0,
                 fileno=None, suppress_ragged_eofs=True, npn_protocols=None, ciphers=None,
                 server_hostname=None, _context=None): pass
    def dup(self): pass
    def read(self, len=0, buffer=None): pass
    def write(self, data): pass
    def getpeercert(self, binary_form=False): pass
    def selected_npn_protocol(self): pass
    def cipher(self): pass
    def compression(self): pass
    def send(self, data, flags=0): pass
    def sendto(self, data, flags_or_addr, addr=None): pass
    def sendmsg(self, *args, **kwargs): pass
    def sendall(self, data, flags=0): pass
    def recv(self, buflen=1024, flags=0): pass
    def recv_into(self, buffer, nbytes=None, flags=0): pass
    def recvfrom(self, buflen=1024, flags=0): pass
    def recvfrom_into(self, buffer, nbytes=None, flags=0): pass
    def recvmsg(self, *args, **kwargs): pass
    def recvmsg_into(self, *args, **kwargs): pass
    def pending(self): pass
    def shutdown(self, how): pass
    def unwrap(self): pass
    def do_handshake(self, block=False): pass
    def connect(self, addr): pass
    def connect_ex(self, addr): pass
    def accept(self): pass
    def get_channel_binding(self, cb_type=''): pass

def wrap_socket(sock, keyfile=None, certfile=None, server_side=False, cert_reqs=...,
                ssl_version=..., ca_certs=None, do_handshake_on_connect=True,
                suppress_ragged_eofs=True, ciphers=None): pass
def cert_time_to_seconds(cert_time): pass

PEM_HEADER = ... # type: Any
PEM_FOOTER = ... # type: Any

def DER_cert_to_PEM_cert(der_cert_bytes): pass
def PEM_cert_to_DER_cert(pem_cert_string): pass
def get_server_certificate(addr, ssl_version=..., ca_certs=None): pass
def get_protocol_name(protocol_code): pass
