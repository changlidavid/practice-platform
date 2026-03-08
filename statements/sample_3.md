# Sample 3

## Problem

Given a word w, a good subsequence of w is defined as a word w' such that
- all letters in w' are different;
- w' is obtained from w by deleting some letters in w.

Returns the list of all good subsequences, without duplicates, in lexicographic order
(recall that the sorted() function sorts strings in lexicographic order).

The number of good sequences grows exponentially in the number of distinct letters in w,
so the function will be tested only for cases where the latter is not too large.

## Function Signature

- `good_subsequences(word)`

## Notes

- Write your code in the solution file on the right.

- The runner executes `python -m doctest -v` against your solution.
