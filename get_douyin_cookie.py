'''
coding:utf-8
@FileName:get_douyin_cookie
@Time:2024/3/19 3:37 PM
@Author: Xiang Xiao
@Email: btxiaox@gmail.com
@Description:
'''


import asyncio
from pathlib import Path

from config import BASE_DIR
from main import douyin_setup

if __name__ == '__main__':
    cookie_setup = asyncio.run(douyin_setup(handle=True))