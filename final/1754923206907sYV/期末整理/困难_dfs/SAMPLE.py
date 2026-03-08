# You can assume that word_pairs() is called with a string of
# uppercase letters as agument.
#
# dictionary.txt is stored in the working directory.
#
# Outputs all pairs of distinct words in the dictionary file, if any,
# that are made up of all letters in available_letters
# (if a letter in available_letters has n occurrences,
# then there are n occurrences of that letter in the combination
# of both words that make up an output pair).
#
# The second word in a pair comes lexicographically after the first word.
# The first words in the pairs are output in lexicographic order
# and for a given first word, the second words are output in
# lexicographic order.
#
# Hint: If you do not know the imported Counter class,
#       experiment with it, passing a string as argument, and try
#       arithmetic and comparison operators on Counter objects.


from collections import Counter
import copy

dictionary_file = "dictionary.txt"


class Node:
    def __init__(self):
        self.isEnd = False
        self.isWord = None
        self.child = {}


class T:
    def __init__(self):
        self.all_childs = {}

    def insert(self, word):
        if len(word) not in self.all_childs:
            self.all_childs[len(word)] = Node()
        root = self.all_childs[len(word)]
        for char in word:
            if char not in root.child:
                root.child[char] = Node()
            root = root.child[char]
        root.isEnd = True
        root.isWord = word

    def find_all_word(self, node: Node, sets: list, result: set):
        if not sets:
            if node.isEnd:
                result.add(node.isWord)
            return result
        for item in sets:
            if item in node.child:
                new_sets = copy.deepcopy(sets)
                new_sets.remove(item)
                self.find_all_word(node.child[item], new_sets, result)
        return result


def word_pairs(available_letters):
    """
    >>> word_pairs('ABCDEFGHIJK')
    >>> word_pairs('ABCDEF')
    CAB FED
    >>> word_pairs('ABCABC')
    >>> word_pairs('EOZNZOE')
    OOZE ZEN
    ZOE ZONE
    >>> word_pairs('AIRANPDLER')
    ADRENAL RIP
    ANDRE APRIL
    APRIL ARDEN
    ARID PLANER
    ARLEN RAPID
    DANIEL PARR
    DAR PLAINER
    DARER PLAIN
    DARNER PAIL
    DARPA LINER
    DENIAL PARR
    DIRE PLANAR
    DRAIN PALER
    DRAIN PEARL
    DRAINER LAP
    DRAINER PAL
    DRAPER LAIN
    DRAPER NAIL
    ERRAND PAIL
    IRELAND PAR
    IRELAND RAP
    LAIR PANDER
    LAND RAPIER
    LAND REPAIR
    LANDER PAIR
    LARDER PAIN
    LEARN RAPID
    LIAR PANDER
    LINDA RAPER
    NADIR PALER
    NADIR PEARL
    NAILED PARR
    PANDER RAIL
    PLAN RAIDER
    PLANAR REID
    PLANAR RIDE
    PLANER RAID
    RAPID RENAL
    """
    pass
    # REPLACE PASS ABOVE WITH YOUR CODE
    printed = set()
    inp = list(available_letters)
    
    # 处理单词表 把单词表里的单词插入到字典树
    w = set()
    with open(dictionary_file, "r") as rf:
        for item in rf:
            w.add("".join(item.split()))
    w = sorted(list(w))
    Tt = T()
    for item in w:
        Tt.insert(item)
        
    # 开始做题
    # 对于每个单词进行循环
    for item in w:
        # 复制了一份 输入的字符串
        tp = copy.deepcopy(inp)
        # 首先把所有的单词 当成第一个单词
        # 在输入的字符串里 把 这些单词 的 字母 都删掉
        # 如果当前单词 有字母 并不在 我们输入的字母中 呢么我们就跳过这个单词
        valid = True
        for char in item:
            if char in tp:
                tp.remove(char)
            else:
                valid = False

        if valid:
            # 寻找所有符合条件的 另一个单词
            if len(tp) in Tt.all_childs:
                result = Tt.find_all_word(Tt.all_childs[len(tp)], 0, tp, set())
                if result:
                    print(result)
                result = sorted(list(result))
                for m in result:
                    if not (m in printed or item in printed) and item != m:
                        print(item, m)
        printed.add(item)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
