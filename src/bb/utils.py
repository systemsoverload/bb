from functools import reduce


def rget(dct, keys, default=None, getter=None):
    """Safe nested dictionary key lookup helper

    >>> dct = {'foo': {'bar': 123}}
    >>> rget(dct, 'foo.bar') == 123
    >>> rget(dct, ['foo', 'bar') == 123
    >>> rget(dct, 'foo.baz', 42) == 42

    :param dct: Dictionary to perform nested .get()'s on
    :param keys: Any iterable or dot separated string of keys to accumlate from
    :default: Default return value when .get()'s fail
    """
    if isinstance(keys, bytes):
        keys = keys.split(b'.')
    elif isinstance(keys, str):
        keys = keys.split('.')

    if getter is None:
        getter = lambda a, i: (a.get(i, default) if hasattr(a, 'get') else default)  # noqa: NVR1 (AUTO)

    return reduce(getter, keys, dct)
