def f(word):
    """
    Recall that if c is an ascii character then ord(c) returns its ascii code.
    Will be tested on nonempty strings of lowercase letters only.

    >>> f('x')
    The longest substring of consecutive letters has a length of 1.
    The leftmost such substring is x.
    >>> f('xy')
    The longest substring of consecutive letters has a length of 2.
    The leftmost such substring is xy.
    >>> f('ababcuvwaba')
    The longest substring of consecutive letters has a length of 3.
    The leftmost such substring is abc.
    >>> f('abbcedffghiefghiaaabbcdefgh')
    The longest substring of consecutive letters has a length of 7.
    The leftmost such substring is bcdefgh.
    >>> f('abcabccdefcdefghacdef')
    The longest substring of consecutive letters has a length of 6.
    The leftmost such substring is cdefgh.
    >>> f('abcdbcdedefg')
    The longest substring of consecutive letters has a length of 4.
    The leftmost such substring is abcd.
    """
    table = "abcdefghijklmnopqrstuvwxyz"
    if word == "":
        print(f"The longest substring of consecutive letters has a length of 0.")
        print(f"The leftmost such substring is {""}.")
        return
    # 先把第0个元素加到结果里
    new = word[0]
    # 记录最长的结果
    result = new
    # 把第0个元素从word里删了
    word = word[1::]
    for current_letter in word:
        # 取出上一个字母
        last_letter = new[-1]
        # 比较当前字母是不是上一个字母 字母表顺序中的下一个字母
        if table.find(current_letter) - table.find(last_letter) == 1:
            new += current_letter
        else:
            # 如果字母不连续 尝试把最长的结果加入
            if len(new) > len(result):
                result = new
            new = current_letter

    if len(new) > len(result):
        result = new
    print(f"The longest substring of consecutive letters has a length of {len(result)}.")
    print(f"The leftmost such substring is {result}.")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
