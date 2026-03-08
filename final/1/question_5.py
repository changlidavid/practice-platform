# COMP9021 25T2 - Rachid Hamadi
# Sample Exam Question 5 Solution


"""
Write a function that accepts a year between 1913 and 2013 inclusive
and displays the maximum inflation during that year and the month(s)
in which it was achieved.
You might find the reader() function of the csv module useful,
but you can also use the split() method of the str class.
Make use of the attached cpiai.csv file.
"""

import csv


def f(year):
    """
    >>> f(1914)
    In 1914, maximum inflation was: 2.0
    It was achieved in the following months: Aug
    >>> f(1922)
    In 1922, maximum inflation was: 0.6
    It was achieved in the following months: Jul, Oct, Nov, Dec
    >>> f(1995)
    In 1995, maximum inflation was: 0.4
    It was achieved in the following months: Jan, Feb
    >>> f(2013)
    In 2013, maximum inflation was: 0.82
    It was achieved in the following months: Feb
    """
    months = (
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    )
    # Insert your code here
    max = -10
    with open("cpiai.csv") as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # skips the first row (header) of the CSV file
        for i in csv_reader:
            if i[0].split("-")[0] == str(year):
                if float(i[2]) > max:
                    max = float(i[2])
    with open("cpiai.csv") as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # skips the first row (header) of the CSV file
        m = 0
        s = ""
        for i in csv_reader:
            if i[0].split("-")[0] == str(year):
                if float(i[2]) == max:
                    s += months[m] + ", "
                m += 1

    print(f"In {year}, maximum inflation was: {max}")
    print(f"It was achieved in the following months: {s[:-2]}")


if __name__ == "__main__":
    import doctest

    doctest.testmod()

# f(1922)
