import os
import unittest

from framework.http import url_file, url_for
from framework.http import file
from framework.http import redirect
from framework.http import set_header, get_header, has_header, delete_header
from framework.http import set_cookie, delete_cookie
from framework.routing import Rule, Endpoint, Map, Path
from framework.service import Service
from framework.utils.alias import WSGIApplication

from .. import dummy, DummyStartResponse

environ, start_response = dict(QUERY_STRING=''), DummyStartResponse()


def dummy_url_for(path: Path):
    if value := path.get('float'):
        if (
                isinstance(value, float) and 3.141592 == value or 3.14 == value and
                isinstance(path['int'], int) and 1 == path['int'] and
                isinstance(path['str'], str) and 'str' == path['str']
        ):
            return 'float'

    if value := path.get('int'):
        if (
                isinstance(value, int) and 1 == value and
                isinstance(path['str'], str) and 'str' == path['str']
        ):
            return 'int'

    if value := path.get('str'):
        if isinstance(value, str) and 'str' == value:
            return 'str'


def dummy_file(path: Path):
    return file(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', path['filename'])))


def dummy_redirect(path: Path):
    url = url_for('dummy', dummy=path['redirect'])

    if 0 == path['code']:
        args = url,
    else:
        args = url, path['code']

    return redirect(*args)


def dummy_header():
    set_header('header', 'header')
    set_header('delete', 'delete')
    true = has_header('delete')
    value = get_header('delete')
    delete_header('delete')
    return str((true, value, has_header('delete')))


def dummy_cookie():
    set_cookie('one', 'one cookie')
    set_cookie('two', 'two cookie')
    set_cookie('delete', 'delete')
    delete_cookie('delete')


class Headers(unittest.TestCase):
    def header(self, app: WSGIApplication, response: DummyStartResponse):
        def header():
            for key, value in response.headers:
                if 'header' == key:
                    return value

        environ['PATH_INFO'] = '/header'

        self.assertTupleEqual((True, 'delete', False), eval(b''.join(app(environ, response))))
        self.assertEqual('header', header())

    def cookie(self, app: WSGIApplication, response: DummyStartResponse):
        def cookie_headers():
            cookie = dict()

            for name, body in response.headers:
                if 'set-cookie' == name:
                    cookie[body.split('=', 1)[0]] = body

            return cookie

        environ['PATH_INFO'] = '/cookie'

        tuple(app(environ, response))

        self.assertDictEqual(
            {
                'one': 'one=one cookie; path=/',
                'two': 'two=two cookie; path=/',
                'delete': 'delete=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT',
            }, cookie_headers()
        )


class TestModule(Headers):
    def test_url_file(self):
        Service()

        self.assertEqual('/test.file', url_file('test.file'))

        Service(static_urlpath='/path/to/file/')

        self.assertEqual('/path/to/file/test.file', url_file('test.file'))

    def test_url_for(self):
        def response(path_info: str, url: str, first: bytes):
            self.assertEqual(path_info, url)

            environ['PATH_INFO'] = path_info

            self.assertEqual(first, b''.join(app(environ, start_response)))

        Service()

        self.assertIsNone(url_for('index'))

        app = Service(Map((
            Rule('/path/<str>', 'path'),
            Rule('/path/<str>/<int(2):int>', 'path'),
            Rule('/path/<str>/<int:int>/<float:float>', 'path'),
            Endpoint('path', dummy_url_for),
            Rule('/token/<str>', 'token',
                 {'str': (0, r'[a-z]+')}),
            Rule('/token/<str>/<int>', 'token',
                 {'str': (0, r'[a-z]+'), 'int': (1, r'\d{2}')}),
            Rule('/token/<str>/<int>/<float>', 'token',
                 {'str': (0, r'[a-z]+'), 'int': (1, r'\d+'), 'float': (2, r'\d\.\d{2}')}),
            Endpoint('token', dummy_url_for),
        )))

        self.assertIsNone(url_for('path', str='str', int='1'))
        self.assertIsNone(url_for('path', str='str', int='001'))

        response('/path/str', url_for('path', str='str'), b'str')
        response('/path/str/01', url_for('path', str='str', int='01'), b'int')
        response(
            '/path/str/001/3.141592',
            url_for('path', str='str', int='001', float='3.141592'),
            b'float'
        )

        self.assertIsNone(url_for('token', str='str', int='1'))
        self.assertIsNone(url_for('token', str='str', int='001', float='3.141592'))

        response('/token/str', url_for('token', str='str'), b'str')
        response('/token/str/01', url_for('token', str='str', int='01'), b'int')
        response(
            '/token/str/001/3.14',
            url_for('token', str='str', int='001', float='3.14'),
            b'float'
        )

    def test_file(self):
        app = Service(Map((
            Rule('/<filename>', 'file', {'filename': (0, r'[a-z.]+')}),
            Endpoint('file', dummy_file),
        )))

        self.response(app, '/file.css', b'* {\r\n    margin: 0;\r\n    padding: 0;\r\n}')
        self.start_response('39', 'text/css; charset=utf-8')

        self.response(app, '/file.json', b'{\r\n    "none": null\r\n}')
        self.start_response('22', 'application/json')

        self.response(app, '/file.txt', b'simple text')
        self.start_response('11', 'text/plain; charset=utf-8')

        self.response(app, '/file.error', b'File not found')
        self.start_response('14', 'text/plain; charset=utf-8', '404 Not Found')

    def response(self, app: Service, path_info: str, body: bytes):
        environ['PATH_INFO'] = path_info

        self.assertEqual(body, b''.join(app(environ, start_response)))

    def start_response(self, length: str, mimetype: str, status: str = '200 OK'):
        self.file_content(length, mimetype)

        self.assertEqual(start_response.status, status)

    def file_content(self, length: str, mimetype: str):
        content_length = content_type = None

        for name, value in start_response.headers:
            match name:
                case 'content-length':
                    content_length = value
                case 'content-type':
                    content_type = value

        self.assertEqual(content_length, length)
        self.assertEqual(content_type, mimetype)

    def test_redirect(self):
        def response(target: str, code: int):
            environ['PATH_INFO'] = url_for('redirect', redirect=target, code=str(code))

            tuple(app(environ, start_response))

            for key, value in start_response.headers:
                if 'location' == key:
                    return start_response.status, value

        app = Service(Map((
            Rule('/<dummy>', 'dummy'),
            Endpoint('dummy', dummy),
            Rule('/<redirect>/<int:code>', 'redirect'),
            Endpoint('redirect', dummy_redirect),
        )))

        status, location = response('permanently', 301)

        self.assertEqual('301 Moved Permanently', status)
        self.assertEqual('/permanently', location)

        status, location = response('temporarily', 302)

        self.assertEqual('302 Moved Temporarily', status)
        self.assertEqual('/temporarily', location)

        status, location = response('temporary', 0)

        self.assertEqual('307 Temporary Redirect', status)
        self.assertEqual('/temporary', location)

        status, location = response('permanent', 308)

        self.assertEqual('308 Permanent Redirect', status)
        self.assertEqual('/permanent', location)

    def test_headers(self):
        app = Service(Map((
            Rule('/header', 'header'),
            Endpoint('header', dummy_header),
            Rule('/cookie', 'cookie'),
            Endpoint('cookie', dummy_cookie),
        )))

        self.header(app, start_response)
        self.cookie(app, start_response)


def response_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_url_file',
            'test_url_for',
            'test_file',
            'test_redirect',
            'test_headers',
    ):
        suite.addTest(TestModule(test))

    return suite
