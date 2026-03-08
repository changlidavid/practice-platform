# 24T3  Q3
def f(n):
    """
    Removes all even digits from a number, preserving the sign of the original number.
    If the result has no digits (all were even), returns 0.

    Args:
        n: An integer

    Returns:
        An integer with all even digits of n removed

    >>> f(-12345667)
    -1357
    >>> f(0)
    0
    >>> f(1)
    1
    >>> f(12334503)
    13353
    >>> f(2468)
    0
    >>> f(-2468)
    0
    >>> f(123456789)
    13579
    >>> f(-987654321)
    -97531
    >>> f(10203040)
    13
    >>> f(9876543210)
    97531
    """
    if n == 0:
        return 0
    elif n % 2 != 0 and len(str(n)) == 1:
        return n
    else:
        L = []
        for i in str(abs(n)):
            L.append(i)
        L1 = []
        for i in L:
            if int(i) % 2 != 0:
                L1.append(i)
        if len(L1) == 0:
            return 0
        num = int("".join(L1))
        if n > 0:
            return num
        else:
            return -num


if __name__ == "__main__":
    import doctest

    doctest.testmod()
