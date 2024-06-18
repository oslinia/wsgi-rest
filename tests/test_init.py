import unittest

from framework import Framework
from framework.service import static


class TestModule(unittest.TestCase):
    def test(self):
        self.assertTupleEqual((1, 0, 0), (fw := Framework()).version)
        self.assertDictEqual(dict(), fw.mapped)
        self.assertDictEqual(dict(), fw.callback)

        self.assertEqual('/', static.urlpath)
        self.assertDictEqual(dict(), static.link)


def init_tests():
    suite = unittest.TestSuite()

    for test in (
            'test',
    ):
        suite.addTest(TestModule(test))

    return suite
