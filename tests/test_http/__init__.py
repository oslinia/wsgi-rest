import unittest


def http_tests():
    from .test_request import request_tests
    from .test_response import response_tests

    suite = unittest.TestSuite()
    suite.addTests(request_tests())
    suite.addTests(response_tests())

    return suite
