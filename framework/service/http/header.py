import re
from datetime import datetime, timedelta, timezone
from typing import Literal

from ...utils import utc

simple: dict[str, str]
cookie: dict[str, str]


def headers():
    return [(k, v) for k, v in simple.items()]


def cookies():
    return [('set-cookie', v) for v in cookie.values()]


wd = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
mn = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def cookie_format(dt: datetime):
    if dt.tzinfo is None or dt.tzinfo != timezone.utc:
        raise ValueError('Cookie requires UTC datetime.')

    t = dt.timetuple()

    return '%s, %02d %s %04d %02d:%02d:%02d GMT' % (wd[t[6]], t[2], mn[t[1] - 1], t[0], t[3], t[4], t[5])


def format_expires(variable: datetime | str | int | float):
    if isinstance(variable, int | float):
        variable = datetime.fromtimestamp(variable, tz=timezone.utc)

    if isinstance(variable, datetime):
        return cookie_format(variable)

    else:
        if r := re.search(
                r'^([A-Za-z]{3}), (\d{2}) ([A-Za-z]{3}) (\d{4}) (\d{2}:\d{2}:\d{2}) GMT$', variable
        ):
            if r[1] in wd and r[3] in mn:
                return variable

        raise ValueError('Datetime string format does not match for cookie.')


def flags(httponly: bool, secure: bool):
    security = ''

    if httponly:
        security += '; HttpOnly'

    if secure:
        security += '; Secure'

    return security


class Cookie(object):
    __slots__ = ('body', 'expires', 'security')

    def __init__(
            self,
            name: str,
            value: str,
            domain: str | None,
            path: str,
            expires: datetime | str | int | float | None,
            max_age: timedelta | int | None,
            httponly: bool,
            secure: bool,
            samesite: Literal['none', 'lax', 'strict'] | None,
    ):
        self.body = f"{name}={value}"

        if domain is not None:
            self.body += f"; domain={domain}"

        self.body += f"; path={path}"

        if expires is None:
            self.expires = ''

        else:
            self.expires = f"; expires={format_expires(expires)}"

        if max_age is not None:
            self.max_age(max_age, bool(expires))

        self.security = flags(httponly, secure)

        if samesite is not None:
            if samesite not in ('none', 'lax', 'strict'):
                raise ValueError(f"Cookie value samesite='{samesite}', maybe: ('none', 'lax', 'strict').")

            self.security += f"; samesite={samesite}"

    def max_age(self, max_age: timedelta | int, true: bool):
        if isinstance(max_age, timedelta):
            max_age = int(max_age.total_seconds())

        if not true:
            self.expires = f"; expires={format_expires(utc.timestamp + max_age)}"

        self.expires += f"; max-age={max_age}"

    def value(self):
        return ''.join((getattr(self, a) for a in self.__slots__))
