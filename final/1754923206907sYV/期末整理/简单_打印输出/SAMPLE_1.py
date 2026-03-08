# Note that NONE OF THE LINES THAT ARE OUTPUT HAS TRAILING SPACES.
#
# You can assume that vertical_bars() is called with nothing but
# integers at least equal to 0 as arguments (if any).

# 打印输出
# 转换方向 90度 180度 270 度


#
def vertical_bars(*x):
    """
    >>> vertical_bars()
    >>> vertical_bars(0, 0, 0)
    >>> vertical_bars(4)
    *
    *
    *
    *
    >>> vertical_bars(4, 4, 4)
    * * *
    * * *
    * * *
    * * *
    >>> vertical_bars(4, 0, 3, 1)
    *
    *   *
    *   *
    *   * *
    >>> vertical_bars(0, 1, 2, 3, 2, 1, 0, 0)
          *
        * * *
      * * * * *
    """
    # REPLACE PASS ABOVE WITH YOUR CODE
    # 借助二维列表 把要按行打印的东西 存储再二维列表里 行数 列数
    # *
    # *   *
    # *   *
    # *   * *
    if list(x) == []:
        return
    x = list(x)
    max_x = max(x)
    result = []
    for item in x:
        l = ["*"] * item + [" "] * (max_x - item)
        result.append(l)
    for col in range(len(result[0]) - 1, -1, -1):
        result_print = ""
        for row in range(len(result)):
            # result_print.append(result[row][col])
            result_print += result[row][col] + " "
        print(result_print.rstrip())


# vertical_bars(4, 0, 3, 1)
if __name__ == "__main__":
    import doctest

    doctest.testmod()
