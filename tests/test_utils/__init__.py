import unittest


def utils_tests():
    from .test_utc import utc_tests

    suite = unittest.TestSuite()
    suite.addTests(utc_tests())

    return suite
