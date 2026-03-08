# 24T3  Q2
def f(size=2, characters="."):
    """
    >>> f()
    . .
     .
     .
    . .
    >>> f(4,'12345')
    1 2 3 4
     5 1 2
      3 4
       5
       1
      2 3
     4 5 1
    2 3 4 5
    >>> f(3, 'abc')
    a b c
     a b
      c
      a
     b c
    a b c
    >>> f(5, 'xyz')
    x y z x y
     z x y z
      x y z
       x y
        z
        x
       y z
      x y z
     x y z x
    y z x y z
    >>> f(1, '*')
    *
    *
    >>> f(2, 'AB')
    A B
     A
     B
    A B
    >>> f(30, '#')
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
     # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
      # # # # # # # # # # # # # # # # # # # # # # # # # # # #
       # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # # # # # # # # # # # # # # # # # # # # # # # # # #
         # # # # # # # # # # # # # # # # # # # # # # # # #
          # # # # # # # # # # # # # # # # # # # # # # # #
           # # # # # # # # # # # # # # # # # # # # # # #
            # # # # # # # # # # # # # # # # # # # # # #
             # # # # # # # # # # # # # # # # # # # # #
              # # # # # # # # # # # # # # # # # # # #
               # # # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # #
                 # # # # # # # # # # # # # # # # #
                  # # # # # # # # # # # # # # # #
                   # # # # # # # # # # # # # # #
                    # # # # # # # # # # # # # #
                     # # # # # # # # # # # # #
                      # # # # # # # # # # # #
                       # # # # # # # # # # #
                        # # # # # # # # # #
                         # # # # # # # # #
                          # # # # # # # #
                           # # # # # # #
                            # # # # # #
                             # # # # #
                              # # # #
                               # # #
                                # #
                                 #
                                 #
                                # #
                               # # #
                              # # # #
                             # # # # #
                            # # # # # #
                           # # # # # # #
                          # # # # # # # #
                         # # # # # # # # #
                        # # # # # # # # # #
                       # # # # # # # # # # #
                      # # # # # # # # # # # #
                     # # # # # # # # # # # # #
                    # # # # # # # # # # # # # #
                   # # # # # # # # # # # # # # #
                  # # # # # # # # # # # # # # # #
                 # # # # # # # # # # # # # # # # #
                # # # # # # # # # # # # # # # # # #
               # # # # # # # # # # # # # # # # # # #
              # # # # # # # # # # # # # # # # # # # #
             # # # # # # # # # # # # # # # # # # # # #
            # # # # # # # # # # # # # # # # # # # # # #
           # # # # # # # # # # # # # # # # # # # # # # #
          # # # # # # # # # # # # # # # # # # # # # # # #
         # # # # # # # # # # # # # # # # # # # # # # # # #
        # # # # # # # # # # # # # # # # # # # # # # # # # #
       # # # # # # # # # # # # # # # # # # # # # # # # # # #
      # # # # # # # # # # # # # # # # # # # # # # # # # # # #
     # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    >>> f(10,'an0fpbgwuag9ahfwggb0')
    a n 0 f p b g w u a
     g 9 a h f w g g b
      0 a n 0 f p b g
       w u a g 9 a h
        f w g g b 0
         a n 0 f p
          b g w u
           a g 9
            a h
             f
             w
            g g
           b 0 a
          n 0 f p
         b g w u a
        g 9 a h f w
       g g b 0 a n 0
      f p b g w u a g
     9 a h f w g g b 0
    a n 0 f p b g w u a
    """
    L = [["" for i in range(size)] for j in range(size)]
    L1 = [["" for i in range(size)] for j in range(size)]
    sum = 0
    for i in range(size):
        for j in range(size - i):
            L[i][j] = characters[sum % len(characters)]
            sum += 1
    for i in range(size):
        a = 0
        for j in range(size - i):
            if i == 0:
                if j == size - i - 1:
                    print(L[i][j], end="")
                else:
                    print(L[i][j], end=" ")
            else:
                if a == 0:
                    print(" " * (i - 1), end="")
                    a = 1
                print(" " + L[i][j], end="")
        print()
    for i in range(size):
        for j in range(i + 1):
            L1[i][j] = characters[sum % len(characters)]
            sum += 1
    for i in range(size):
        a = 0
        for j in range(i + 1):
            if i != size - 1:
                if a == 0:
                    print(" " * (size - i - 2), end="")
                    a = 1
                print(" " + L1[i][j], end="")
            else:
                if j == i:
                    print(L1[i][j], end="")
                else:
                    print(L1[i][j], end=" ")
        print()

    pass


if __name__ == "__main__":
    import doctest

    doctest.testmod()
