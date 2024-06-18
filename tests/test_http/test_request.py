import unittest

from framework.http import env, query, cookie
from framework.service import http, Service

from .. import DummyStartResponse

app, start_response = Service(), DummyStartResponse()


class TestModule(unittest.TestCase):
    def test_env(self):
        environ = dict(PATH_INFO='', QUERY_STRING='')

        tuple(app(environ, start_response))

        self.assertEqual('', env('PATH_INFO'))
        self.assertEqual('', env('QUERY_STRING'))

        environ['PATH_INFO'] = '/path.info'
        environ['QUERY_STRING'] = 'query=string'

        tuple(app(environ, start_response))

        self.assertEqual('/path.info', env('PATH_INFO'))
        self.assertEqual('query=string', env('QUERY_STRING'))

    def test_query(self):
        environ = dict(QUERY_STRING='')

        tuple(app(environ, start_response))

        self.assertDictEqual({}, http.call.query)

        environ['QUERY_STRING'] = 'query'

        tuple(app(environ, start_response))

        self.assertEqual('', query('query'))

        environ['QUERY_STRING'] = 'one=one%20query&two=two%20query'

        tuple(app(environ, start_response))

        self.assertEqual('one query', query('one'))
        self.assertEqual('two query', query('two'))

    def test_cookie(self):
        environ = dict(QUERY_STRING='')

        tuple(app(environ, start_response))

        self.assertDictEqual({}, http.call.cookie)

        environ['HTTP_COOKIE'] = 'one=one cookie; two=two cookie'

        tuple(app(environ, start_response))

        self.assertEqual('one cookie', cookie('one'))
        self.assertEqual('two cookie', cookie('two'))


def request_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_env',
            'test_query',
            'test_cookie',
    ):
        suite.addTest(TestModule(test))

    return suite
