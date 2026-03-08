# Consider a strictly positive integer. Omit all occurrences of 0,
# if any, and write what is left as d_1d_2...d_k.
# Returns the integer consisting of d_2 copies of d_1, followed
# by d_3 copies of d_2, ... followed by d_k copies of d_{k-1},
# followed by d_1 copies of d_k (note that when k = 1, that is
# d_1 copies of d_1).
#
# For instance, if the integer is 40025000170 then removing
# all occurrences of 0, it becomes 42517, and what is returned
# is the integer consisting of
# - 2 copies of 4,
# - followed by 5 copies of 2,
# - followed by 1 copy of 5,
# - followed by 7 copies of 1,
# - followed 4 copies of 7,
# so the integer 4422222511111117777
#
# You can assume that the function is called with a strictly
# positive integer as argument.


def transform(number):
    '''
    >>> transform(1)
    1
    >>> transform(12)
    112
    >>> transform(321)
    332111
    >>> transform(2143)
    2111144433
    >>> transform(3000)
    333
    >>> transform(40025000170)
    4422222511111117777
    '''
    array = str(number)
    result = []
    if len(array) > 0:
        for item in range(0, len(array)):
            if array[item] != '0':
                result.append(int(array[item]))
        if len(result) > 0:
            if len(result) == 1:
                print(int(result[0]) * str(result[0]))
                return
            start = result[0]
            output = ""
            for num in range(len(result) - 1):
                times = result[num + 1]
                output = output + times * str(result[num])
            output = output + start * str(result[-1])
            print(output)
            return


if __name__ == '__main__':
    import doctest

    doctest.testmod()
