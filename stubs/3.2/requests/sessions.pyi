# Stubs for requests.sessions (Python 3)

from typing import Any, Union, MutableMapping
from . import auth
from . import compat
from . import cookies
from . import models
from .models import Response
from . import hooks
from . import utils
from . import exceptions
from .packages.urllib3 import _collections
from . import structures
from . import adapters
from . import status_codes

OrderedDict = compat.OrderedDict
cookiejar_from_dict = cookies.cookiejar_from_dict
extract_cookies_to_jar = cookies.extract_cookies_to_jar
RequestsCookieJar = cookies.RequestsCookieJar
merge_cookies = cookies.merge_cookies
Request = models.Request
PreparedRequest = models.PreparedRequest
DEFAULT_REDIRECT_LIMIT = models.DEFAULT_REDIRECT_LIMIT
default_hooks = hooks.default_hooks
dispatch_hook = hooks.dispatch_hook
to_key_val_list = utils.to_key_val_list
default_headers = utils.default_headers
to_native_string = utils.to_native_string
TooManyRedirects = exceptions.TooManyRedirects
InvalidSchema = exceptions.InvalidSchema
ChunkedEncodingError = exceptions.ChunkedEncodingError
ContentDecodingError = exceptions.ContentDecodingError
RecentlyUsedContainer = _collections.RecentlyUsedContainer
CaseInsensitiveDict = structures.CaseInsensitiveDict
HTTPAdapter = adapters.HTTPAdapter
requote_uri = utils.requote_uri
get_environ_proxies = utils.get_environ_proxies
get_netrc_auth = utils.get_netrc_auth
should_bypass_proxies = utils.should_bypass_proxies
get_auth_from_url = utils.get_auth_from_url
codes = status_codes.codes
REDIRECT_STATI = models.REDIRECT_STATI

REDIRECT_CACHE_SIZE = ... # type: Any

def merge_setting(request_setting, session_setting, dict_class=...): pass
def merge_hooks(request_hooks, session_hooks, dict_class=...): pass

class SessionRedirectMixin:
    def resolve_redirects(self, resp, req, stream=False, timeout=None, verify=True, cert=None,
                          proxies=None): pass
    def rebuild_auth(self, prepared_request, response): pass
    def rebuild_proxies(self, prepared_request, proxies): pass

class Session(SessionRedirectMixin):
    __attrs__ = ... # type: Any
    headers = ... # type: MutableMapping[str, str]
    auth = ... # type: Any
    proxies = ... # type: Any
    hooks = ... # type: Any
    params = ... # type: Any
    stream = ... # type: Any
    verify = ... # type: Any
    cert = ... # type: Any
    max_redirects = ... # type: Any
    trust_env = ... # type: Any
    cookies = ... # type: Any
    adapters = ... # type: Any
    redirect_cache = ... # type: Any
    def __init__(self) -> None: pass
    def __enter__(self) -> 'Session': pass
    def __exit__(self, *args) -> None: pass
    def prepare_request(self, request): pass
    def request(self, method: str, url: Union[str, bytes], params=None, data=None, headers=None,
                cookies=None, files=None, auth=None, timeout=None, allow_redirects=True,
                proxies=None, hooks=None, stream=None, verify=None, cert=None,
                json=None) -> Response: pass
    def get(self, url: Union[str, bytes], **kwargs) -> Response: pass
    def options(self, url: Union[str, bytes], **kwargs) -> Response: pass
    def head(self, url: Union[str, bytes], **kwargs) -> Response: pass
    def post(self, url: Union[str, bytes], data=None, json=None, **kwargs) -> Response: pass
    def put(self, url: Union[str, bytes], data=None, **kwargs) -> Response: pass
    def patch(self, url: Union[str, bytes], data=None, **kwargs) -> Response: pass
    def delete(self, url: Union[str, bytes], **kwargs) -> Response: pass
    def send(self, request, **kwargs): pass
    def merge_environment_settings(self, url, proxies, stream, verify, cert): pass
    def get_adapter(self, url): pass
    def close(self) -> None: pass
    def mount(self, prefix, adapter): pass

def session() -> Session: pass
