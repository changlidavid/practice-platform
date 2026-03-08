import sys
from itertools import compress
from math import sqrt

from itertools import chain


# 小于n的素数
def sieve_of_primes_less_to(n):
    # We let primes_sieve encode the sequence
    # (2, 3, 5, 7, 9, 11, ..., n') with n' equal to n if n is odd
    #  and n - 1 is n is even. The index of n' is n_index.
    n = n - 1
    if n < 2:
        return []
    n_index = (n - 1) // 2
    sieve = [True] * (n_index + 1)
    for k in range(1, (round(sqrt(n)) + 1) // 2):
        if sieve[k]:
            # If k is the index of p then
            # 2 * k * (k + 1) is the index of p ** 2;
            # Also, we increment the value by 2p,
            # which corresponds to increasing the index by 2 * k + 1.
            for i in range(2 * k * (k + 1), n_index + 1, 2 * k + 1):
                sieve[i] = False

    while not sieve[-1]:
        sieve.pop()

    return list(chain((2,), (2 * p + 1 for p in range(1, len(sieve)) if sieve[p])))


def f(a, b):
    '''
    The prime numbers between 2 and 12 (both included) are: 2, 3, 5, 7, 11
    The gaps between successive primes are: 0, 1, 1, 3.
    Hence the maximum gap is 3.
    
    Won't be tested for b greater than 10_000_000
    
    >>> f(3, 3)
    The maximum gap between successive prime numbers in that interval is 0
    >>> f(3, 4)
    The maximum gap between successive prime numbers in that interval is 0
    >>> f(3, 5)
    The maximum gap between successive prime numbers in that interval is 1
    >>> f(2, 12)
    The maximum gap between successive prime numbers in that interval is 3
    >>> f(5, 23)
    The maximum gap between successive prime numbers in that interval is 3
    >>> f(20, 106)
    The maximum gap between successive prime numbers in that interval is 7
    >>> f(31, 291)
    The maximum gap between successive prime numbers in that interval is 13
    '''
    if a <= 0 or b < a:
        sys.exit()
    max_gap = 0
    # Insert your code here
    pass


if __name__ == '__main__':
    import doctest

    doctest.testmod()
