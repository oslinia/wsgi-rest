import unittest

from tests.test_http import http_tests
from tests.test_routing import routing_tests
from tests.test_service import service_tests
from tests.test_utils import utils_tests
from tests.test_wrapper import wrapper_tests
from tests.test_init import init_tests


def all_test():
    suite = unittest.TestSuite()
    suite.addTests(http_tests())
    suite.addTests(routing_tests())
    suite.addTests(service_tests())
    suite.addTests(utils_tests())
    suite.addTests(wrapper_tests())
    suite.addTests(init_tests())

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(all_test())
