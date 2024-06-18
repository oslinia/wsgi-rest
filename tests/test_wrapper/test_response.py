import os
import unittest

from framework.routing import Rule, Endpoint, Map, Path
from framework.service import Service
from framework.wrapper import Response

from .. import dummy, DummyStartResponse
from ..test_http.test_response import Headers

environ, start_response = dict(QUERY_STRING=''), DummyStartResponse()


class DummyMap(Response):
    def dummy_url_file(self, path: Path):
        return self.url_file(path['filename'])

    def dummy_for_index(self):
        return self.url_for('imdex')

    def dummy_url_for(self, section: str, path: Path):
        if value := path.get('float'):
            if (
                    isinstance(value, float) and 3.141592 == value or 3.14 == value and
                    isinstance(path['int'], int) and 1 == path['int'] and
                    isinstance(path['str'], str) and 'str' == path['str']
            ):
                return self.url_for(section, str=path['str'], int=str(path['int']).zfill(3), float=str(value))

        if value := path.get('int'):
            if (
                    isinstance(value, int) and 1 == value and
                    isinstance(path['str'], str) and 'str' == path['str']
            ):
                return self.url_for(section, str=path['str'], int=str(value).zfill(2))

        if value := path.get('str'):
            if isinstance(value, str) and 'str' == value:
                return self.url_for(section, str=value)

    def dummy_file(self, path: Path):
        return self.file(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', path['filename'])))

    def dummy_redirect(self, path: Path):
        url = self.url_for('dummy', dummy=path['redirect'])

        if 0 == path['code']:
            args = url,
        else:
            args = url, path['code']

        return self.redirect(*args)

    def dummy_header(self):
        self.set_header('header', 'header')
        self.set_header('delete', 'delete')
        true = self.has_header('delete')
        value = self.get_header('delete')
        self.delete_header('delete')
        return str((true, value, self.has_header('delete')))

    def dummy_cookie(self):
        self.set_cookie('one', 'one cookie')
        self.set_cookie('two', 'two cookie')
        self.set_cookie('delete', 'delete')
        self.delete_cookie('delete')


class TestModule(Headers):
    def test_url_file(self):
        def response(urlpath: bytes):
            environ['PATH_INFO'] = '/test.file'

            self.assertEqual(urlpath, b''.join(app(environ, start_response)))

        urlmap = Map((
            Rule('/<filename>', 'file', {'filename': (0, r'[a-z.]+')}),
            Endpoint('file', (DummyMap, 'dummy_url_file'))
        ))

        app = Service(urlmap)
        response(b'/test.file')

        app = Service(urlmap, static_urlpath='/path/to/file/')
        response(b'/path/to/file/test.file')

    def test_url_for(self):
        def response(path_info: str):
            environ['PATH_INFO'] = path_info

            self.assertEqual(path_info.encode('ascii'), b''.join(app(environ, start_response)))

        Service()

        self.assertIsNone(DummyMap().dummy_for_index())

        app = Service(Map((
            Rule('/path/<str>', 'path'),
            Rule('/path/<str>/<int(2):int>', 'path'),
            Rule('/path/<str>/<int:int>/<float:float>', 'path'),
            Endpoint('path', (DummyMap, 'dummy_url_for'), 'path'),
            Rule('/token/<str>', 'token',
                 {'str': (0, r'[a-z]+')}),
            Rule('/token/<str>/<int>', 'token',
                 {'str': (0, r'[a-z]+'), 'int': (1, r'\d{2}')}),
            Rule('/token/<str>/<int>/<float>', 'token',
                 {'str': (0, r'[a-z]+'), 'int': (1, r'\d+'), 'float': (2, r'\d\.\d{2}')}),
            Endpoint('token', (DummyMap, 'dummy_url_for'), 'token'),
        )))

        response('/path/str')
        response('/path/str/01')
        response('/path/str/001/3.141592')
        response('/token/str')
        response('/token/str/01')
        response('/token/str/001/3.14')

    def test_file(self):
        def response(path_info: str, body: bytes):
            environ['PATH_INFO'] = path_info

            self.assertEqual(body, b''.join(app(environ, start_response)))

        app = Service(Map((
            Rule('/<filename>', 'file', {'filename': (0, r'[a-z.]+')}),
            Endpoint('file', (DummyMap, 'dummy_file')),
        )))

        response('/file.error', b'File not found')
        self.start_response('14', 'text/plain; charset=utf-8', '404 Not Found')

        response('/file.css', b'* {\r\n    margin: 0;\r\n    padding: 0;\r\n}')
        self.start_response('39', 'text/css; charset=utf-8')

        response('/file.json', b'{\r\n    "none": null\r\n}')
        self.start_response('22', 'application/json')

        response('/file.txt', b'simple text')
        self.start_response('11', 'text/plain; charset=utf-8')

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
        def response(path_info: str, status: str):
            environ['PATH_INFO'] = path_info

            tuple(app(environ, start_response))

            self.assertEqual(start_response.status, status)

            for key, value in start_response.headers:
                if 'location' == key:
                    return value

        app = Service(Map((
            Rule('/<dummy>', 'dummy'),
            Endpoint('dummy', dummy),
            Rule('/<redirect>/<int:code>', 'redirect'),
            Endpoint('redirect', (DummyMap, 'dummy_redirect')),
        )))

        self.assertEqual('/permanently', response('/permanently/301', '301 Moved Permanently'))
        self.assertEqual('/temporarily', response('/temporarily/302', '302 Moved Temporarily'))
        self.assertEqual('/temporary', response('/temporary/0', '307 Temporary Redirect'))
        self.assertEqual('/permanent', response('/permanent/308', '308 Permanent Redirect'))

    def test_headers(self):
        app = Service(Map((
            Rule('/header', 'header'),
            Endpoint('header', (DummyMap, 'dummy_header')),
            Rule('/cookie', 'cookie'),
            Endpoint('cookie', (DummyMap, 'dummy_cookie')),
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
