from collections import defaultdict
from copy import deepcopy

def upp(L):
    """
    Finds all increasing subsequences that start with the first element of the list.

    A subsequence is valid if:
    1. It starts with the first element of L
    2. It has length greater than 1
    3. It is strictly increasing (each element is greater than the previous)
    4. It can skip any elements in the original list

    Args:
        L: A list of integers

    Returns:
        A list of all maximal valid increasing subsequences

    >>> upp([])
    []
    >>> upp([1, 3, 8, 2, 5, 7, 13, 6])
    [[1, 3, 8, 13], [1, 3, 5, 7, 13], [1, 3, 5, 6], [1, 2, 5, 7, 13], [1, 2, 5, 6]]
    >>> upp([2, 3, 1])
    [[2, 3]]
    >>> upp([3, 1, 2])
    []
    >>> upp([1, 9, 2, 8, 3, 7, 4, 6])
    [[1, 9], [1, 2, 8], [1, 2, 3, 7], [1, 2, 3, 4, 6]]
    >>> upp([1, 2, 3, 4, 5, 6, 7, 8])
    [[1, 2, 3, 4, 5, 6, 7, 8]]
    >>> upp([5])
    []
    >>> upp([5, 4, 3, 2, 1])
    []
    >>> upp([10, 20, 30, 25, 15, 5])
    [[10, 20, 30], [10, 20, 25], [10, 15]]
    >>> upp([7, 8, 9, 1, 2, 3])
    [[7, 8, 9]]
    >>> upp([5, 10, 8, 15, 12, 20, 18])
    [[5, 10, 15, 20], [5, 10, 15, 18], [5, 10, 12, 20], [5, 10, 12, 18], [5, 8, 15, 20], [5, 8, 15, 18], [5, 8, 12, 20], [5, 8, 12, 18]]
    >>> upp([100, 50, 101, 52, 102, 54])
    [[100, 101, 102]]
    >>> upp([3, 4, 5, 1, 2, 6])
    [[3, 4, 5, 6]]
    >>> upp([10, 12, 11, 14, 13, 16, 15])
    [[10, 12, 14, 16], [10, 12, 14, 15], [10, 12, 13, 16], [10, 12, 13, 15], [10, 11, 14, 16], [10, 11, 14, 15], [10, 11, 13, 16], [10, 11, 13, 15]]
    >>> upp([5, 6, 7, 1, 2, 3, 4])
    [[5, 6, 7]]
    >>> upp([1, 3, 5, 2, 4, 6])
    [[1, 3, 5, 6], [1, 3, 4, 6], [1, 2, 4, 6]]
    """
    # Your implementation here
    return []

    

if __name__ == "__main__":
   import doctest
   doctest.testmod()
