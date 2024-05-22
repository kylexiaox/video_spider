'''
coding:utf-8
@FileName:run
@Time:2024/3/19 5:09 PM
@Author: Xiang Xiao
@Email: btxiaox@gmail.com
@Description:
'''
import sys
from main import *

if __name__ == '__main__':
    args = sys.argv[1:]
    # if args[0] is None:
    #     video_id = args[0]
    # else:
    video_id = 7365746739808079140
    app = Douyin_Spider(start_video_id = video_id)
    asyncio.run(app.main(),debug=False)

