import sys
import unittest
from datetime import datetime, timedelta
from email.utils import format_datetime

from framework.service import Service
from framework.service.http import header
from framework.service.http.header import cookie_format, format_expires, Cookie
from framework.utils import utc

from ... import DummyStartResponse

format_utc: str
delta: datetime
format_delta: str

start_response = DummyStartResponse()


def init(
        i: int,
        value: datetime | str | int | float | bool = None,
        args: list[datetime | str | int | float | bool | None] = None
):
    if args is None:
        args = ['test', 'value', None, '/', None, None, False, False, None]

    if 0 == i:
        return args

    args[i] = value

    return args


class TestModule(unittest.TestCase):
    def setUp(self):
        tuple(Service()(dict(QUERY_STRING=''), start_response))

        setattr(sys.modules[__name__], 'format_utc', format_datetime(utc.now, True))
        setattr(sys.modules[__name__], 'delta', utc.now + timedelta(days=1))
        setattr(sys.modules[__name__], 'format_delta', format_datetime(delta, True))

    def test_blank(self):
        self.assertDictEqual(dict(), header.simple)
        self.assertDictEqual(dict(), header.cookie)

    def test_format(self):
        self.assertEqual(format_utc, cookie_format(utc.now))

        with self.assertRaises(ValueError) as context:
            cookie_format(datetime.now(tz=None))

        self.assertEqual(
            "Cookie requires UTC datetime.",
            context.exception.args[0],
        )

        self.assertEqual(format_utc, format_expires(utc.now))
        self.assertEqual(format_utc, format_expires(format_utc))
        self.assertEqual('Thu, 01 Jan 1970 00:00:00 GMT', format_expires(0))
        self.assertEqual(format_utc, format_expires(utc.timestamp))

        with self.assertRaises(ValueError) as context:
            format_expires(format_datetime(utc.now))

        self.assertEqual(
            "Datetime string format does not match for cookie.",
            context.exception.args[0],
        )

    def test_cookie_body(self):
        for first, args in (
                ('test=value; path=/', init(0)),
                ('test=value; domain=127.0.0.1; path=/', init(2, '127.0.0.1')),
        ):
            self.assertEqual(first, Cookie(*args).value())

    def test_cookie_expires(self):
        for args in (
                init(4, utc.now),
                init(4, format_datetime(utc.now, True)),
                init(4, int(utc.timestamp)),
                init(4, utc.timestamp),
        ):
            self.assertEqual('test=value; path=/; expires=%s' % format_utc, Cookie(*args).value())

        with self.assertRaises(ValueError) as context:
            Cookie(*init(4, datetime.now(tz=None))).value()

        self.assertEqual(
            "Cookie requires UTC datetime.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Cookie(*init(4, format_datetime(utc.now))).value()

        self.assertEqual(
            "Datetime string format does not match for cookie.",
            context.exception.args[0],
        )

        for first, second in (
                (
                        'test=value; path=/; expires=%s; max-age=86400' % format_delta,
                        Cookie(*init(5, day := 60 * 60 * 24)).value(),
                ),
                (
                        'test=value; path=/; expires=%s; max-age=86400' % format_utc,
                        Cookie(*init(4, utc.now, init(5, day))).value(),
                ),
                (
                        'test=value; path=/; expires=%s; max-age=86400' % format_utc,
                        Cookie(*init(4, format_utc, init(5, day))).value(),
                ),
        ):
            self.assertEqual(first, second)

    def test_cookie_security(self):
        for first, args in (
                ('test=value; path=/; %s' % 'HttpOnly', init(6, True)),
                ('test=value; path=/; %s' % 'Secure', init(7, True)),
        ):
            self.assertEqual(first, Cookie(*args).value())

        for first, args in (
                ('test=value; path=/; samesite=%s' % 'none', init(8, 'none')),
                ('test=value; path=/; samesite=%s' % 'lax', init(8, 'lax')),
                ('test=value; path=/; samesite=%s' % 'strict', init(8, 'strict')),
        ):
            self.assertEqual(first, Cookie(*args).value())

        with self.assertRaises(ValueError) as context:
            Cookie(*init(8, 'error')).value()

        self.assertEqual(
            "Cookie value samesite='error', maybe: ('none', 'lax', 'strict').",
            context.exception.args[0],
        )

    def test_cookie_full(self):
        self.assertEqual(
            'test=value; domain=127.0.0.1; path=/; expires=%s; HttpOnly; Secure; samesite=lax' % format_utc,
            Cookie(*('test', 'value', '127.0.0.1', '/', utc.now, None, True, True, 'lax')).value()
        )

        body = 'test=value; domain=127.0.0.1; path=/; expires=%s; max-age=86400; HttpOnly; Secure; samesite=%s'

        self.assertEqual(
            body % (format_utc, 'none'),
            Cookie(*('test', 'value', '127.0.0.1', '/', utc.now, 86400, True, True, 'none')).value()
        )

        self.assertEqual(
            body % (format_delta, 'lax'),
            Cookie(*('test', 'value', '127.0.0.1', '/', None, 86400, True, True, 'lax')).value()
        )

        self.assertEqual(
            body % (format_delta, 'strict'),
            Cookie(*('test', 'value', '127.0.0.1', '/', delta, 86400, True, True, 'strict')).value()
        )


def header_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_blank',
            'test_format',
            'test_cookie_body',
            'test_cookie_expires',
            'test_cookie_security',
            'test_cookie_full',
    ):
        suite.addTest(TestModule(test))

    return suite
