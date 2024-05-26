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

MAX_RECURSION_DEPTH = 5

# 不符合条件的视频，有多大的概率进行下一级递归
random_incidences = 0.3

rule: dict = {
    # 低粉爆款的规则
    'default':{
        # 默认规则 :
        'max_fans': 10000, # 粉丝数不超过max_fans
        'max_favorites': None, # 点赞数不超过max_favorites
        'min_favorites': 1000, # 点赞数不低于min_favorites
        'ratio':5  # 点赞是粉丝数的多少倍
        },
    }