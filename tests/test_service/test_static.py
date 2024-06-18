import unittest

from framework.routing import Rule, Endpoint, Map, Path
from framework.service import static, Service

from .. import DummyStartResponse

start_response = DummyStartResponse()


def dummy_urlpath(name: str):
    return f"{static.urlpath}{name}"


def dummy_link(path: Path):
    return (f"{static.link.collect(('urlpath',), {})}\n"
            f"{static.link.collect(('link',), {'name': path['name']})}")


class TestModule(unittest.TestCase):
    def test_urlpath(self):
        Service()

        self.assertEqual('/', static.urlpath)

        Service(static_urlpath='/path/to/file/')

        self.assertEqual('/path/to/file/', static.urlpath)

        with self.assertRaises(ValueError) as context:
            Service(static_urlpath='')

        self.assertEqual(
            "URL for static files cannot be empty.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Service(static_urlpath='slash/')

        self.assertEqual(
            "URL for static files must begin with a slash 'slash/'.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Service(static_urlpath='/slash')

        self.assertEqual(
            "URL for static files must end with a slash '/slash'.",
            context.exception.args[0],
        )

    def test_link(self):
        def response(path_info: str):
            environ['PATH_INFO'] = path_info

            return b''.join(app(environ, start_response))

        app, environ = Service(Map((
            Rule('/', 'urlpath'),
            Endpoint('urlpath', dummy_urlpath, 'style.css'),
            Rule('/link/<name>', 'link', {'name': (0, r'[a-z.]+')}),
            Endpoint('link', dummy_link),
        ))), dict(QUERY_STRING='')

        self.assertEqual(b'/style.css', response('/'))
        self.assertEqual(b'/\n/link/test.html', response('/link/test.html'))


def static_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_urlpath',
            'test_link',
    ):
        suite.addTest(TestModule(test))

    return suite
