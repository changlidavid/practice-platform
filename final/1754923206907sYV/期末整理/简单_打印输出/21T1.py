# The first argument, rows, is a string consisting of nothing but
# DISTINCT uppercase letters, with an arbitrary number (possibly 0)
# of spaces at the beginning, at the end, and between letters, two
# consecutive letters being separated by at least one space.
#
# The second argument, columns, is a string consisting of nothing but
# (not necessarily distinct) digits, with an arbitrary number (possibly 0)
# of spaces at the beginning, at the end, and between digits, two
# consecutive digits being separated by at least one space.
#
# The number of letters in rows is equal to the number of digits in columns.
# Each letter in rows is associated with the CORRESPONDING digit in columns
# to yield a star in the output.
#
# Note that all lines in the output have the same number of characters
# (click far enough to the right on a line in the docstring to check where
# the line ends), so most lines have trailing spaces.
def f(rows, columns):
    """
    >>> f('  U  ', '8')
       8
    U  *
    >>> f(' B   E ', '  7 3  ')
       3  4  5  6  7
    B              *
    C
    D
    E  *
    >>> f('   G E', '0 0  ')
       0
    E  *
    F
    G  *
    >>> f(' J  L I  E ', '7 4   2 4')
       2  3  4  5  6  7
    E        *
    F
    G
    H
    I  *
    J                 *
    K
    L        *
    >>> f(' B A  C  H    F', ' 7 4 2 4  5  ')
       2  3  4  5  6  7
    A        *
    B                 *
    C  *
    D
    E
    F           *
    G
    H        *
    """
    # 1) 解析并配对（去空格、保持一一对应关系）
    letters = rows.split()  # DISTINCT 大写字母
    digits = [int(x) for x in columns.split()]  # 0~9 数字（可重复）
    mapping = dict(zip(letters, digits))  # letter -> digit

    # 2) 计算行/列范围（连续打印）
    r_min, r_max = min(letters), max(letters)
    c_min, c_max = min(digits), max(digits)

    # 3) 打印列标题（3 个起始空格 + 每列“数字 + 2 空格”）
    header = "   " + "  ".join(str(d) for d in range(c_min, c_max + 1))
    print(header)

    width = len(header)
    base, step = 3, 3  # 第一个列位偏移 3；相邻列相距 3（数字 + 两个空格）

    # 4) 逐行输出：首列放字母；如该字母在映射中，则在对应列放 '*'
    for code in range(ord(r_min), ord(r_max) + 1):
        ch = chr(code)
        line = [" "] * width
        line[0] = ch
        if ch in mapping:
            pos = base + (mapping[ch] - c_min) * step
            if 0 <= pos < width:
                line[pos] = "*"
        print("".join(line).rstrip())


if __name__ == "__main__":
    import doctest

    doctest.testmod()
