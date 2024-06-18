from framework.utils.alias import StartResponse


def dummy():
    pass


class Dummy:
    def dummy(self):
        pass

    def __call__(self):
        pass


class DummyStartResponse(StartResponse):
    __slots__ = ('status', 'headers')

    def __call__(self, *args):
        self.status, self.headers = args
