from math import sqrt
import time
from itertools import compress


# You can assume that a is a strictly positive integer;
# b and c are positive integers (possibly equal to 0).
#
# The last test is representative of the most complex kind
# of input that could be used. Of course, comment it out
# if your solution is not efficient enough and you still want
# to know how your code deals with simpler tests.
def sieve_of_primes_up_to(n):
    sieve = [True] * (n + 1)
    for p in range(2, round(sqrt(n)) + 1):
        if sieve[p]:
            for i in range(p * p, n + 1, p):
                sieve[i] = False
    return sieve


def f(a, b, c):
    '''
    >>> f(1, 0, 0)
    Here are, from smallest to largest, all primes of the form 1_0_0:
    >>> f(1, 0, 1)
    Here are, from smallest to largest, all primes of the form 1_0_1:
        11071
        12011
        12041
        12071
        14011
        14051
        14071
        14081
        15031
        15061
        15091
        16061
        16091
        17011
        17021
        17041
        18041
        18061
        19031
        19051
        19081
    >>> f(96, 2, 9)
    Here are, from smallest to largest, all primes of the form 96_2_9:
        963239
        963299
        964219
        964259
        964289
        965249
        967229
        967259
        967289
        968239
        968299
        969239
        969259
    >>> f(12, 34, 67)
    Here are, from smallest to largest, all primes of the form 12_34_67:
        12134467
        12134867
        12234667
        12334867
        12434167
        12534367
        12634967
        12734467
        12734867
    >>> f(9, 99, 999)
    Here are, from smallest to largest, all primes of the form 9_99_999:
        91996999
        92995999
        92996999
        93991999
        94993999
        94996999
        94997999
        98995999
        99991999
        99995999
        99998999
    '''
    print('Here are, from smallest to largest, all primes of the form '
          f'{a}_{b}_{c}:'
          )
    # INSERT YOUR CODE HERE




if __name__ == '__main__':
    import doctest
    doctest.testmod()
