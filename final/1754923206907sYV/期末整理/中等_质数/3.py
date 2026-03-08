import sys
from math import sqrt
from itertools import compress

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

def f(n):
    '''
    Won't be tested for n greater than 10_000_000
    
    >>> f(3)
    The largest prime strictly smaller than 3 is 2.
    >>> f(10)
    The largest prime strictly smaller than 10 is 7.
    >>> f(20)
    The largest prime strictly smaller than 20 is 19.
    >>> f(210)
    The largest prime strictly smaller than 210 is 199.
    >>> f(1318)
    The largest prime strictly smaller than 1318 is 1307.
    '''
    if n <= 2:
        sys.exit()
    largest_prime_strictly_smaller_than_n = 0
    # Insert your code here
    pass

if __name__ == '__main__':
    import doctest
    doctest.testmod()
