import json
import os
import unittest

from framework.routing import Rule, Endpoint, Map, Path
from framework.service import http, Service
from framework.service.http import File
from framework.utils import utc

from .test_http import status_codes, Response
from .. import dummy, Dummy, DummyStartResponse

environ, start_response = dict(QUERY_STRING=''), DummyStartResponse()


def dummy_status(path: Path):
    return b'', None if 0 == path['code'] else path['code']


def dummy_args(*args):
    return str(args)


def dummy_path(*args, path: Path):
    return str({
        'args': args,
        'path': path['name'],
    })


def dummy_page(path: Path):
    return path['name']


def dummy_json(path: Path):
    return json.dumps(getattr(path, '_Path__token'))


def dummy_file(path: Path):
    return File(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', path['filename'])))


def dummy_redirect(path: Path):
    return b'', path['status'], [('location', f"/{path['redirect']}")]


def dummy_not_found(code: int):
    return b'Dummy Not Found', code


class DummyNotFound(object):
    @staticmethod
    def dummy_not_found(code: int):
        return b'Dummy Not Found', code

    def __call__(self, code: int):
        return b'Dummy Not Found', code


class TestModule(Response):
    def test_status(self):
        def second():
            environ['PATH_INFO'] = f"/{0 if code is None else code}"
            list(app(environ, start_response))

            return start_response.status

        app = Service(Map((
            Rule('/<int:code>', 'status'),
            Endpoint('status', dummy_status)
        )))

        for first, code in status_codes:
            self.assertEqual(first, second())

    def test_environ(self):
        app = Service()

        environ['PATH_INFO'] = '/path-info'
        environ['QUERY_STRING'] = 'query-string'

        tuple(app(environ, start_response))

        self.assertDictEqual({'PATH_INFO': '/path-info', 'QUERY_STRING': 'query-string'}, http.environ)

    def test_args(self):
        def args():
            return 'arg-1', 'arg-2', 'arg-3'

        none = None

        app = Service(Map((
            Rule('/', 'args'),
            Endpoint('args', dummy_args, 1, 2, 3, True, False, none, *args()),
            Rule('/<name>', 'path', {'name': (0, r'[a-z.]+')}),
            Endpoint('path', dummy_path, *args()),
        )))

        environ['PATH_INFO'] = '/'

        self.assertTupleEqual(
            (1, 2, 3, True, False, None, 'arg-1', 'arg-2', 'arg-3'),
            eval(b''.join(app(environ, start_response))),
        )

        environ['PATH_INFO'] = '/path.info'

        self.assertDictEqual(
            {'args': ('arg-1', 'arg-2', 'arg-3'), 'path': 'path.info'},
            eval(b''.join(app(environ, start_response))),
        )

    def test_path(self):
        app = Service(Map((
            Rule('/', 'index'),
            Endpoint('index', dummy),
            Rule('/<name>', 'page'),
            Endpoint('page', dummy_page),
            Rule('/<str>/<int:int>/<float:float>', 'json'),
            Endpoint('json', dummy_json),
            Rule('/date/<int(4):year>/<int(1,2):month>/<int(1,2):day>', 'date'),
            Endpoint('date', dummy_json),
        )))

        environ['PATH_INFO'] = '/'

        self.assertListEqual(list(), list(app(environ, start_response)))

        environ['PATH_INFO'] = '/page-name'

        self.assertEqual(b'page-name', b''.join(app(environ, start_response)))

        environ['PATH_INFO'] = '/value_01/001/003.14'

        self.assertDictEqual(
            {'str': 'value_01', 'int': 1, 'float': 3.14},
            json.loads(b''.join(app(environ, start_response))),
        )

        year, month, day = str(utc.now.year), str(utc.now.month), str(utc.now.day)

        environ['PATH_INFO'] = f"/date/{year}/{month}/{day}"

        self.assertDictEqual(
            {'year': utc.now.year, 'month': utc.now.month, 'day': utc.now.day},
            json.loads(b''.join(app(environ, start_response))),
        )

        with self.assertRaises(ValueError) as context:
            Service(Map((Rule('', 'link'),)))

        self.assertEqual(
            "URL Map. Rule. Path must not be an empty string.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Service(Map((Rule('slash', 'link'),)))

        self.assertEqual(
            "URL Map. Rule. Path must start slash: 'slash'.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Service(Map((Rule('/<int(1,2,3):name>', 'link'),)))

        self.assertEqual(
            "URL Map. Rule. Path token 'int' format error: int(1,2,3).",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Service(Map((Rule('/<error:name>', 'link'),)))

        self.assertEqual(
            "URL Map. Rule. Path token has an invalid flag: 'error:name'.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Service(Map((
                Rule('/path', 'link'),
                Rule('/path', 'link'),
            )))

        self.assertEqual(
            "URL Map. Rule. Path already exists in pattern list: '/path'.",
            context.exception.args[0],
        )

    def test_token(self):
        app = Service(Map((
            Rule('/<name>', 'page'),
            Endpoint('page', dummy_page),
            Rule('/float-<int>/<float>', 'float',
                 {'int': (1, r'\d+'), 'float': (2, r'\d\.\d{5}')}),
            Endpoint('float', dummy_json),
            Rule('/archive/<year>', 'archive',
                 {'year': (0, r'\d{4}')}),
            Rule('/archive/<year>/<month>', 'archive',
                 {'year': (0, r'\d{4}'), 'month': (0, r'\d{1,2}')}),
            Rule('/archive/<year>/<month>/<day>', 'archive',
                 {'year': (0, r'\d{4}'), 'month': (0, r'\d{1,2}'), 'day': (0, r'\d{1,2}')}),
            Endpoint('archive', dummy_json),
        )))

        environ['PATH_INFO'] = '/page-name'

        self.assertEqual(b'page-name', b''.join(app(environ, start_response)))

        year, month, day = str(utc.now.year), str(utc.now.month), str(utc.now.day)

        environ['PATH_INFO'] = f"/float-{day}/3.14159"

        self.assertDictEqual(
            {'int': utc.now.day, 'float': 3.14159},
            json.loads(b''.join(app(environ, start_response))),
        )

        environ['PATH_INFO'] = f"/archive/{year}"

        self.assertDictEqual(
            {'year': year},
            json.loads(b''.join(app(environ, start_response))),
        )

        environ['PATH_INFO'] = f"/archive/{year}/{month}"

        self.assertDictEqual(
            {'year': year, 'month': month},
            json.loads(b''.join(app(environ, start_response))),
        )

        environ['PATH_INFO'] = f"/archive/{year}/{month}/{day}"

        self.assertDictEqual(
            {'year': year, 'month': month, 'day': day},
            json.loads(b''.join(app(environ, start_response))),
        )

        with self.assertRaises(ValueError) as context:
            Service(Map((Rule('/<token>', 'link', {'token': (3, r'...')}),)))

        self.assertEqual(
            "URL Map. Rule. The added token has an invalid type flag: (3, '...').",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Service(Map((Rule('/<path>', 'link', {'token': (3, r'...')}),)))

        self.assertEqual(
            "URL Map. Rule. Patterns added to rules have unused values: {'token': (3, '...')}.",
            context.exception.args[0],
        )

    def test_endpoint(self):
        def endpoint(path_info: str):
            environ['PATH_INFO'] = path_info

            self.assertEqual(b'', b''.join(app(environ, start_response)))

        app = Service(Map((
            Rule('/function', 'function'),
            Endpoint('function', dummy),
            Rule('/class', 'class'),
            Endpoint('class', Dummy),
            Rule('/call', 'call'),
            Endpoint('call', (Dummy,)),
            Rule('/method', 'method'),
            Endpoint('method', (Dummy, 'dummy')),
        )))

        endpoint('/function')
        endpoint('/class')
        endpoint('/call')
        endpoint('/method')

        with self.assertRaises(ValueError) as context:
            Service(Map((
                Endpoint('link', dummy),
                Endpoint('link', dummy),
            )))

        self.assertEqual(
            "URL Map. Endpoint. Link already exists in endpoint list: 'link'.",
            context.exception.args[0],
        )

    def test_file(self):
        def response(path_info: str, first: bytes):
            environ['PATH_INFO'] = path_info

            self.assertEqual(first, b''.join(app(environ, start_response)))

        app = Service(Map((
            Rule('/<filename>', 'file', {'filename': (0, r'[a-z.]+')}),
            Endpoint('file', dummy_file),
        )))

        response('/file.css', b'* {\r\n    margin: 0;\r\n    padding: 0;\r\n}')
        self.start_response(start_response, '39', 'text/css; charset=utf-8')

        response('/file.json', b'{\r\n    "none": null\r\n}')
        self.start_response(start_response, '22', 'application/json')

        response('/file.txt', b'simple text')
        self.start_response(start_response, '11', 'text/plain; charset=utf-8')

    def test_redirect(self):
        def redirect(path_info: str):
            environ['PATH_INFO'] = path_info

            tuple(app(environ, start_response))

            for key, value in start_response.headers:
                if 'location' == key:
                    return start_response.status, value

        app = Service(Map((
            Rule('/<redirect>/<int:status>', 'redirect'),
            Endpoint('redirect', dummy_redirect),
        )))

        status, location = redirect('/permanently/301')

        self.assertEqual('301 Moved Permanently', status)
        self.assertEqual('/permanently', location)

        status, location = redirect('/temporarily/302')

        self.assertEqual('302 Moved Temporarily', status)
        self.assertEqual('/temporarily', location)

        status, location = redirect('/temporary/307')

        self.assertEqual('307 Temporary Redirect', status)
        self.assertEqual('/temporary', location)

        status, location = redirect('/permanent/308')

        self.assertEqual('308 Permanent Redirect', status)
        self.assertEqual('/permanent', location)

    def test_not_found(self):
        app = Service()

        environ['PATH_INFO'] = '/'

        self.assertEqual(b'Not Found', b''.join(app(environ, start_response)))
        self.assertEqual('404 Not Found', start_response.status)
        for key, value in start_response.headers:
            match key:
                case 'content-length':
                    self.assertEqual('9', value)

                case 'content-type':
                    self.assertEqual('text/plain; charset=ascii', value)

        self.dummy_not_found(Service(not_found=dummy_not_found))
        self.dummy_not_found(Service(not_found=DummyNotFound))
        self.dummy_not_found(Service(not_found=(DummyNotFound,)))
        self.dummy_not_found(Service(not_found=(DummyNotFound, 'dummy_not_found')))

    def dummy_not_found(self, app: Service):
        self.assertEqual(b'Dummy Not Found', b''.join(app(environ, start_response)))
        self.assertEqual('404 Not Found', start_response.status)
        for key, value in start_response.headers:
            match key:
                case 'content-length':
                    self.assertEqual('15', value)

                case 'content-type':
                    self.assertEqual('text/plain; charset=utf-8', value)


def service_tests():
    from .test_http import http_tests
    from .test_static import static_tests

    suite = unittest.TestSuite()
    suite.addTests(http_tests())
    suite.addTests(static_tests())

    for test in (
            'test_status',
            'test_environ',
            'test_args',
            'test_path',
            'test_token',
            'test_endpoint',
            'test_file',
            'test_redirect',
            'test_not_found',
    ):
        suite.addTest(TestModule(test))

    return suite
