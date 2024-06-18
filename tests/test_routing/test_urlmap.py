import unittest

from framework.routing import Rule, Endpoint, Map
from framework.routing.urlmap import Link, Mapped, Callback

from .. import dummy, Dummy


class TestModule(unittest.TestCase):
    def test_map_blank(self):
        urlmap = Map(())

        for model in (Link(urlmap), Mapped(urlmap), Callback(urlmap)):
            self.assertDictEqual({}, model.__dict__)

    def test_rule_path(self):
        urlmap = Map((
            Rule('/', 'index'),
            Endpoint('index', dummy, 'args'),
            Rule('/<name>', 'slug'),
            Endpoint('slug', (Dummy, 'dummy')),
            Rule('/<int:name>', 'int'),
            Endpoint('int', (Dummy, 'dummy')),
            Rule('/<int(2):name>', 'num'),
            Endpoint('num', (Dummy, 'dummy')),
            Rule('/<int(1,2):name>', 'range'),
            Endpoint('range', (Dummy, 'dummy')),
            Rule('/<float:name>', 'float'),
            Endpoint('float', (Dummy, 'dummy')),
        ))

        links = Link(urlmap)

        for link, model in {
            'index': (('^/$', '/', ()),),
            'slug': (('^/([A-Za-z0-9_-]+)$', '/<name>', ('name',)),),
            'int': (('^/(\\d+)$', '/<name>', ('name',)),),
            'num': (('^/(\\d{2})$', '/<name>', ('name',)),),
            'range': (('^/(\\d{1,2})$', '/<name>', ('name',)),),
            'float': (('^/(\\d+\\.\\d+)$', '/<name>', ('name',)),),
        }.items():
            self.assertEqual(model, links[link])

        for args, kwargs in (
                (('/?query=one&two=query', 'index', 'query=one', 'two=query'), {}),
                (('/value?query', 'slug', 'query'), {'name': 'value'}),
                (('/001', 'int'), {'name': '001'}),
                (('/01', 'num'), {'name': '01'}),
                (('/1', 'range'), {'name': '1'}),
                (('/3.14', 'float'), {'name': '3.14'}),
        ):
            self.assertEqual(args[0], links.collect(args[1:], kwargs))

        mapped = Mapped(urlmap)

        for pattern, model in (
                ('^/$', ('index', ())),
                ('^/([A-Za-z0-9_-]+)$', ('slug', ((0, 'name'),))),
                ('^/(\\d+)$', ('int', ((1, 'name'),))),
                ('^/(\\d{2})$', ('num', ((1, 'name'),))),
                ('^/(\\d{1,2})$', ('range', ((1, 'name'),))),
                ('^/(\\d+\\.\\d+)$', ('float', ((2, 'name'),))),
        ):
            self.assertTupleEqual(mapped[pattern], model)

        callback = Callback(urlmap)

        for model, link in (
                (('tests', 'dummy', None, ('args',)), 'index'),
                (('tests', 'Dummy', 'dummy', ()), 'slug'),
                (('tests', 'Dummy', 'dummy', ()), 'int'),
                (('tests', 'Dummy', 'dummy', ()), 'num'),
                (('tests', 'Dummy', 'dummy', ()), 'range'),
                (('tests', 'Dummy', 'dummy', ()), 'float'),
        ):
            self.assertTupleEqual(model, callback[link])

    def test_rule_patterns(self):
        urlmap = Map((
            Rule('/<slug>', 'link',
                 {'slug': (0, r'[a-z]+')}),
            Rule('/<slug>/<int>', 'link',
                 {'slug': (0, r'[a-z]+'), 'int': (1, r'\d{4}')}),
            Rule('/<slug>/<int>/<float>', 'link',
                 {'slug': (0, r'[a-z]+'), 'int': (1, r'\d{4}'), 'float': (2, r'\d{1}\.\d{2}')}),
            Endpoint('link', Dummy, 'args'),
        ))

        links = Link(urlmap)

        for link, model in {
            'link': (
                    ('^/([a-z]+)$', '/<slug>', ('slug',)),
                    ('^/([a-z]+)/(\\d{4})$', '/<slug>/<int>', ('slug', 'int')),
                    ('^/([a-z]+)/(\\d{4})/(\\d{1}\\.\\d{2})$', '/<slug>/<int>/<float>', ('slug', 'int', 'float'))
            )
        }.items():
            self.assertTupleEqual(model, links[link])

        for args, kwargs in (
                (('/slug', 'link'), {'slug': 'slug'}),
                (('/slug/0000', 'link'), {'slug': 'slug', 'int': '0000'}),
                (('/slug/9999/3.14', 'link'), {'slug': 'slug', 'int': '9999', 'float': '3.14'}),
        ):
            self.assertEqual(args[0], links.collect(args[1:], kwargs))

        mapped = Mapped(urlmap)

        for pattern, model in (
                ('^/([a-z]+)$', ('link', ((0, 'slug'),))),
                ('^/([a-z]+)/(\\d{4})$', ('link', ((0, 'slug'), (1, 'int')))),
                ('^/([a-z]+)/(\\d{4})/(\\d{1}\\.\\d{2})$', ('link', ((0, 'slug'), (1, 'int'), (2, 'float')))),
        ):
            self.assertTupleEqual(mapped[pattern], model)

        callback = Callback(urlmap)

        self.assertTupleEqual(callback['link'], ('tests', 'Dummy', '__call__', ('args',)))


def urlmap_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_map_blank',
            'test_rule_path',
            'test_rule_patterns',
    ):
        suite.addTest(TestModule(test))

    return suite
