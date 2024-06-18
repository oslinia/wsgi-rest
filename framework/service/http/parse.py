from urllib.parse import unquote

from ...utils.alias import WSGIEnvironment


class Query(dict[str, str]):
    def __init__(self, environ: WSGIEnvironment):
        dict.__init__(self)

        if e := environ['QUERY_STRING']:
            for key, value in (
                    ((v := q.split('=', 1))[0], '' if 1 == len(v) else v[1])
                    for q in unquote(e).split('&')
            ):
                self[key] = value


class Cookie(dict[str, str]):
    def __init__(self, environ: WSGIEnvironment):
        dict.__init__(self)

        if 'HTTP_COOKIE' in environ:
            for key, value in (
                    ((p := i.split('='))[0], p[1])
                    for i in environ['HTTP_COOKIE'].split('; ')
            ):
                self[key] = value


class EnvironParse(object):
    __slots__ = ('query', 'cookie')

    query: Query
    cookie: Cookie

    def __init__(self, environ: WSGIEnvironment):
        self.query = Query(environ)
        self.cookie = Cookie(environ)
