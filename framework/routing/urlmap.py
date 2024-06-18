import re
from typing import Any

from . import Map, Path
from ..utils.alias import WSGIEnvironment


class Link(dict[str, tuple[tuple[str, str, tuple[str, ...]], ...]]):
    def __init__(self, urlmap: Map):
        dict.__init__(self)
        dict.update(self, urlmap.link)

    def collect(self, args: tuple[str, ...], kwargs: dict[str, str]):
        def query():
            return f"?{'&'.join(args[1:])}" if 1 < len(args) else ''

        if args[0] in self.keys():
            for pattern, path, keys in self[args[0]]:
                if (i := len(kwargs)) == len(keys):
                    if 0 < i:
                        for key in keys:
                            try:
                                path = path.replace(f"<{key}>", kwargs[key])

                                if hasattr(r := re.match(pattern, path), 'string'):
                                    return f"{r.string}{query()}"

                            except KeyError:
                                pass
                    else:
                        return f"{path}{query()}"


class Mapped(dict[str, tuple[str, tuple[tuple[int, str], ...]]]):
    def __init__(self, urlmap: Map):
        dict.__init__(self)
        dict.update(self, urlmap.mapped)

    def parse(self, environ: WSGIEnvironment):
        link, kwargs = None, dict()

        for pattern, items in self.items():
            if values := re.findall(pattern, environ['PATH_INFO']):
                (link, types), values = items, v if isinstance((v := values[0]), tuple) else (v,)

                if 0 < values.__len__() == types.__len__():
                    tokens, i = dict(), 0

                    for flag, key in types:
                        match flag:
                            case 0:
                                tokens[key] = values[i]

                            case 1:
                                tokens[key] = int(values[i])

                            case 2:
                                tokens[key] = float(values[i])

                        i += 1

                    kwargs['path'] = Path(tokens)

                break

        return link, kwargs


class Callback(dict[str, tuple[str, str, str | None, tuple[Any, ...]]]):
    def __init__(self, urlmap: Map):
        dict.__init__(self)
        dict.update(self, urlmap.callback)
