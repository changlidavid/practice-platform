# You can assume that the argument to solve() is of the form
# x+y=z where:
# - x, y and z are NONEMPTY sequences of UNDERSCORES and DIGITS;
# - there can be any number of spaces (possibly none) before x,
#   between x and +, between + and y, between y and =, between = and z,
#   and after z.
#
# ALL OCCURRENCES OF _ ARE MEANT TO BE REPLACED BY THE SAME DIGIT.
#
# Note that sequences of digits such as 000 and 00037 represent
# 0 and 37, consistently with what int('000') and int('00037') return,
# respectively.
#
# When there is more than one solution, solutions are output from
# smallest to largest values of _.
#
# Note that an equation is always output with a single space before and after
# + and =, with no leading nor trailing spaces, and without extra leading 0s
# in front of an integer.
#
# Hint: The earlier you process underscores, the easier,
#       and recall what dir(str) can do for you.

# 小规模枚举


def solve(equation):
    """
    >>> solve('1 + 2 = 4')
    No solution!
    >>> solve('123 + 2_4 = 388')
    No solution!
    >>> solve('1+2   =   3')
    1 + 2 = 3
    >>> solve('123 + 2_4 = 387')
    123 + 264 = 387
    >>> solve('_23+234=__257')
    23 + 234 = 257
    >>> solve('   __   +  _____   =     ___    ')
    0 + 0 = 0
    >>> solve('__ + __  = 22')
    11 + 11 = 22
    >>> solve('   012+021   =   00__   ')
    12 + 21 = 33
    >>> solve('_1   +    2   =    __')
    31 + 2 = 33
    >>> solve('0 + _ = _')
    0 + 0 = 0
    0 + 1 = 1
    0 + 2 = 2
    0 + 3 = 3
    0 + 4 = 4
    0 + 5 = 5
    0 + 6 = 6
    0 + 7 = 7
    0 + 8 = 8
    0 + 9 = 9
    """
    # REPLACE PASS ABOVE WITH YOUR CODE
    equation = "".join(equation.split())
    # 拆分 + 拆分出 数字1 = 拆分出 数字2 和数字3
    equation = equation.split("+")
    equation = [equation[0]] + equation[1].split("=")
    if "_" not in "".join(equation):
        try:
            if int(equation[0]) + int(equation[1]) == int(equation[2]):
                print(f"{int(equation[0])} + {int(equation[1])} = {int(equation[2])}")
            else:
                print("No solution!")
        except:
            print("No solution!")
        return
    Flag = False
    for x in range(10):
        res_num1, res_num2, res_res = "", "", ""
        for num1 in range(len(equation[0])):
            if equation[0][num1] == "_":
                res_num1 += str(x)
            else:
                res_num1 += equation[0][num1]

        for num2 in range(len(equation[1])):
            if equation[1][num2] == "_":
                res_num2 += str(x)
            else:
                res_num2 += equation[1][num2]

        for rr in range(len(equation[2])):
            if equation[2][rr] == "_":
                res_res += str(x)
            else:
                res_res += equation[2][rr]
        try:
            if int(res_num1) + int(res_num2) == int(res_res):
                Flag = True
                print(f"{int(res_num1)} + {int(res_num2)} = {int(res_res)}")
        except:
            pass
    if not Flag:
        print("No solution!")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
