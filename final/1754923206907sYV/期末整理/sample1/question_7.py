# COMP9021 25T2 - Rachid Hamadi
# Sample Exam Question 7


'''
Will be tested with height a strictly positive integer.
'''


def f(height):
    '''
    >>> f(1)
    0
    >>> f(2)
     0
    123
    >>> f(3)
      0
     123
    45678
    >>> f(4)
       0
      123
     45678
    9012345
    >>> f(5)
        0
       123
      45678
     9012345
    678901234
    >>> f(6)
         0
        123
       45678
      9012345
     678901234
    56789012345
    >>> f(20)
                       0
                      123
                     45678
                    9012345
                   678901234
                  56789012345
                 6789012345678
                901234567890123
               45678901234567890
              1234567890123456789
             012345678901234567890
            12345678901234567890123
           4567890123456789012345678
          901234567890123456789012345
         67890123456789012345678901234
        5678901234567890123456789012345
       678901234567890123456789012345678
      90123456789012345678901234567890123
     4567890123456789012345678901234567890
    123456789012345678901234567890123456789
    '''
    
    # # current = 0
    # # shuzi = '0123456789')
    # #     for j in range(i + i - 1):
    # # for i in range(1, height + 1):
    # #     print(' ' * (height - i), end=''
    # #         print(shuzi[current % len(shuzi)], end='')
    # #         current += 1
    # #     print()
    # #倒放
    # current=0
    # shuzi='123456789'
    # for i in range(height,0,-1):
    #     print(' ' * (height - i), end='')
    #     for j in range(i + i - 1):
    #         print(shuzi[current % len(shuzi)], end='')
    #         current += 1
    #     print()
        



if __name__ == '__main__':
    import doctest
    doctest.testmod()
