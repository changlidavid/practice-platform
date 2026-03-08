# The text file is assumed to be stored in the working directory.
# Make sure you do NOT use an absolute path to open it.
#
# Can be tested on a file with a different name and different contents.
#
# Call token a longest sequence of characters in the text none
# of which is a space (examples of tokens: "The", "avenged;",
# "punish,", "MILLIONAIRES.").
# - You can assume that the only space characters in the file are
#   single spaces and new line characters (no tabs).
# - You can assume that A SINGLE SPACE separates two SUCCESSIVE
#   tokens on a given line. But a line can start and end with an
#   arbitrary number of single spaces (possibly none), and there
#   can be blank lines, with or without single spaces.
#
# - Each line in the output has no single space at the beginning nor
#   at the end.
# - Each line in the output has at most length (the second argument
#   to the function) many characters. You can assume that the argument
#   length to the function is AT LEAST EQUAL to the length of the
#   longest token in the text.
# - No token is split over two lines in the output.
# - Each line in the output is the longest possible.
#
# Note: If you think well, then this exercise is easy and the solution
#       very short. But if you do not think well, it could quickly
#       become messy. So if you attempt this question, make sure you
#       give yourself plenty of time to reflect on how to approach the
#       question rather than jumping straight into coding.
def f(filename, length):
    '''
    >>> f('edgar_poe.txt', 50)
    The thousand injuries of Fortunato I had borne as
    I best could, but when he ventured upon insult, I
    vowed revenge. You, who so well know the nature of
    my soul, will not suppose, however, that I gave
    utterance to a threat. At length I would be
    avenged; this was a point definitively settled,
    but the very definitiveness with which it was
    resolved precluded the idea of risk. I must not
    only punish, but punish with impunity. A wrong is
    unredressed when retribution overtakes its
    redresser. It is equally unredressed when the
    avenger fails to make himself felt as such to him
    who has done the wrong. It must be understood that
    neither by word nor deed had I given Fortunato
    cause to doubt my good will. I continued as was my
    wont, to smile in his face, and he did not
    perceive that my smile NOW was at the thought of
    his immolation. He had a weak point, this
    Fortunato, although in other regards he was a man
    to be respected and even feared. He prided himself
    on his connoisseurship in wine. Few Italians have
    the true virtuoso spirit. For the most part their
    enthusiasm is adopted to suit the time and
    opportunity to practise imposture upon the British
    and Austrian MILLIONAIRES.
    >>> f('edgar_poe.txt', 21)
    The thousand injuries
    of Fortunato I had
    borne as I best
    could, but when he
    ventured upon insult,
    I vowed revenge. You,
    who so well know the
    nature of my soul,
    will not suppose,
    however, that I gave
    utterance to a
    threat. At length I
    would be avenged;
    this was a point
    definitively settled,
    but the very
    definitiveness with
    which it was resolved
    precluded the idea of
    risk. I must not only
    punish, but punish
    with impunity. A
    wrong is unredressed
    when retribution
    overtakes its
    redresser. It is
    equally unredressed
    when the avenger
    fails to make himself
    felt as such to him
    who has done the
    wrong. It must be
    understood that
    neither by word nor
    deed had I given
    Fortunato cause to
    doubt my good will. I
    continued as was my
    wont, to smile in his
    face, and he did not
    perceive that my
    smile NOW was at the
    thought of his
    immolation. He had a
    weak point, this
    Fortunato, although
    in other regards he
    was a man to be
    respected and even
    feared. He prided
    himself on his
    connoisseurship in
    wine. Few Italians
    have the true
    virtuoso spirit. For
    the most part their
    enthusiasm is adopted
    to suit the time and
    opportunity to
    practise imposture
    upon the British and
    Austrian
    MILLIONAIRES.
    '''
    # INSERT YOUR CODE HERE


if __name__ == '__main__':
    import doctest

    doctest.testmod()
