import mimetypes
import os
import sys
from collections.abc import Callable, Generator
from typing import Any, TypeAlias

from . import header
from .parse import EnvironParse
from ...routing import Map
from ...routing.urlmap import Callback
from ...utils.alias import HeadersAlias, StartResponse, WSGIEnvironment

CallableResponse: TypeAlias = Callable[[StartResponse], Generator[bytes]]

call: EnvironParse
environ: WSGIEnvironment


def status(code: int):
    status_codes = {
        200: '200 OK',
        301: '301 Moved Permanently',
        302: '302 Moved Temporarily',
        307: '307 Temporary Redirect',
        308: '308 Permanent Redirect',
        404: '404 Not Found',
        500: '500 Internal Server Error',
        520: '520 Unknown Error',
    }

    return status_codes[code if code in status_codes.keys() else 520]


class Http(object):
    __slots__ = ('encoding', 'buffer_size', 'size', 'headers', 'mimetype')

    encoding: str
    buffer_size: int
    size: int
    headers: HeadersAlias
    mimetype: str

    def mime(self, mimetype: str | None, encoding: str | None):
        if mimetype is None:
            mimetype = 'text/plain'

        if mimetype.startswith('text/'):
            if 0 < self.size:
                if encoding is None:
                    encoding = self.encoding

                mimetype = f"{mimetype}; charset={encoding}"

        self.mimetype = mimetype

    def content_header(self, mimetype: str):
        self.headers.extend([('content-length', str(self.size)), ('content-type', mimetype)])

        return self.headers


class File(Http):
    __slots__ = ('filepath',)

    def __init__(self, filepath: str):
        self.filepath, self.size, self.headers = filepath, os.path.getsize(filepath), HeadersAlias()

        self.mime(*mimetypes.guess_type(filepath, strict=True))

        setattr(Routing, 'file', True)

    def __call__(self, start_response: StartResponse) -> Generator[bytes]:
        start_response(status(200), self.content_header(self.mimetype))

        try:
            f = open(self.filepath, 'rb')
            for i in range(0, self.size, self.buffer_size):
                yield f.read(self.buffer_size)

            f.close()

        except OSError:
            pass


class Route(Http):
    __slots__ = ('body', 'code')

    def __init__(
            self,
            body: Any,
            code: int = None,
            headers: HeadersAlias = None,
            mimetype: str = None,
            encoding: str = None,
    ):
        if not isinstance(body, bytes):
            if isinstance(body, str):
                body = body.encode(encoding := self.encoding if encoding is None else encoding)

            else:
                body = b''

        self.body, self.size = body, len(body)

        if code is None:
            code = 200

        if headers is None:
            headers = list()

        headers.extend(header.headers())
        headers.extend(header.cookies())

        self.code, self.headers = code, headers

        self.mime(mimetype, encoding)

    def __call__(self, start_response: StartResponse) -> Generator[bytes]:
        start_response(status(self.code), self.content_header(self.mimetype))

        for i in range(0, self.size, self.buffer_size):
            yield self.body[i:i + self.buffer_size]


def import_callback(module: str, name: str, method: str | None) -> Callable[..., Any]:
    __import__(module)

    callback = getattr(sys.modules[module], name)

    if method is not None:
        callback = getattr(callback(), method)

    setattr(Routing, 'file', False)

    return callback


def as_tuple(callback: Any):
    return callback if isinstance(callback, tuple) else (callback,)


class Routing(object):
    __slots__ = ('file', 'callback', 'not_found')

    file: bool

    def __init__(self, urlmap: Map, not_found: tuple[str, str, str | None] | None):
        self.callback = Callback(urlmap)
        self.not_found = not_found

    def error(self, code: int) -> CallableResponse:
        if self.not_found is None:
            return Route(b'Not Found', code, None, encoding='ascii')

        else:
            return Route(*as_tuple(import_callback(*self.not_found)(code)))

    def response(self, link: str, kwargs: dict[str, Any]) -> CallableResponse:
        module, name, method, args = self.callback[link]

        callback = import_callback(module, name, method)(*args, **kwargs)

        if self.file:
            return callback

        return Route(*as_tuple(callback))
