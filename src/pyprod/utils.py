from collections.abc import Iterable


def flatten(seq):
    if isinstance(seq, str) or (not isinstance(seq, Iterable)):
        yield seq
        return

    for item in seq:
        if isinstance(item, str) or (not isinstance(item, Iterable)):
            yield item
        else:
            yield from flatten(item)


def unique_list(lst):
    return list({e: None for e in lst}.keys())
