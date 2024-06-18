import re
from collections.abc import Callable


class Rule(object):
    __slots__ = ('path', 'link', 'patterns')

    def __init__(self, path: str, link: str, patterns: dict[str, tuple[int, str]] = None):
        for attr, value in (
                ('path', path),
                ('link', link),
                ('patterns', dict() if patterns is None else patterns),
        ):
            setattr(self, attr, value)


class Endpoint(object):
    __slots__ = ('link', 'module', 'name', 'method', 'args')

    def __init__(self, link: str, endpoint: Callable | tuple[Callable] | tuple[Callable, str], *args):
        if isinstance(obj := endpoint, tuple):
            obj, method = obj[0], obj[1] if 2 == len(obj) else '__call__'

        else:
            method = '__call__' if isinstance(obj, type) else None

        for attr, value in (
                ('link', link),
                ('module', obj.__module__),
                ('name', obj.__name__),
                ('method', method),
                ('args', args),
        ):
            setattr(self, attr, value)


class Map(object):
    __slots__ = ('link', 'mapped', 'callback')

    def __init__(self, rules: tuple[Rule | Endpoint, ...]):
        def generator():
            return (getattr(line, a) for a in line.__slots__)

        for attr in ('link', 'mapped', 'callback'):
            setattr(self, attr, dict())

        for line in rules:
            match line.__class__.__name__:
                case 'Rule':
                    self.rule(*generator())

                case 'Endpoint':
                    link, module, name, method, args = generator()

                    if link in self.callback.keys():
                        raise ValueError("URL Map. Endpoint. Link already exists in endpoint list: '%s'." % link)

                    self.callback[link] = module, name, method, args

    def rule(self, path: str, link: str, patterns: dict[str, str]):
        def msg(message: str, *args):
            if args:
                message = message % args

            return ValueError(f"URL Map. Rule. {message}.")

        if '' == path:
            raise msg('Path must not be an empty string')

        if not path.startswith('/'):
            raise msg("Path must start slash: '%s'", path)

        raw_path, pattern, keys, types = path, f"^{path}$", tuple(), tuple()

        for key in re.findall(r'<([A-Za-z0-9:_,()]+)>', path):
            if 1 < len(s := str(key).split(':', 1)):
                (raw_flag, key), replace = s, key

                if 'int' == raw_flag:
                    flag, value = 1, r'\d+'

                elif r := re.findall(r'^int\(([0-9,]+)\)$', raw_flag):
                    if (
                            2 > r[0].count(',') and
                            (s := re.search(r'^(\d+,\d+)|(\d+,)|(\d+)|(,\d+)$', r[0]))
                    ):
                        if '1' == (g := s.group()):
                            value = r'\d'

                        else:
                            value = r'\d{%s}' % g

                        flag, raw_flag = 1, 'int'

                    else:
                        raise msg("Path token 'int' format error: int(%s)", r[0])

                else:
                    flag, value = 2, r'\d+\.\d+'

                if raw_flag not in ('int', 'float'):
                    raise msg("Path token has an invalid flag: '%s'", replace)

                path = path.replace(f"<{replace}>", f"<{key}>")
                pattern = pattern.replace(f"<{replace}>", f"({value})")

            else:
                token = patterns.pop(key, None)

                if token is None:
                    flag, value = 0, r'[A-Za-z0-9_-]+'

                else:
                    flag, value = token

                if flag not in (0, 1, 2):
                    raise msg("The added token has an invalid type flag: (%s, '%s')", flag, value)

                pattern = pattern.replace(f"<{key}>", f"({value})")

            keys = (*keys, key)
            types = (*types, (flag, key))

        if {} != patterns:
            raise msg('Patterns added to rules have unused values: %s', patterns)

        if pattern in self.mapped.keys():
            raise msg("Path already exists in pattern list: '%s'", raw_path)

        if link in self.link.keys():
            self.link[link] = (*self.link[link], (pattern, path, keys))

        else:
            self.link[link] = ((pattern, path, keys),)

        self.mapped[pattern] = link, types


class Path(object):
    __slots__ = ('__token',)

    def __init__(self, tokens: dict[str, str | int | float]):
        self.__token = tokens

    def __getitem__(self, key: str):
        return self.__token[key]

    def __repr__(self):
        return self.__token.__repr__()

    def get(self, key: str):
        return self.__token.get(key)
