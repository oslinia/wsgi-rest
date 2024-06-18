import unittest
from datetime import datetime

from framework.service import Service
from framework.utils import utc

from .. import DummyStartResponse

start_response = DummyStartResponse()


class TestModule(unittest.TestCase):
    def test(self):
        tuple(Service()(dict(QUERY_STRING=''), start_response))

        self.assertIsInstance(utc.now, datetime)
        self.assertIsInstance(utc.timestamp, float)
        self.assertEqual(utc.timestamp, utc.now.timestamp())


def utc_tests():
    suite = unittest.TestSuite()

    for test in (
            'test',
    ):
        suite.addTest(TestModule(test))

    return suite
