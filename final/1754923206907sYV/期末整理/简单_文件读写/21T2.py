# Q6 文件读取 统计计数 难度一般

# The text file, dictionary.txt and lexicon.txt are all assumed
# to be stored in the working directory.
# Make sure you do NOT use an absolute path to open them.
#
# The words in the file are supposed to consist of nothing but letters
# (no apostrophes, no hyphens...), possibly immediately followed by
# a single full stop, comma, colon or semicolon.
# There can be any amount of space anywhere between words, before the
# first word, and after the last word.
#
# Two words w_1 and w_2 are similar if:
# - w_2 is w_1 plus one letter at the end, or
# - w_1 is w_2 plus one letter at the end, or
# - w_1 and w_2 only differ in their last letter.
#
# Outputs:
# - the list of words which are similar to at least one word
#   in either dictionary.txt or lexicon.txt, ignoring case differences;
# - all other words which are different to all words in both
#   dictionary.txt and lexicon.txt, ignoring case differences.
#
# Though case does not matter in comparisons, words are output
# with the case they have in the text file (and so possibly
# many times if they occur with different cases in the file,
# but only once for a given case).
#
# For both lists, words are output (once for a given case),
# in lexicographic order (note that uppercase letters come
# before lowercase letters in the ASCII, and so in the Unicode,
# character set).
#
# The lines that read "The similar words are:" and
# "The possible new words are:" are always output,
# even if they are not followed by any word.
#
# You can assume that the function is called with as argument
# a string that is the name of a text file that exists in the
# working directory.


def f(filename):
    '''
    >>> f('edgar_poe.txt')
    The similar words are:
      Fortunato
      redresser
    The possible new words are:
      connoisseurship
      definitively
      definitiveness
      immolation
      imposture
      practise
      unredressed
    >>> f('oscar_wild.txt')
    The similar words are:
      Renan
      realise
    The possible new words are:
      Flaubert
      misdirected
      neighbours
    '''
    # INSERT YOUR CODE HERE

if __name__ == '__main__':
    import doctest

    doctest.testmod()
