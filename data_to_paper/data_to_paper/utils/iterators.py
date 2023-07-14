from itertools import zip_longest


def interleave(*iterators):
    """
    interleave([1, 2, 3], [4, 5, 6]) -> [1, 4, 2, 5, 3, 6]
    interleave([1, 2, 3], [4, 5], [7])) -> [1, 4, 7, 2, 5, 3]
    """
    sentinel = object()
    for tuple in zip_longest(*iterators, fillvalue=sentinel):
        for item in tuple:
            if item is not sentinel:
                yield item
