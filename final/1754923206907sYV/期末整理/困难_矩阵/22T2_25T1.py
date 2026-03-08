# Exploration proceeds horizontally and vertically (not diagonally).
#
# The coordinate system is the usual one mathematically:
# - x is for the horizontal coordinate, ranging between 1 and size
#   moving from left to right;
# - y is for the vertical coordinate, ranging between 1 and size
#   moving from bottom to top.
#
# <BLANKLINE> is not output by the program, but
# doctest's way to refer to an empty line
# (here, output by the print() statement in the stub).
#
# You can assume that f is called with for_seed and density two integers,
# size an integer at least equal to 1, and x and y two integers between
# 1 and size included.
import copy
from random import seed, random

all_point = []


def display(grid):
    for row in grid:
        print(''.join(e and '\N{Black large square}'
                      or '\N{White large square}'
                      for e in row
                      )
              )


def f(for_seed, density, size, x, y):
    '''
    >>> f(3, 0.65, 10, 1, 1)
    ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛
    ⬜⬛⬜⬛⬛⬛⬛⬜⬛⬜
    ⬜⬛⬜⬛⬛⬛⬜⬛⬜⬜
    ⬜⬜⬛⬜⬛⬜⬜⬛⬛⬛
    ⬜⬛⬛⬛⬛⬛⬛⬛⬛⬜
    ⬜⬜⬜⬜⬜⬛⬜⬜⬜⬛
    ⬜⬛⬜⬛⬛⬛⬜⬜⬛⬜
    ⬛⬛⬛⬜⬜⬛⬛⬛⬜⬛
    ⬜⬜⬛⬜⬛⬛⬛⬛⬛⬛
    ⬛⬛⬛⬜⬛⬜⬜⬛⬛⬛
    <BLANKLINE>
    ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛
    ⬜⬛⬜⬛⬛⬛⬛⬜⬛⬜
    ⬜⬛⬜⬛⬛⬛⬜⬛⬜⬜
    ⬜⬜⬛⬜⬛⬜⬜⬛⬛⬛
    ⬜⬛⬛⬛⬛⬛⬛⬛⬛⬜
    ⬜⬜⬜⬜⬜⬛⬜⬜⬜⬛
    ⬜🔵⬜⬛⬛⬛⬜⬜⬛⬜
    🔵🔵🔵⬜⬜⬛⬛⬛⬜⬛
    ⬜⬜🔵⬜⬛⬛⬛⬛⬛⬛
    🔴🔵🔵⬜⬛⬜⬜⬛⬛⬛
    >>> f(3, 0.65, 10, 1, 10)
    ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛
    ⬜⬛⬜⬛⬛⬛⬛⬜⬛⬜
    ⬜⬛⬜⬛⬛⬛⬜⬛⬜⬜
    ⬜⬜⬛⬜⬛⬜⬜⬛⬛⬛
    ⬜⬛⬛⬛⬛⬛⬛⬛⬛⬜
    ⬜⬜⬜⬜⬜⬛⬜⬜⬜⬛
    ⬜⬛⬜⬛⬛⬛⬜⬜⬛⬜
    ⬛⬛⬛⬜⬜⬛⬛⬛⬜⬛
    ⬜⬜⬛⬜⬛⬛⬛⬛⬛⬛
    ⬛⬛⬛⬜⬛⬜⬜⬛⬛⬛
    <BLANKLINE>
    🔴🔵🔵🔵🔵🔵🔵⬜⬛⬛
    ⬜🔵⬜🔵🔵🔵🔵⬜⬛⬜
    ⬜🔵⬜🔵🔵🔵⬜🔵⬜⬜
    ⬜⬜🔵⬜🔵⬜⬜🔵🔵🔵
    ⬜🔵🔵🔵🔵🔵🔵🔵🔵⬜
    ⬜⬜⬜⬜⬜🔵⬜⬜⬜⬛
    ⬜⬛⬜🔵🔵🔵⬜⬜⬛⬜
    ⬛⬛⬛⬜⬜🔵🔵🔵⬜🔵
    ⬜⬜⬛⬜🔵🔵🔵🔵🔵🔵
    ⬛⬛⬛⬜🔵⬜⬜🔵🔵🔵
    >>> f(3, 0.65, 10, 10, 1)
    ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛
    ⬜⬛⬜⬛⬛⬛⬛⬜⬛⬜
    ⬜⬛⬜⬛⬛⬛⬜⬛⬜⬜
    ⬜⬜⬛⬜⬛⬜⬜⬛⬛⬛
    ⬜⬛⬛⬛⬛⬛⬛⬛⬛⬜
    ⬜⬜⬜⬜⬜⬛⬜⬜⬜⬛
    ⬜⬛⬜⬛⬛⬛⬜⬜⬛⬜
    ⬛⬛⬛⬜⬜⬛⬛⬛⬜⬛
    ⬜⬜⬛⬜⬛⬛⬛⬛⬛⬛
    ⬛⬛⬛⬜⬛⬜⬜⬛⬛⬛
    <BLANKLINE>
    🔵🔵🔵🔵🔵🔵🔵⬜⬛⬛
    ⬜🔵⬜🔵🔵🔵🔵⬜⬛⬜
    ⬜🔵⬜🔵🔵🔵⬜🔵⬜⬜
    ⬜⬜🔵⬜🔵⬜⬜🔵🔵🔵
    ⬜🔵🔵🔵🔵🔵🔵🔵🔵⬜
    ⬜⬜⬜⬜⬜🔵⬜⬜⬜⬛
    ⬜⬛⬜🔵🔵🔵⬜⬜⬛⬜
    ⬛⬛⬛⬜⬜🔵🔵🔵⬜🔵
    ⬜⬜⬛⬜🔵🔵🔵🔵🔵🔵
    ⬛⬛⬛⬜🔵⬜⬜🔵🔵🔴
    >>> f(3, 0.65, 10, 10, 10)
    ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛
    ⬜⬛⬜⬛⬛⬛⬛⬜⬛⬜
    ⬜⬛⬜⬛⬛⬛⬜⬛⬜⬜
    ⬜⬜⬛⬜⬛⬜⬜⬛⬛⬛
    ⬜⬛⬛⬛⬛⬛⬛⬛⬛⬜
    ⬜⬜⬜⬜⬜⬛⬜⬜⬜⬛
    ⬜⬛⬜⬛⬛⬛⬜⬜⬛⬜
    ⬛⬛⬛⬜⬜⬛⬛⬛⬜⬛
    ⬜⬜⬛⬜⬛⬛⬛⬛⬛⬛
    ⬛⬛⬛⬜⬛⬜⬜⬛⬛⬛
    <BLANKLINE>
    ⬛⬛⬛⬛⬛⬛⬛⬜🔵🔴
    ⬜⬛⬜⬛⬛⬛⬛⬜🔵⬜
    ⬜⬛⬜⬛⬛⬛⬜⬛⬜⬜
    ⬜⬜⬛⬜⬛⬜⬜⬛⬛⬛
    ⬜⬛⬛⬛⬛⬛⬛⬛⬛⬜
    ⬜⬜⬜⬜⬜⬛⬜⬜⬜⬛
    ⬜⬛⬜⬛⬛⬛⬜⬜⬛⬜
    ⬛⬛⬛⬜⬜⬛⬛⬛⬜⬛
    ⬜⬜⬛⬜⬛⬛⬛⬛⬛⬛
    ⬛⬛⬛⬜⬛⬜⬜⬛⬛⬛
    >>> f(3, 0.65, 10, 7, 5)
    ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛
    ⬜⬛⬜⬛⬛⬛⬛⬜⬛⬜
    ⬜⬛⬜⬛⬛⬛⬜⬛⬜⬜
    ⬜⬜⬛⬜⬛⬜⬜⬛⬛⬛
    ⬜⬛⬛⬛⬛⬛⬛⬛⬛⬜
    ⬜⬜⬜⬜⬜⬛⬜⬜⬜⬛
    ⬜⬛⬜⬛⬛⬛⬜⬜⬛⬜
    ⬛⬛⬛⬜⬜⬛⬛⬛⬜⬛
    ⬜⬜⬛⬜⬛⬛⬛⬛⬛⬛
    ⬛⬛⬛⬜⬛⬜⬜⬛⬛⬛
    <BLANKLINE>
    ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛
    ⬜⬛⬜⬛⬛⬛⬛⬜⬛⬜
    ⬜⬛⬜⬛⬛⬛⬜⬛⬜⬜
    ⬜⬜⬛⬜⬛⬜⬜⬛⬛⬛
    ⬜⬛⬛⬛⬛⬛⬛⬛⬛⬜
    ⬜⬜⬜⬜⬜⬛⬜⬜⬜⬛
    ⬜⬛⬜⬛⬛⬛⬜⬜⬛⬜
    ⬛⬛⬛⬜⬜⬛⬛⬛⬜⬛
    ⬜⬜⬛⬜⬛⬛⬛⬛⬛⬛
    ⬛⬛⬛⬜⬛⬜⬜⬛⬛⬛
    >>> f(5, 0.4, 10, 1, 3)
    ⬜⬜⬜⬜⬜⬜⬛⬜⬜⬜
    ⬜⬛⬜⬛⬜⬜⬛⬛⬛⬜
    ⬜⬛⬜⬛⬜⬛⬛⬜⬛⬛
    ⬜⬜⬛⬜⬜⬜⬛⬜⬜⬜
    ⬜⬛⬛⬛⬛⬛⬛⬜⬛⬜
    ⬛⬛⬜⬜⬛⬜⬜⬛⬜⬛
    ⬜⬜⬛⬜⬛⬜⬛⬛⬛⬜
    ⬛⬜⬜⬜⬛⬛⬜⬜⬛⬜
    ⬜⬜⬛⬜⬛⬛⬜⬜⬛⬜
    ⬜⬛⬛⬛⬛⬛⬜⬜⬛⬛
    <BLANKLINE>
    ⬜⬜⬜⬜⬜⬜⬛⬜⬜⬜
    ⬜⬛⬜⬛⬜⬜⬛⬛⬛⬜
    ⬜⬛⬜⬛⬜⬛⬛⬜⬛⬛
    ⬜⬜⬛⬜⬜⬜⬛⬜⬜⬜
    ⬜⬛⬛⬛⬛⬛⬛⬜⬛⬜
    ⬛⬛⬜⬜⬛⬜⬜⬛⬜⬛
    ⬜⬜⬛⬜⬛⬜⬛⬛⬛⬜
    🔴⬜⬜⬜⬛⬛⬜⬜⬛⬜
    ⬜⬜⬛⬜⬛⬛⬜⬜⬛⬜
    ⬜⬛⬛⬛⬛⬛⬜⬜⬛⬛
    >>> f(5, 0.4, 10, 3, 7)
    ⬜⬜⬜⬜⬜⬜⬛⬜⬜⬜
    ⬜⬛⬜⬛⬜⬜⬛⬛⬛⬜
    ⬜⬛⬜⬛⬜⬛⬛⬜⬛⬛
    ⬜⬜⬛⬜⬜⬜⬛⬜⬜⬜
    ⬜⬛⬛⬛⬛⬛⬛⬜⬛⬜
    ⬛⬛⬜⬜⬛⬜⬜⬛⬜⬛
    ⬜⬜⬛⬜⬛⬜⬛⬛⬛⬜
    ⬛⬜⬜⬜⬛⬛⬜⬜⬛⬜
    ⬜⬜⬛⬜⬛⬛⬜⬜⬛⬜
    ⬜⬛⬛⬛⬛⬛⬜⬜⬛⬛
    <BLANKLINE>
    ⬜⬜⬜⬜⬜⬜🔵⬜⬜⬜
    ⬜⬛⬜⬛⬜⬜🔵🔵🔵⬜
    ⬜⬛⬜⬛⬜🔵🔵⬜🔵🔵
    ⬜⬜🔴⬜⬜⬜🔵⬜⬜⬜
    ⬜🔵🔵🔵🔵🔵🔵⬜⬛⬜
    🔵🔵⬜⬜🔵⬜⬜⬛⬜⬛
    ⬜⬜⬛⬜🔵⬜⬛⬛⬛⬜
    ⬛⬜⬜⬜🔵🔵⬜⬜⬛⬜
    ⬜⬜🔵⬜🔵🔵⬜⬜⬛⬜
    ⬜🔵🔵🔵🔵🔵⬜⬜⬛⬛
    '''
    seed(for_seed)
    grid = [[random() < density for _ in range(size)]
            for _ in range(size)
            ]
    display(grid)
    print()
    visited = set()
    start = x, y
    # CHANGE THE PREVIOUS ASSIGNMENT SO grid[start[0]][start[1]]
    # IS WHERE EXPLORATION STARTS FROM.
    # (That way, you can just use grid[i][j] without having to bother
    # what the coordinate system happens to be.)
    

    # REPLACE THE PASS STATEMENT ABOVE WITH YOUR CODE
    # It involves (as possible ways to denote the appropriate
    # Unicode characters):
    # - '\N{Large red circle}'
    # - '\N{Large blue circle}'


if __name__ == '__main__':
    import doctest

    doctest.testmod()
