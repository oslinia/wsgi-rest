import unittest
from typing import Any

from framework.routing import Rule, Endpoint, Map, Path

from .. import dummy, Dummy


class TestModule(unittest.TestCase):
    def test_map_blank(self):
        urlmap = Map(())

        for attr in urlmap.__slots__:
            self.assertDictEqual({}, getattr(urlmap, attr))

    def test_rule_path(self):
        def callback(link: str, name: str, method: str | None):
            data: tuple[str, str, str | None, tuple[Any, ...]] = urlmap.callback[link]

            self.assertTupleEqual(('tests', name, method), data[:3])

            return data[3]

        urlmap = Map((
            Rule('/<name>', 'slug'),
            Endpoint('slug', dummy, 'start', 1, True, None, dummy, tuple()),
            Rule('/<int:name>', 'int'),
            Endpoint('int', Dummy),
            Rule('/<int(1):name>', 'one'),
            Endpoint('one', Dummy),
            Rule('/<int(2):name>', 'num'),
            Endpoint('num', Dummy),
            Rule('/<int(1,2):name>', 'range'),
            Endpoint('range', Dummy),
            Rule('/<float:name>', 'float'),
            Endpoint('float', (Dummy,), 'end')
        ))

        for key, model in (
                ('slug', (('^/([A-Za-z0-9_-]+)$', '/<name>', ('name',)),)),
                ('int', (('^/(\\d+)$', '/<name>', ('name',)),)),
                ('one', (('^/(\\d)$', '/<name>', ('name',)),)),
                ('num', (('^/(\\d{2})$', '/<name>', ('name',)),)),
                ('range', (('^/(\\d{1,2})$', '/<name>', ('name',)),)),
                ('float', (('^/(\\d+\\.\\d+)$', '/<name>', ('name',)),)),
        ):
            self.assertTupleEqual(urlmap.link[key], model)

        for key, model in (
                ('^/([A-Za-z0-9_-]+)$', ('slug', ((0, 'name'),))),
                ('^/(\\d+)$', ('int', ((1, 'name'),))),
                ('^/(\\d)$', ('one', ((1, 'name'),))),
                ('^/(\\d{2})$', ('num', ((1, 'name'),))),
                ('^/(\\d{1,2})$', ('range', ((1, 'name'),))),
                ('^/(\\d+\\.\\d+)$', ('float', ((2, 'name'),))),
        ):
            self.assertTupleEqual(urlmap.mapped[key], model)

        args = callback('slug', 'dummy', None)

        self.assertEqual('start', args[0])
        self.assertEqual(1, args[1])
        self.assertTrue(args[2])
        self.assertIsNone(args[3])
        self.assertIsNone(args[4]())
        self.assertTupleEqual(tuple(), args[5])

        self.assertTupleEqual(callback('int', 'Dummy', '__call__'), ())
        self.assertTupleEqual(callback('one', 'Dummy', '__call__'), ())
        self.assertTupleEqual(callback('num', 'Dummy', '__call__'), ())
        self.assertTupleEqual(callback('range', 'Dummy', '__call__'), ())
        self.assertEqual(callback('float', 'Dummy', '__call__')[0], 'end')

    def test_rule_patterns(self):
        urlmap = Map((
            Rule('/<slug>', 'link',
                 {'slug': (0, r'\d{4}')}),
            Rule('/<slug>/<int>', 'link',
                 {'slug': (0, r'\d{4}'), 'int': (1, r'\d{2}')}),
            Rule('/<slug>/<int>/<float>', 'link',
                 {'slug': (0, r'\d{4}'), 'int': (1, r'\d{2}'), 'float': (2, r'\d{1}\.\d{2}')}),
            Endpoint('link', (Dummy, 'dummy'))
        ))

        self.assertTupleEqual(urlmap.link['link'], (
            ('^/(\\d{4})$', '/<slug>', ('slug',)),
            ('^/(\\d{4})/(\\d{2})$', '/<slug>/<int>', ('slug', 'int')),
            ('^/(\\d{4})/(\\d{2})/(\\d{1}\\.\\d{2})$', '/<slug>/<int>/<float>', ('slug', 'int', 'float')),
        ))

        for key, model in (
                ('^/(\\d{4})$', ('link', ((0, 'slug'),))),
                ('^/(\\d{4})/(\\d{2})$', ('link', ((0, 'slug'), (1, 'int')))),
                ('^/(\\d{4})/(\\d{2})/(\\d{1}\\.\\d{2})$', ('link', ((0, 'slug'), (1, 'int'), (2, 'float')))),
        ):
            self.assertTupleEqual(urlmap.mapped[key], model)

        self.assertTupleEqual(urlmap.callback['link'], ('tests', 'Dummy', 'dummy', ()))

    def test_map_raise(self):
        with self.assertRaises(ValueError) as context:
            Map((Rule('', 'link'),))

        self.assertEqual(
            'URL Map. Rule. Path must not be an empty string.',
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('slash', 'link'),))

        self.assertEqual(
            "URL Map. Rule. Path must start slash: 'slash'.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('/<int(1,2,3):name>', 'link'),))

        self.assertEqual(
            "URL Map. Rule. Path token 'int' format error: int(1,2,3).",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('/<error:name>', 'link'),))

        self.assertEqual(
            "URL Map. Rule. Path token has an invalid flag: 'error:name'.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('/<pk>', 'link', {'pk': (3, '\\d{2}')}),))

        self.assertEqual(
            r"URL Map. Rule. The added token has an invalid type flag: (3, '\d{2}').",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('/<int:pk>', 'link', {'pk': (3, '\\d{2}')}),))

        self.assertEqual(
            r"URL Map. Rule. Patterns added to rules have unused values: {'pk': (3, '\\d{2}')}.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Rule('/', 'link'), Rule('/', 'link')))

        self.assertEqual(
            "URL Map. Rule. Path already exists in pattern list: '/'.",
            context.exception.args[0],
        )

        with self.assertRaises(ValueError) as context:
            Map((Endpoint('link', dummy), Endpoint('link', dummy)))

        self.assertEqual(
            "URL Map. Endpoint. Link already exists in endpoint list: 'link'.",
            context.exception.args[0],
        )

    def test_path_token(self):
        path = Path({'str': 'str', 'int': 1, 'float': 0.1})

        self.assertDictEqual({'str': 'str', 'int': 1, 'float': 0.1}, getattr(path, '_Path__token'))
        self.assertEqual('str', path.get('str'))
        self.assertEqual(1, path['int'])
        self.assertEqual(0.1, path['float'])


def routing_tests():
    from .test_urlmap import urlmap_tests

    suite = unittest.TestSuite()
    suite.addTests(urlmap_tests())

    for test in (
            'test_map_blank',
            'test_rule_path',
            'test_rule_patterns',
            'test_map_raise',
            'test_path_token',
    ):
        suite.addTest(TestModule(test))

    return suite
