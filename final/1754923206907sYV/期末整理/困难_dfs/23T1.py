# Given two sets sums and summands of integers and an integer a,
# computes the LONGEST lists of the form
# [a, a + n_1, a + n_1 + n_2, ..., a + n_1 + n_2 + ... + n_k]
# such that:
# - a, a + n_1, a + n_1 + n_2, ..., a + n_1 + n_2 + ... + n_k are all in sums;
# - n_1, n_2, ..., n_k are all in summands and DISTINCT.
#
# The code is already written to print out the lists in lexicographic order
# (together with extra information on how they have been obtained).
#
# You can assume that the function is called with sets of integers
# as first two arguments and with an integer as third argument.
import copy

max_len = 0


def dfs(number, cur_n, new_list, sums, temp_result, real_result):
    global max_len

    if number not in sums:
        if temp_result:
            max_len = max(len(temp_result), max_len)
            temp = tuple(temp_result)
            real_result.add(temp)
        return False
    if not new_list:
        temp = tuple(temp_result)
        max_len = max(len(temp_result), max_len)
        real_result.add(temp)
        return False
    if cur_n:
        temp_result.append(cur_n)
    for item in new_list:
        cur_list = copy.deepcopy(new_list)
        cur_list.remove(item)
        dfs(number + item, item, cur_list, sums, temp_result, real_result)
    if cur_n:
        temp_result.remove(cur_n)
    return False


def chains(sums, summands, a):
    """
    >>> chains({}, {1, 2, 3}, 1)
    >>> chains({1, 2, 3}, {}, 4)
    >>> chains({1, 2, 3}, {}, 2)
    [2]
    >>> chains({11, 12, 13, 14, 15, 16}, {1, 2, 3, 4}, 11)
    [11, 12, 14] by successively adding 1, 2
    [11, 12, 15] by successively adding 1, 3
    [11, 12, 16] by successively adding 1, 4
    [11, 13, 14] by successively adding 2, 1
    [11, 13, 16] by successively adding 2, 3
    [11, 14, 15] by successively adding 3, 1
    [11, 14, 16] by successively adding 3, 2
    [11, 15, 16] by successively adding 4, 1
    >>> chains({1, 3, 4, 6, 9, 10, 20}, {-30, 1, 2, 3, 5, 6, 30}, 3)
    [3, 4, 6, 9] by successively adding 1, 2, 3
    >>> chains({10, 12, 13, 14, 16, 21, 26, 36, 37, 38, 50},\
               {2, 4, 7, 10, 16, 20, 100}, 10)
    [10, 12, 16, 26] by successively adding 2, 4, 10
    [10, 12, 16, 36] by successively adding 2, 4, 20
    [10, 14, 16, 26] by successively adding 4, 2, 10
    [10, 14, 16, 36] by successively adding 4, 2, 20
    [10, 14, 21, 37] by successively adding 4, 7, 16
    [10, 26, 36, 38] by successively adding 16, 10, 2
    """
    S = sorted(list(sums))
    T = sorted(list(summands))
    if not S:
        return
    all_sums = set()
    dfs(a, None, T, S, [], all_sums)

    res = []
    for item in all_sums:
        if max_len == len(list(item)):
            res.append(item)
    res.sort()
    for item in res:
        pre_arr = [a]
        initial = a
        aft_arr = []
        for sub_item in item:
            pre_arr.append(initial + sub_item)
            initial += sub_item
            aft_arr.append(str(sub_item))
        if max_len>1:
            print(f'{pre_arr} by successively adding {", ".join(aft_arr)}')
        else:
            print(pre_arr)

if __name__ == "__main__":
    import doctest

    doctest.testmod()
