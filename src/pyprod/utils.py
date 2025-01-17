from collections.abc import Iterable


def flatten(seq, ignore_none=True):
    if isinstance(seq, str) or (not isinstance(seq, Iterable)):
        yield seq
        return

    for item in seq:
        if isinstance(item, str) or (not isinstance(item, Iterable)):
            if ignore_none and (item is None):
                continue
            yield item
        else:
            yield from flatten(item)


def unique_list(lst):
    return list({e: None for e in lst}.keys())
