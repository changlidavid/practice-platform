# You can assume that the argument L to positive_gaps()
# is a list of integers.
#
# Records all gaps between two SUCCESSIVE members of L,
# say a and b, such that b is STRICTLY GREATER than a.
#
# Gap values are output from smallest to largest.
#
# For a given gap value, gaps for that value are output
# from smallest to largest starts of gap, without repetition,
# with 2 spaces before "Between".

# 列表和字符串的问题
# 列表处理


from collections import defaultdict


def positive_gaps(L):
    """
    >>> positive_gaps([])
    >>> positive_gaps([2, 2, 2, 1, 1, 0])
    >>> positive_gaps([0, 1, 1, 2, 2, 2])
    Gaps of 1:
      Between 0 and 1
      Between 1 and 2
    >>> positive_gaps([0, 4, 0, 4, 0, 4])
    Gaps of 4:
      Between 0 and 4
    >>> positive_gaps([2, 14, 1, 14, 19, 6, 4, 16, 3, 2])
    Gaps of 5:
      Between 14 and 19
    Gaps of 12:
      Between 2 and 14
      Between 4 and 16
    Gaps of 13:
      Between 1 and 14
    >>> positive_gaps([1, 3, 3, 0, 3, 0, 3, 7, 5, 0, 3, 6, 3, 1, 4])
    Gaps of 2:
      Between 1 and 3
    Gaps of 3:
      Between 0 and 3
      Between 1 and 4
      Between 3 and 6
    Gaps of 4:
      Between 3 and 7
    >>> positive_gaps([11, -10, -9, 11, 15, 8, -5])
    Gaps of 1:
      Between -10 and -9
    Gaps of 4:
      Between 11 and 15
    Gaps of 20:
      Between -9 and 11
    """
    # REPLACE PASS ABOVE WITH YOUR CODE
    if L:
        gap_dict = defaultdict(set)
        processed_L = L + [L[-1]]
        for x in range(len(L)):
            if processed_L[x] < processed_L[x + 1]:
                gap_dict[processed_L[x + 1] - processed_L[x]].add((processed_L[x], processed_L[x + 1]))
        keysss = sorted(list(gap_dict.keys()))
        for item in keysss:
          print(f'Gaps of {item}:')
          for pari in sorted(list(gap_dict[item])):
            print(f'  Between {pari[0]} and {pari[1]}')
        
if __name__ == "__main__":
    import doctest

    doctest.testmod()
