# 24T3  Q1
def f(start=1, nb_of_terms=1):
    """
    Generates a sequence and its reverse version.
    The sequence begins with the given start value, and each subsequent element
    is formed by adding the current position index to the previous element.

    Parameters:
    start: the initial value of the sequence, defaults to 1
    nb_of_terms: the length of the sequence, defaults to 1

    Returns:
    A tuple pair where the first element is the original sequence (as a tuple)
    and the second element is the reversed sequence (as a tuple)

    Examples:
    >>> f()
    ((1,), (1,))
    >>> f(1, 2)
    ((1, 2), (2, 1))
    >>> f(1, 3)
    ((1, 2, 4), (4, 2, 1))
    >>> f(1, 4)
    ((1, 2, 4, 7), (7, 4, 2, 1))
    >>> f(1, 5)
    ((1, 2, 4, 7, 11), (11, 7, 4, 2, 1))
    >>> f(-10)
    ((-10,), (-10,))
    >>> f(-10, 2)
    ((-10, -9), (-9, -10))
    >>> f(5, 6)
    ((5, 6, 8, 11, 15, 20), (20, 15, 11, 8, 6, 5))
    >>> f(0, 7)
    ((0, 1, 3, 6, 10, 15, 21), (21, 15, 10, 6, 3, 1, 0))
    >>> f(100, 3)
    ((100, 101, 103), (103, 101, 100))
    >>> f(-5, 4)
    ((-5, -4, -2, 1), (1, -2, -4, -5))
    """
    if nb_of_terms == 1:
        return ((start,), (start,))
    else:
        L = [start]
        for i in range(nb_of_terms - 1):
            L.append(L[i] + i + 1)
        t1 = tuple(L)
        t2 = tuple(reversed(L))
        return (t1, t2)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
