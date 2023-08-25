import logging


def range_limit(n, minn: float, maxn: float):
    """Fit a value to a specified range, if applicable"""
    n_range = n

    if any(list(map(lambda x: isinstance(x, str), [n_range, minn, maxn]))):
        logging.critical('Cannot perform range comparison with string-type')

    if n < minn:
        n_range = minn
    if n > maxn:
        n_range = maxn

    return n_range


def in_range(n, minn, maxn):
    if isinstance(minn, float) or isinstance(minn, int):
        if isinstance(maxn, float) or isinstance(maxn, int):
            if n >= minn and n <= maxn:
                return True
            else:
                return False
        else:
            return False
    else:
        return False
