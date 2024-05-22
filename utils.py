'''
coding:utf-8
@FileName:utils
@Time:2024/3/22 1:17 AM
@Author: Xiang Xiao
@Email: btxiaox@gmail.com
@Description:
'''


def convert_numbers(num: str) -> int:
    """
    Convert the number with 万 to the number
    :param num: str
    :return: int
    """
    if type(num) == int:
        return num
    if num[-1] == '万':
        return int(float(num[:-1]) * 10000)
    else:
        return int(num)