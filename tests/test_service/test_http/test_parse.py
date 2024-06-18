import unittest

from framework.service.http.parse import Query, Cookie


class TestModule(unittest.TestCase):
    def test_query(self):
        environ = dict(QUERY_STRING='')

        self.assertDictEqual({}, Query(environ))

        environ['QUERY_STRING'] = 'one=one%20query&two=two%20query'

        self.assertDictEqual({'one': 'one query', 'two': 'two query'}, Query(environ))

    def test_cookie(self):
        environ = dict()

        self.assertDictEqual({}, Cookie(environ))

        environ['HTTP_COOKIE'] = 'one=one cookie; two=two cookie'

        self.assertDictEqual({'one': 'one cookie', 'two': 'two cookie'}, Cookie(environ))


def parse_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_query',
            'test_cookie',
    ):
        suite.addTest(TestModule(test))

    return suite
