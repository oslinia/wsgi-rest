from datetime import datetime, timedelta
from typing import Literal

from ..service import HttpResponse
from ..service.http.header import format_expires, Cookie


class Response(HttpResponse):
    def url_file(self, name: str):
        return f"{self.static.urlpath}{name}"

    def url_for(self, *args: str, **kwargs: str):
        return self.static.link.collect(args, kwargs)

    def redirect(self, urlpath: str, status_code: int = 307):
        self.header.simple['location'] = urlpath

        return b'', status_code

    def set_header(self, name: str, value: str):
        self.header.simple[name.lower()] = value

    def get_header(self, name: str):
        return self.header.simple.get(name.lower())

    def has_header(self, name: str):
        return name.lower() in self.header.simple.keys()

    def delete_header(self, name: str):
        if (name := name.lower()) in self.header.simple.keys():
            del self.header.simple[name]

    def set_cookie(
            self,
            name: str,
            value: str,
            domain: str = None,
            path: str = '/',
            expires: datetime | str | int | float = None,
            max_age: timedelta | int = None,
            httponly: bool = False,
            secure: bool = False,
            samesite: Literal['none', 'lax', 'strict'] = None,
    ):
        self.header.cookie[name] = Cookie(
            name, value, domain, path, expires, max_age, httponly, secure, samesite
        ).value()

    def delete_cookie(self, name: str, path: str = '/', domain: str = None):
        value = f"{name}="

        if domain is not None:
            value = f"{value}; domain={domain}"

        self.header.cookie[name] = f"{value}; path={path}; expires={format_expires(0)}"
