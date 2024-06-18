from ..service import http


def env(name: str):
    return http.environ.get(name)


def query(name: str):
    return http.call.query.get(name)


def cookie(name: str):
    return http.call.cookie.get(name)
