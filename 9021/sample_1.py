# COMP9021 25T2 - Rachid Hamadi
# Sample Exam 2 Question 1


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
    if len(word) == 0:
        return ""
    result = [word[0]]
    for i in range(len(word) - 1):
        if word[i] != word[i + 1]:
            result.append(word[i + 1])
    return "".join(result)

if __name__ == "__main__":
    import doctest

    doctest.testmod()
