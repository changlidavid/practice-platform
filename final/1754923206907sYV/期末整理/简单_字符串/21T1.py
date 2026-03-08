# The input, n, is a string consisting of a succession of positive integers
# (0 is a positive integer) followed by one of either o, for 0, or i, for 1;
# the integer indicates how many times what follows is to be repeated.
#
# There is no space anywhere.
#
# You can assume that at least one number is strictly positive, so n
# properly represents a (unique) number in base 2.
#
# You can import the re module. It has not been imported because the
# simplest solution is... very simple and makes no use of it.
def f(n):
    """
    >>> f('1o')
    This is a weird way to write 0, which in base 10 is 0.
    >>> f('3o')
    This is a weird way to write 000, which in base 10 is 0.
    >>> f('2o1o')
    This is a weird way to write 000, which in base 10 is 0.
    >>> f('1o0o2o0o0o')
    This is a weird way to write 000, which in base 10 is 0.
    >>> f('1i')
    This is a weird way to write 1, which in base 10 is 1.
    >>> f('1i1o1i1o')
    This is a weird way to write 1010, which in base 10 is 10.
    >>> f('1i1i1i3o2i1i2o')
    This is a weird way to write 11100011100, which in base 10 is 1820.
    >>> f('0o2o3i1i2o0o3o5i0o')
    This is a weird way to write 0011110000011111, which in base 10 is 15391.
    >>> f('13i4o26i')
    This is a weird way to write 1111111111111000011111111111111111111111111, \
which in base 10 is 8795086389247.
    """
    # INSERT YOUR CODE HERE
    number = ""
    result = ""
    for x in range(len(n)):
        if n[x] == "i":
            current_number = int(number)
            result = result + "1" * current_number
            number = ""
            continue
        if n[x] == "o":
            current_number = int(number)
            result = result + "0" * current_number
            number = ""
            continue
        number += n[x]

    print(
        f"This is a weird way to write {result}, which in base 10 is {int(result,2)}."
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
