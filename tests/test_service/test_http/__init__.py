import io
import json
import os
import unittest

from framework.service.http import header, Http, File, Route

from ... import DummyStartResponse

start_response, status_codes = DummyStartResponse(), (
    ('200 OK', None),
    ('200 OK', 200),
    ('301 Moved Permanently', 301),
    ('302 Moved Temporarily', 302),
    ('307 Temporary Redirect', 307),
    ('308 Permanent Redirect', 308),
    ('404 Not Found', 404),
    ('500 Internal Server Error', 500),
    ('520 Unknown Error', 520),
    ('520 Unknown Error', 999),
)


class Response(unittest.TestCase):
    def start_response(self, response: DummyStartResponse, length: str, mimetype: str):
        self.assertEqual('200 OK', response.status)

        content_length = content_type = None

        for name, value in response.headers:
            match name:
                case 'content-length':
                    content_length = value
                case 'content-type':
                    content_type = value

        self.assertEqual(content_length, length)
        self.assertEqual(content_type, mimetype)


class TestModule(Response):
    def setUp(self):
        for attr, value in (('encoding', 'utf-8'), ('buffer_size', io.DEFAULT_BUFFER_SIZE)):
            setattr(Http, attr, value)

        for attr in ('simple', 'cookie'):
            setattr(header, attr, dict())

    def test_status(self):
        def response_status():
            tuple(Route(b'', code)(start_response))

            return start_response.status

        for status, code in status_codes:
            self.assertEqual(status, response_status())

    def test_file(self):
        def filepath(filename: str):
            return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'static', filename))

        app = File(filepath('file.css'))

        self.assertEqual(b'* {\r\n    margin: 0;\r\n    padding: 0;\r\n}', b''.join(app(start_response)))
        self.start_response(start_response, '39', 'text/css; charset=utf-8')

        app = File(filepath('file.json'))

        self.assertDictEqual({'none': None}, json.loads(b''.join(app(start_response))))
        self.start_response(start_response, '22', 'application/json')

        app = File(filepath('file.txt'))

        self.assertEqual(b'simple text', b''.join(app(start_response)))
        self.start_response(start_response, '11', 'text/plain; charset=utf-8')

        with self.assertRaises(FileNotFoundError):
            File(filepath('file.error'))

    def test_body(self):
        app = Route(1)

        self.assertEqual(b'', b''.join(app(start_response)))
        self.start_response(start_response, '0', 'text/plain')

        app = Route("class 'str'")

        self.assertEqual(b"class 'str'", b''.join(app(start_response)))
        self.start_response(start_response, '11', 'text/plain; charset=utf-8')

        app = Route(b"class 'bytes'")

        self.assertEqual(b"class 'bytes'", b''.join(app(start_response)))
        self.start_response(start_response, '13', 'text/plain; charset=utf-8')

    def test_header(self):
        tuple(Route(
            b'', None, [('name', 'header value'), ('location', '/response.redirect')]
        )(start_response))

        name = location = None

        for key, value in start_response.headers:
            if 'name' == key:
                name = value

            if 'location' == key:
                location = value

        self.assertEqual('header value', name)
        self.assertEqual('/response.redirect', location)

    def test_mimetype(self):
        def mime(body: bytes = b'', mimetype: str = None, encoding: str = None):
            tuple(Route(body, mimetype=mimetype, encoding=encoding)(start_response))

            for key, value in start_response.headers:
                if 'content-type' == key:
                    return value

        self.assertEqual('text/plain', mime())
        self.assertEqual('text/plain; charset=utf-8', mime(b's'))
        self.assertEqual('text/plain; charset=ascii', mime(b's', encoding='ascii'))
        self.assertEqual('text/css', mime(mimetype='text/css'))
        self.assertEqual('text/css; charset=utf-8', mime(b's', 'text/css'))
        self.assertEqual('text/css; charset=ascii', mime(b's', 'text/css', 'ascii'))
        self.assertEqual('application/json', mime(mimetype='application/json'))
        self.assertEqual('application/json', mime(mimetype='application/json', encoding='ascii'))


def http_tests():
    from .test_header import header_tests
    from .test_parse import parse_tests

    suite = unittest.TestSuite()
    suite.addTests(header_tests())
    suite.addTests(parse_tests())

    for test in (
            'test_status',
            'test_file',
            'test_body',
            'test_header',
            'test_mimetype',
    ):
        suite.addTest(TestModule(test))

    return suite
