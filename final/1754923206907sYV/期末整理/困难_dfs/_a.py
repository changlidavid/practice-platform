# Returns the list of all lists of the form [L[i_0], ..., L[i_k]] such that:
# - i_0 < ... < i_k
# - L[i_0] < ... < L[i_k]
# - there is NO list of the form [L[j_0], ..., L[j_k']] such that:
#   * j_0 < ... < j_k'
#   * L[j_0] < ... < L[j_k']
#   * {i_0, ..., i_k} is a strict subset of {j_0, ..., j_k'}.
#
# The solutions are output in lexicographic order of the associated tuples
# (i_0, ..., i_k).
#
# Will be tested on inputs that, for some of them, are too large for a brute
# force approach to be efficient enough. Think recursively.
#
# You can assume that L is a list of DISTINCT integers.
solutions = []

def f(L):
    '''
    >>> f([3, 2, 1])
    [[3], [2], [1]]
    >>> f([2, 1, 3, 4])
    [[2, 3, 4], [1, 3, 4]]
    >>> f([4, 7, 6, 1, 3, 5, 8, 2])
    [[4, 7, 8], [4, 6, 8], [4, 5, 8], [1, 3, 5, 8], [1, 2]]
    >>> f([3, 4, 6, 10, 2, 7, 1, 5, 8, 9])
    [[3, 4, 6, 10], [3, 4, 6, 7, 8, 9], [3, 4, 5, 8, 9], [2, 7, 8, 9], \
[2, 5, 8, 9], [1, 5, 8, 9]]
    '''
    # INSERT YOUR CODE HERE
    def find_list(list_now):
        global solutions
        num = 0
        slow = 0
        res = [list_now[0]]
        temp = list_now[slow]
        for fast in range(1, len(list_now)):
            if temp < list_now[fast]:
                res.append(list_now[fast])
                temp = list_now[fast]
        solutions.append(res)
        res = []
        for fast in range(1, len(list_now)):
            if list_now[fast - 1] > list_now[fast]:
                next_lis = []
                for num, item in enumerate(list_now):
                    if num != fast - 1:
                        next_lis.append(item)
                find_list(next_lis)
    global solutions
    solutions = []
    find_list(L)
    solutions.sort()
    solutions_dis=[]
    for item in solutions:
        if item not in solutions_dis:
            solutions_dis.append(item)
    solutionss=[]
    maxlen=0
    for item in solutions_dis:
        if len(item)>maxlen:
            maxlen=len(item)
        solutionss.append(set(item))
    maxl=[]
    for item in solutions_dis:
        if maxlen==len(item):
            maxl.append(set(item))
    result_r=[]
    for item in solutionss:
        for items in solutionss:
            if len(item)!=len(items):
                if len(item-items)==0:
                    break
        else:
            result_r.append(item)
    so=[]
    for item in solutions_dis:
        if set(item) in result_r:
            so.append(item)
    print(so[::-1])

# POSSIBLY DEFINE ANOTHER FUNCTION

if __name__ == '__main__':
    import doctest

    doctest.testmod()
