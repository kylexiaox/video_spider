'''
coding:utf-8
@FileName:config
@Time:2024/3/19 3:32 PM
@Author: Xiang Xiao
@Email: btxiaox@gmail.com
@Description:
'''
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

RESULT_PATH = BASE_DIR / 'result'

MAX_RECURSION_DEPTH = 10