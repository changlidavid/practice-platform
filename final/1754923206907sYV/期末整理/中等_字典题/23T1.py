# Given a dictionary D and a key x, there is a (unique) loop
# containing x if there are keys x_1, ..., x_k such that:
# D maps x to x_1
# D maps x_1 to x_2
# ...
# D maps x_{k-1} to x_k
# x_1, ..., x_{k-1} are all different to x and x_k is x
# (in the particular case where k = 1, D maps x to x).
#
# When the loop does not exist, the function prints out nothing.
# When the loop exists, the function prints out the loop,
# STARTING AND ENDING with the SMALLEST element in the loop.
#
# You can assume that the function is called with as first argument,
# a dictionary having nothing but integers as keys and values,
# and with as second argument, an integer.


def loop(D, x):
    '''
    >>> loop({1: 1}, 0)
    >>> loop({1: 2, 2: 2}, 1)
    >>> loop({1: 2, 2: 3}, 1)
    >>> loop({1: 2, 2: 3, 3: 2}, 1)
    >>> loop({1: 1}, 1)    
    1--1
    >>> loop({1: 2, 2: 1}, 2)
    1--2--1
    >>> loop({12: 14, 13: 14, 14: 7, 7: 12, 6: 8, 8: 6, 5: 11}, 14)
    7--12--14--7
    >>> loop({0: 4, 1: 0, 2: 1, 3: 2, 4: 7, 5: 6, 6: 4, 7: 0, 8: 8, 9: 4}, 4)
    0--4--7--0
    >>> loop({0: 7, 1: 7, 2: 3, 3: 8, 4: 6, 5: 8, 6: 6, 7: 4, 8: 9, 9: 2}, 8)
    2--3--8--9--2
    '''
    Dict = D
    array = []
    if x in Dict.keys():
        array.append(str(x))
        temp = Dict[x]
        while temp in Dict.keys():
            if temp == x:
                array.append(str(x))
                array.append(str(Dict[x]))
                break
            if str(temp) in array:
                break
            array.append(str(temp))
            temp = Dict[temp]
    mini = 9999999
    for item in array:
        if mini > int(item):
            mini = int(item)
    x = mini
    array = []
    if x in Dict.keys():
        temp = Dict[x]
        array.append(str(x))
        while temp in Dict.keys():
            if temp == x:
                array.append(str(x))
                print("--".join(array))
                break
            if str(temp) in array:
                break
            array.append(str(temp))
            temp = Dict[temp]


if __name__ == '__main__':
    import doctest

    doctest.testmod()
