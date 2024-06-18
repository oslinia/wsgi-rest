import io
import os
from collections.abc import Callable, Iterable
from datetime import datetime, timezone

from .http import header, Http, File, Routing
from .http.parse import EnvironParse
from .static import valid
from ..routing import Map
from ..routing.urlmap import Link, Mapped
from ..utils import utc
from ..utils.alias import StartResponse, WSGIEnvironment, WSGIApplication


def recompile(not_found: Callable | tuple[Callable] | tuple[Callable, str] | None):
    if not_found is not None:
        if isinstance(nf := not_found, tuple):
            not_found, method = nf[0], nf[1] if 2 == len(nf) else '__call__'

        else:
            method = '__call__' if isinstance(not_found, type) else None

        return not_found.__module__, not_found.__name__, method


class Service(Routing):
    __slots__ = ('mapped',)

    def __init__(
            self: WSGIApplication,
            urlmap: Map = None,
            not_found: Callable | tuple[Callable] | tuple[Callable, str] = None,
            static_urlpath: str = None,
    ):
        if urlmap is None:
            urlmap = Map(())

        self.mapped = Mapped(urlmap)

        super().__init__(urlmap, recompile(not_found))

        for attr, value in (
                ('urlpath', valid(static_urlpath)),
                ('link', Link(urlmap)),
        ):
            setattr(static, attr, value)

        for attr, value in (
                ('encoding', 'utf-8'),
                ('buffer_size', io.DEFAULT_BUFFER_SIZE),
        ):
            setattr(Http, attr, value)

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]:
        for attr, value in (
                ('now', dt := datetime.now(tz=timezone.utc)),
                ('timestamp', dt.timestamp()),
        ):
            setattr(utc, attr, value)

        for attr, value in (
                ('call', EnvironParse(environ)),
                ('environ', environ),
        ):
            setattr(http, attr, value)

        for attr in (
                'simple', 'cookie'
        ):
            setattr(header, attr, dict())

        link, kwargs = self.mapped.parse(environ)

        if link is None:
            return self.error(404)(start_response)

        return self.response(link, kwargs)(start_response)


class HttpRequest(object):
    __slots__ = ('http',)

    def __init__(self):
        self.http = http


class HttpResponse(object):
    __slots__ = ('__file', 'header', 'static')

    def __init__(self):
        self.__file = File
        self.header = header
        self.static = static

    def file(self, filepath: str | os.PathLike):
        if os.path.isfile(filepath):
            return self.__file(filepath)

        return b'File not found', 404
