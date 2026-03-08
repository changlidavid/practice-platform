'''
Will be tested with n at least equal to 2, and "not too large".
'''
from math import sqrt
from collections import defaultdict
def all_prime2(n):
    all_num = list(range(2, n + 1))
    cheng_less_f = 0
    while all_num[cheng_less_f] <= round(sqrt(n)):
        all_num_set = set(all_num)
        cheng2 = 0
        while True:
            not_prime = all_num[cheng_less_f] * all_num[cheng_less_f + cheng2]
            if not_prime > n:
                break
            all_num_set.remove(not_prime)
            cheng2 += 1
        all_num = sorted(all_num_set)
        cheng_less_f += 1
    return all_num


def f(n):
    '''
    >>> f(2)
    The decomposition of 2 into prime factors reads:
       2 = 2
    >>> f(3)
    The decomposition of 3 into prime factors reads:
       3 = 3
    >>> f(4)
    The decomposition of 4 into prime factors reads:
       4 = 2^2
    >>> f(5)
    The decomposition of 5 into prime factors reads:
       5 = 5
    >>> f(6)
    The decomposition of 6 into prime factors reads:
       6 = 2 x 3
    >>> f(8)
    The decomposition of 8 into prime factors reads:
       8 = 2^3
    >>> f(10)
    The decomposition of 10 into prime factors reads:
       10 = 2 x 5
    >>> f(15)
    The decomposition of 15 into prime factors reads:
       15 = 3 x 5
    >>> f(100)
    The decomposition of 100 into prime factors reads:
       100 = 2^2 x 5^2
    >>> f(5432)
    The decomposition of 5432 into prime factors reads:
       5432 = 2^3 x 7 x 97
    >>> f(45103)
    The decomposition of 45103 into prime factors reads:
       45103 = 23 x 37 x 53
    >>> f(45100)
    The decomposition of 45100 into prime factors reads:
       45100 = 2^2 x 5^2 x 11 x 41
    '''
    # Insert your code here
    pass


if __name__ == '__main__':
    import doctest

    doctest.testmod()
