# Final 2.Sample 6

## Problem

is_valid_prefix_expression(expression) checks whether the string expression
represents a correct infix expression (where arguments follow operators).

evaluate_prefix_expression(expression) returns the result of evaluating expression.

For expression to be syntactically correct:
- arguments have to represent integers, that is, tokens that can be converted to an integer
  thanks to int();
- operators have to be any of +, -, * and /;
- at least one space has to separate two consecutive tokens.

Assume that evaluate_prefix_expression() is only called on syntactically correct expressions,
and that / (true division) is applied to a denominator that is not 0.

You might find the reversed() function, the split() string method,
and the pop() and append() list methods useful.

## Function Signature

- `is_valid_prefix_expression(expression)`
- `evaluate_prefix_expression(expression)`

## Notes

- Write your code in the solution file on the right.

- The runner executes `python -m doctest -v` against your solution.
