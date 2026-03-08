def chains(L):
    """
    Analyzes the chain relationships in a number by examining which digits follow each digit.
    The number is treated as a circular sequence (the last digit is considered to be
    followed by the first digit).

    For each digit:
    - If it's always followed by the same digit, map it to that single digit
    - If it's followed by different digits in different occurrences, map it to a sorted list of those digits

    Args:
        L: A positive integer

    Returns:
        A dictionary mapping each digit to its following digit(s)

    >>> chains(1)
    {1: 1}
    >>> chains(2121)
    {1: 2, 2: 1}
    >>> chains(1212)
    {1: 2, 2: 1}
    >>> chains(111)
    {1: 1}
    >>> chains(12121)
    {1: [1, 2], 2: 1}
    >>> chains(121213)
    {1: [2, 3], 2: 1, 3: 1}
    >>> chains(123123)
    {1: 2, 2: 3, 3: 1}
    >>> chains(112233)
    {1: [1, 2], 2: [2, 3], 3: [1, 3]}
    >>> chains(12345)
    {1: 2, 2: 3, 3: 4, 4: 5, 5: 1}
    >>> chains(11223344)
    {1: [1, 2], 2: [2, 3], 3: [3, 4], 4: [1, 4]}
    >>> chains(12345123451234512345)
    {1: 2, 2: 3, 3: 4, 4: 5, 5: 1}
    """
    list = [int(i) for i in str(L)]
    a = set(list)
    if len(a) == 1:
        return {list[0]: list[0]}
    else:
        L1 = {}
        for i in a:
            L1[i] = []
        for i in range(1, len(list)):
            if list[i] not in L1[list[i - 1]]:
                L1[list[i - 1]].append(list[i])
            if i == len(list) - 1:
                if list[0] not in L1[list[i]]:
                    L1[list[i]].append(list[0])
                break
        for key, items in L1.items():
            items.sort()
        return {
            key: items if len(items) != 1 else items[0] for key, items in L1.items()
        }


if __name__ == "__main__":
    import doctest

    doctest.testmod()
