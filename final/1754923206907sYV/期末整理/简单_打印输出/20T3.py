# ord(c) returns the encoding of character c.
# chr(e) returns the character encoded by e.


def rectangle(width, height):
    """
    Displays a rectangle by outputting lowercase letters, starting with a,
    in a "snakelike" manner, from left to right, then from right to left,
    then from left to right, then from right to left, wrapping around when z is reached.

    >>> rectangle(1, 1)
    a
    >>> rectangle(2, 3)
    ab
    dc
    ef
    >>> rectangle(3, 2)
    abc
    fed
    >>> rectangle(17, 4)
    abcdefghijklmnopq
    hgfedcbazyxwvutsr
    ijklmnopqrstuvwxy
    ponmlkjihgfedcbaz
    """
    L = [["" for i in range(width)] for j in range(height)]
    letter = [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
    ]
    a = 0
    for i in range(height):
        for j in range(width):
            if i % 2 == 0:
                L[i][j] = letter[a % 26]
            else:
                L[i][width - j - 1] = letter[a % 26]
            a += 1
    for i in range(height):
        for j in range(width):
            print(L[i][j], end="")
        print()
    # REPLACE THE PREVIOUS LINE WITH YOUR CODE
    pass


if __name__ == "__main__":
    import doctest

    doctest.testmod()
