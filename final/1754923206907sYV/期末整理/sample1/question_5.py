# COMP9021 25T2 - Rachid Hamadi
# Sample Exam Question 5


'''
Will be tested with year between 1913 and 2013.
You might find the reader() function of the csv module useful,
but you can also use the split() method of the str class.
'''

import csv

def f(year):
    '''
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
    '''
    months = 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    # Insert your code here
    # max_inflation = float('-inf')
    # months_with_max = []

    # with open('cpiai.csv') as file:
    #     reader = csv.reader(file)
    #     next(reader)  # 跳过表头
        
    #     for row in reader:
    #         date, _, inflation_str = row
    #         row_year = int(date[:4])
    #         if row_year != year:
    #             continue
    #         month_num = int(date[5:7])  # 取出月份数字 01~12
    #         month_name = months[month_num - 1]
    #         inflation = float(inflation_str)

    #         if inflation > max_inflation:
    #             max_inflation = inflation
    #             months_with_max = [month_name]
    #         elif inflation == max_inflation:
    #             months_with_max.append(month_name)
    # with open (cpiai.csv,'r')as flie:
    #     reader=csv.reader(file)
    #     next(reader)
    #     for i in reader:
    #         date, _, inflation_str = row
    #         row_year = int(date[:4])
    #         if row_year !=year:
    #             continue
    #         month_num= int(date[5:7])
    #         month_name = months [month_num - 1] 
            



    print(f'In {year}, maximum inflation was: {max_inflation}')
    print('It was achieved in the following months: ' + ', '.join(months_with_max))


if __name__ == '__main__':
    import doctest
    doctest.testmod()
