def remove_consecutive_duplicates(word):
    """
    >>> remove_consecutive_duplicates('')
    ''
    >>> remove_consecutive_duplicates('a')
    'a'
    >>> remove_consecutive_duplicates('ab')
    'ab'
    >>> remove_consecutive_duplicates('aba')
    'aba'
    >>> remove_consecutive_duplicates('aaabbbbbaaa')
    'aba'
    >>> remove_consecutive_duplicates('abcaaabbbcccabc')
    'abcabcabc'
    >>> remove_consecutive_duplicates('aaabbbbbaaacaacdddd')
    'abacacd'
    """
    # Insert your code here (the output is returned, not printed out)
    if word == "":
        return ""
    # 先把第0个元素加到结果里
    new = word[0]
    # 把第0个元素从word里删了
    word = word[1::]
    for item in word:
        if item != new[-1]:
            new += item
    return new


if __name__ == "__main__":
    import doctest
    doctest.testmod()
