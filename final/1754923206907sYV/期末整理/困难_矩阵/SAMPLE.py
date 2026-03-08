# You can assume that paths() is called with an integer as first
# argument, an integer at least equal to 1 as second argument,
# and integers between 0 and 9 as third and fourth arguments.
#
# A path connects numbers to numbers by moving South,
# South West or South East.
#
# Note that <BLANKLINE> is not output by the program, but
# doctest's way to refer to an empty line
# (here, output by the print() statement in the stub).


from random import seed, randrange

dim = 10


def display(grid):
    print("   ", "-" * (2 * dim + 1))
    for i in range(dim):
        print(
            "   |",
            " ".join(str(j) if grid[i][j] else " " for j in range(dim)),
            end=" |\n",
        )
    print("   ", "-" * (2 * dim + 1))

# 连续的格子有哪些
    # 22T2 DFS Q5
# 所有路径
    # 当前题目
# 最长路径
    # QUIZ 7
    
def dfs(grid, row, col, end_row, end_col, res):
    # 定义方向
    dire = [[1, 0], [1, -1], [1, 1]]
    # 到终点停止
    if (row, col) == (end_row, end_col):
        res.add((row, col))
        return True
    # 确认不越界
    if not (0 <= row < dim and 0 <= col < dim and grid[row][col] == 1):
        return False
    # if abs(col - end_col) > end_row - row:
    #     return False
    # 添加结果
    res.add((row, col))
    # 如果这个格子有任何一条路能到终点 呢么这个格子我们就不删

    flag = False
    # 所有方向进行dfs
    for item in dire:
        nr, nc = row + item[0], col + item[1]
        if dfs(grid, nr, nc, end_row, end_col, res):
            flag = True
    # 否则就要删除
    if not flag:
        res.remove((row, col))
    return flag


def paths(for_seed, density, top, bottom):
    """
    >>> paths(0, 2, 0, 0)
    Here is the grid that has been generated:
        ---------------------
       | 0 1   3 4 5 6 7 8   |
       |   1     4   6     9 |
       | 0   2 3 4   6 7 8   |
       |     2   4 5   7     |
       |       3     6 7   9 |
       | 0   2   4 5   7 8   |
       | 0         5 6       |
       |       3 4     7 8 9 |
       | 0 1   3   5 6       |
       | 0     3   5 6       |
        ---------------------
    <BLANKLINE>
    Here are all paths from 0 at the top to 0 at the bottom:
        ---------------------
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
        ---------------------
    >>> paths(0, 4, 6, 7)
    Here is the grid that has been generated:
        ---------------------
       | 0 1   3 4 5 6 7 8 9 |
       | 0 1 2   4 5 6     9 |
       | 0   2 3 4 5 6 7 8   |
       |     2   4 5 6 7   9 |
       | 0 1 2 3     6 7   9 |
       | 0   2 3 4 5   7 8 9 |
       | 0 1 2 3   5 6     9 |
       | 0     3 4 5 6 7 8 9 |
       | 0 1   3   5 6 7 8   |
       | 0   2 3 4 5 6     9 |
        ---------------------
    <BLANKLINE>
    Here are all paths from 6 at the top to 7 at the bottom:
        ---------------------
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
       |                     |
        ---------------------
    >>> paths(0, 4, 6, 6)
    Here is the grid that has been generated:
        ---------------------
       | 0 1   3 4 5 6 7 8 9 |
       | 0 1 2   4 5 6     9 |
       | 0   2 3 4 5 6 7 8   |
       |     2   4 5 6 7   9 |
       | 0 1 2 3     6 7   9 |
       | 0   2 3 4 5   7 8 9 |
       | 0 1 2 3   5 6     9 |
       | 0     3 4 5 6 7 8 9 |
       | 0 1   3   5 6 7 8   |
       | 0   2 3 4 5 6     9 |
        ---------------------
    <BLANKLINE>
    Here are all paths from 6 at the top to 6 at the bottom:
        ---------------------
       |             6       |
       |           5 6       |
       |         4 5 6 7     |
       |         4 5 6 7     |
       |       3     6 7     |
       |     2 3 4 5   7 8   |
       |       3   5 6     9 |
       |         4 5 6 7 8   |
       |           5 6 7     |
       |             6       |
        ---------------------
    >>> paths(0, 4, 0, 2)
    Here is the grid that has been generated:
        ---------------------
       | 0 1   3 4 5 6 7 8 9 |
       | 0 1 2   4 5 6     9 |
       | 0   2 3 4 5 6 7 8   |
       |     2   4 5 6 7   9 |
       | 0 1 2 3     6 7   9 |
       | 0   2 3 4 5   7 8 9 |
       | 0 1 2 3   5 6     9 |
       | 0     3 4 5 6 7 8 9 |
       | 0 1   3   5 6 7 8   |
       | 0   2 3 4 5 6     9 |
        ---------------------
    <BLANKLINE>
    Here are all paths from 0 at the top to 2 at the bottom:
        ---------------------
       | 0                   |
       |   1                 |
       |     2               |
       |     2               |
       |   1 2 3             |
       | 0   2 3 4           |
       | 0 1 2 3   5         |
       | 0     3 4           |
       |   1   3             |
       |     2               |
        ---------------------
    """
    seed(for_seed)
    grid = [[int(randrange(density) != 0) for _ in range(dim)] for _ in range(dim)]
    print("Here is the grid that has been generated:")
    display(grid)
    # INSERT YOUR CODE HERE
    # for item in grid:
    #     print(item)
    start = (0, top)
    end = (dim - 1, bottom)

    res = set()

    if grid[start[0]][start[1]] == 1 and grid[end[0]][end[1]] == 1:
        dfs(grid, start[0], start[1], end[0], end[1], res)
    ng = []
    for _ in range(dim):
        ng.append([0] * dim)

    if (end[0], end[1]) in res:
        for item in res:
            row, col = item
            ng[row][col] = 1
    grid = ng
    print()
    print(f"Here are all paths from", top, "at the top " "to", bottom, "at the bottom:")
    display(grid)


# POSSIBLY DEFINE EXTRA FUNCTIONS


if __name__ == "__main__":
    import doctest

    doctest.testmod()
