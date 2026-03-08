# 24T3  Q3
# Find words in the dictate.txt that contain all the letters of the target word in the same order.
# Additional letters can be present between the target word's letters.
# You may assume the dictate.txt can be found in your work path.


# 很多人直接暴力枚举了


#
def find(word):
    """
    >>> find('AROSN')
    ANTIREDEPOSITION
    ARDUOUSNESS
    AROUSING
    CAPRICIOUSNESS
    CHIVALROUSNESS
    GASTROINTESTINAL
    HARMONIOUSNESS
    MARVELOUSNESS
    PRECARIOUSNESS
    SACROSANCT
    WAREHOUSING
    >>> find('-')
    NO WORD
    >>> find('ABCDE')
    ABSCONDED
    AMBUSCADE
    >>> find('OAOAO')
    COLLABORATION
    COLLABORATIONS
    COLLABORATOR
    COLLABORATORS
    >>> find('XYXYXYX')
    NO WORD
    >>> find('ARONT')
    ABSTRACTIONIST
    AERONAUTIC
    AERONAUTICAL
    AERONAUTICS
    AFFRONT
    AFFRONTED
    AFFRONTING
    AFFRONTS
    ANACHRONISTICALLY
    ANTIRESONATOR
    APPORTIONMENT
    APPORTIONMENTS
    ARGONAUT
    ARGONAUTS
    ARROGANT
    ARROGANTLY
    ASTRONAUT
    ASTRONAUTICS
    ASTRONAUTS
    BATTLEFRONT
    BATTLEFRONTS
    BICARBONATE
    CARBONATE
    CARBONATES
    CARBONATION
    CARBONIZATION
    CLAIRVOYANT
    CLAIRVOYANTLY
    CLAREMONT
    FAIRMONT
    GASTROINTESTINAL
    HARMONIST
    HARMONISTIC
    HARMONISTICALLY
    MARIONETTE
    PARAMOUNT
    RAPPROCHEMENT
    SACROSANCT
    WAVEFRONT
    WAVEFRONTS
    """
    if not word.isalpha():
        print("NO WORD", end="")
    else:
        sum = 0
        with open("dictionary.txt", "r") as file:
            for letter in file:
                letter = letter.rstrip()
                if len(letter) < len(word):
                    continue
                else:
                    i = 0
                    for ch in letter:
                        if i < len(word) and ch == word[i]:
                            i += 1
                        if i == len(word):
                            print(letter)
                            sum += 1
                            break
            if sum == 0:
                print("NO WORD", end="")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
