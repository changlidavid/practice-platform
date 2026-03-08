# Q7 DFS/BFS遍历 难度高

from random import seed, randrange


# Generates a grid randomly filled with natural numbers.
# Displays two grids:
# - one with *s at locations with a value v such that
#   at least one of the Northern, Southern, Eastern or Western neighbours
#   has a value that differs from v by at most 1;
# - one which is obtained from the previous one by filling holes with *s.
#
# A hole is defined as any location not occupied by a *
# such such moving horizontally and vertically, one cannot
# reach any of the grid's boundaries.
#
# There can be trailing spaces in the output, but best is to use twice
# the display() function so you can ignore formatting issues.
#
# You can assume that the function is called with 4 integers as arguments.


def display(grid):
    for row in grid:
        print('  ', *row)


def f(for_seed, width, height, upper_bound):
    '''
    >>> f(0, 2, 2, 1)
    Here is the grid:
       0 0
       0 0
    Here are the points with a horizontal or vertical neighbour 
    whose value differs by 1 at most:
       * *
       * *
    And here is the filled picture:
       * *
       * *
    >>> f(0, 3, 3, 4)
    Here is the grid:
       3 3 0
       2 3 3
       2 3 2
    Here are the points with a horizontal or vertical neighbour 
    whose value differs by 1 at most:
       * *  
       * * *
       * * *
    And here is the filled picture:
       * *  
       * * *
       * * *
    >>> f(1, 5, 6, 8)
    Here is the grid:
       2 1 4 1 7
       7 7 6 3 1
       7 0 6 6 0
       7 4 3 1 5
       0 0 0 0 6
       3 6 0 3 7
    Here are the points with a horizontal or vertical neighbour 
    whose value differs by 1 at most:
       * *      
       * * *   *
       *   * * *
       * * * * *
       * * * * *
           *   *
    And here is the filled picture:
       * *      
       * * *   *
       * * * * *
       * * * * *
       * * * * *
           *   *
    >>> f(0, 8, 9, 10)
    Here is the grid:
       6 6 0 4 8 7 6 4
       7 5 9 3 8 2 4 2
       1 9 4 8 9 2 4 1
       1 5 7 8 1 5 6 5
       9 3 8 7 7 8 4 0
       8 0 1 6 0 9 7 5
       3 5 1 3 9 3 3 2
       8 7 1 1 5 8 7 1
       4 8 4 1 8 5 8 3
    Here are the points with a horizontal or vertical neighbour 
    whose value differs by 1 at most:
       * *   * * * *  
       * *   * * * * *
       *     * * * * *
       *   * *   * * *
       *   * * * *    
       * * * *   *    
           *     * * *
       * * * *   * * *
         *   *     *  
    And here is the filled picture:
       * *   * * * *  
       * *   * * * * *
       *     * * * * *
       *   * * * * * *
       *   * * * *    
       * * * *   *    
           *     * * *
       * * * *   * * *
         *   *     *  
    '''
    if width < 2 or height < 2 or upper_bound < 1:
        return
    seed(for_seed)
    grid = [[randrange(upper_bound) for _ in range(width)]
            for _ in range(height)
            ]
    print('Here is the grid:')
    display(grid)
    # INSERT YOUR CODE HERE



if __name__ == '__main__':
    import doctest

    doctest.testmod()
