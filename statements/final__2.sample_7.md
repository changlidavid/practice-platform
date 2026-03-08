# Final 2.Sample 7

## Problem

Tries and find a word in a text file that represents a grid of words, all of the same length.
There is only one word per line in the file.
The letters that make up a word can possibly be separated by an arbitrary number of spaces,
and there can also be spaces at the beginning or at the end of a word,
and there can be lines consisting of nothing but spaces anywhere in the file.
Assume that the file stores data as expected.

A word can be read horizontally from left to right,
or vertically from top to bottom,
or diagonally from top left to bottom right
(this is more limited than the lab exercise).
The locations are represented as a pair (line number, column number),
starting the numbering with 1 (not 0).

## Function Signature

- `find_word(filename, word)`
- `find_word_horizontally(grid, word)`
- `find_word_vertically(grid, word)`
- `find_word_diagonally(grid, word)`

## Notes

- Write your code in the solution file on the right.

- The runner executes `python -m doctest -v` against your solution.
