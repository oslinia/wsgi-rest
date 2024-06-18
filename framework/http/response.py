import os
from datetime import datetime, timedelta
from typing import Literal

from ..service import static
from ..service.http import header, File
from ..service.http.header import format_expires, Cookie


def url_file(name: str):
    return f"{static.urlpath}{name}"


def url_for(*args: str, **kwargs: str):
    return static.link.collect(args, kwargs)


def file(filepath: str | os.PathLike):
    if os.path.isfile(filepath):
        return File(filepath)

    return b'File not found', 404


def redirect(urlpath: str, status_code: int = 307):
    header.simple['location'] = urlpath

    return b'', status_code


def set_header(name: str, value: str):
    header.simple[name.lower()] = value


def get_header(name: str):
    return header.simple.get(name.lower())


def has_header(name: str):
    return name.lower() in header.simple.keys()


def delete_header(name: str):
    if (name := name.lower()) in header.simple.keys():
        del header.simple[name]


def set_cookie(
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
    header.cookie[name] = Cookie(
        name, value, domain, path, expires, max_age, httponly, secure, samesite
    ).value()


def delete_cookie(name: str, path: str = '/', domain: str = None):
    value = f"{name}="

    if domain is not None:
        value = f"{value}; domain={domain}"

    header.cookie[name] = f"{value}; path={path}; expires={format_expires(0)}"
