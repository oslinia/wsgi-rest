from ..routing.urlmap import Link

urlpath: str
link: Link


def valid(url: str | None):
    if url is None:
        url = '/'

    elif '' == url:
        raise ValueError(
            "URL for static files cannot be empty."
        )

    elif not url.startswith('/'):
        raise ValueError(
            "URL for static files must begin with a slash '%s'." % url
        )

    elif not url.endswith('/'):
        raise ValueError(
            "URL for static files must end with a slash '%s'." % url
        )

    return url
