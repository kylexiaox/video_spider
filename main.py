'''
coding:utf-8
@FileName:utils
@Time:2024/3/22 1:16 AM
@Author: Xiang Xiao
@Email: btxiaox@gmail.com
@Description:
'''

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import random

import redis
from utils import *
import config
from config import BASE_DIR
from playwright.async_api import async_playwright
import logger


# 连接到 Redis 服务器
# 1号库存储video_id的全部信息，一天以后信息过期
# 2号库存储author_id的作者信息，一周以后信息过期
r1 = redis.StrictRedis(host='localhost', port=6379, db=1)
r2 = redis.StrictRedis(host='localhost', port=6379, db=2)


async def cookie_auth(account_file):
    """
    验证cookie是否有效
    :param account_file:
    :return:
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_selector("div.boards-more h3:text('抖音排行榜')", timeout=5000)  # 等待5秒
            logger.spiderlogger.info("[+] 等待5秒 cookie 失效")
            return False
        except:
            logger.spiderlogger.info("[+] cookie 有效")
            return True


async def douyin_cookie_gen():
    """
    生成cookie
    :return:
    """
    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://www.douyin.com/user/self")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await asyncio.sleep(5)
        account_element = await page.query_selector(
            '#douyin-right-container > div.tQ0DXWWO.DAet3nqK.userNewUi > div > div > div.o1w0tvbC.F3jJ1P9_.InbPGkRv > div.mZmVWLzR > p > span.TVGQz3SI')
        text = await account_element.inner_text()
        account_id = text.split('：')[1]
        account_file = Path(BASE_DIR / "douyin_cookies" / (str(account_id) + ".json"))
        logger.spiderlogger.info(f"[+] 生成cookie文件 {account_file}")
        await context.storage_state(path=account_file)


async def douyin_setup(handle=False, account_file=""):
    """
    配置抖音账号
    :param handle:
    :param account_file:
    :return:
    """
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        logger.spiderlogger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await douyin_cookie_gen()
    return True


class Douyin_Spider(object):
    """
    从douyin某一个视频开始爬取，爬取指定数量的视频，
    视频作者的粉丝数小于等于minimum_fans_count，
    视频的点赞数大于等于minius_like_count
    时间在day_gap天内
    """

    def __init__(self, start_video_id, account_id='89079537399', result_count=20, maxium_fans_count=3000,
                 minimum_favorite_count=10000, day_gap=7):
        """
        初始化函数，设置爬虫的参数，
        :param start_video_id:  起始视频id
        :param account_id:  抖音账号id
        :param result_count:  爬取视频的数量
        :param minimum_fans_count:  视频作者的粉丝数
        :param minimum_like_count:  视频的点赞数
        :param day_gap:  视频距今时间间隔
        """
        self.account_file = Path(BASE_DIR / "douyin_cookies" / (str(account_id) + ".json"))
        self.start_video_id = start_video_id
        self.result_count = result_count
        self.maxium_fans_count = maxium_fans_count
        self.minimum_favorite_count = minimum_favorite_count
        self.day_gap = day_gap
        self.recursion_depth = config.MAX_RECURSION_DEPTH
        self.result = []

    async def on_start(self, playwright: async_playwright):
        """
        爬虫入口
        :return:
        """
        # 使用一chromium浏览器生成一个异步实例
        self.browser = await playwright.chromium.launch(headless=False)
        # 创建一个新的上下文
        context = await self.browser.new_context(storage_state=self.account_file)
        # 创建一个新的页面
        page = await context.new_page()
        logger.spiderlogger.info(f"[+] 开始爬取抖音视频，起始视频id为{self.start_video_id}")
        await self.process_video(page)
        logger.spiderlogger.info(f"[+] 结束爬取抖音视频")
        print(self.result)

    async def process_video(self, page, video_id=None,recursion_depth=0):
        """
        处理视频,递归调用
        :param page:
        :param video_id:
        :return:
        """
        # 获取一个0-5秒的随机数
        await asyncio.sleep(random.randint(0, 10))
        if len(self.result) >= self.result_count:
            # 判断是否完任务
            await page.close()
            logger.spiderlogger.info(f"[+] 爬取视频数量达到{self.result_count}，结束爬取")
            file_name = f'{self.start_video_id}_{self.result_count}_{datetime.now().strftime("%Y-%m-%d")}.json'
            output_path = Path(BASE_DIR / "douyin_output" / file_name)
            # 把self.result的部分字段写入文件
            with open(output_path, 'w') as f:
                json.dump(self.result, f)
            return

        if recursion_depth >= self.recursion_depth:
            await page.close()
            logger.spiderlogger.info(f"[+] 递归深度达到{self.recursion_depth}，结束爬取")
            return
        # 记录当前结果集数量
        logger.spiderlogger.info(f"[+] 当前结果集数量{len(self.result)}")
        video_info = {}
        if video_id is None:
            video_id =self.start_video_id
        # 组装douyin视频的url
        url = f"https://www.douyin.com/video/{video_id}"
        logger.spiderlogger.info(f"[+] 开始处理视频id{video_id},访问视频链接{url},递归深度{recursion_depth}")
        # 访问指定的 URL
        await page.goto(url)

        # 等待页面加载完成
        await page.wait_for_url(url)
        await asyncio.sleep(3)
        author_info = await self.get_author_info(page)
        video_info['video_id'] = video_id
        video_info['author'] = author_info
        video_detail_info = await self.get_video_info(page,video_id)
        video_info['video_detail'] = video_detail_info
        is_qualified = self.is_qualified(video_info)
        logger.spiderlogger.info(f"[-] 视频id{video_id},作者{author_info['author_name']}，粉丝数{author_info['author_fans_count']}，点赞数{video_detail_info['like_count']}，是否符合要求{is_qualified}")
        recommend_selector = '#douyin-right-container > div:nth-child(2) > div > div.lferVJ2i > div > div.fhcniom_ > ul > li'
        recommend_list_element = await page.query_selector_all(recommend_selector)
        logger.spiderlogger.info(f"[-] 获取视频id{video_id}的推荐视频列表")
        for recommend_video in recommend_list_element:
            try:
                video_url_element = await recommend_video.query_selector('.Qyud97Wg')
                video_url_element = await video_url_element.query_selector('a')
                author_url_element = await recommend_video.query_selector('.J8sYvs4F')
                author_url_element = await author_url_element.query_selector('a')
                r_video_url = await video_url_element.get_attribute('href')
                r_author_url = await author_url_element.get_attribute('href')
                r_video_id = r_video_url.split('/')[-1]
                r_author_id = r_author_url.split('?')[0].split('/')[-1]
                r_favorite_count_element = await recommend_video.query_selector('.Yv0z0leE')
                r_favorite_count = await r_favorite_count_element.inner_text()
                r_favorite_count = convert_numbers(r_favorite_count)
                if r2.get(r_author_id) is not None:
                    r_author_fans_count = json.loads(r2.get(r_author_id).decode('utf-8')).get('author_fans_count')
                else:
                    r_author_fans_count = None
                if r_favorite_count <= self.minimum_favorite_count:
                    logger.spiderlogger.info(f"[-] 推荐视频{r_video_id}，作者{r_author_id}，点赞{r_favorite_count}不符合要求")
                    continue
                elif r_author_fans_count is not None and convert_numbers(r_author_fans_count) >= self.maxium_fans_count:
                    logger.spiderlogger.info(f"[-] 推荐视频{r_video_id}，作者{r_author_id}，粉丝数{r_author_fans_count}不符合要求")
                    continue
                else:
                    logger.spiderlogger.info(f"[+] 推荐视频{r_video_id}，作者{r_author_id}，点赞{r_favorite_count}符合要求,获取信息中")
                    # playwright 打开一个新页面,获取视频信息
                    new_page = await page.context.new_page()
                    await self.process_video(new_page,r_video_id,recursion_depth+1)
                    # sleep 5s
                    await asyncio.sleep(5)
            except Exception as e:
                logger.spiderlogger.error(e,exc_info=True)
                logger.spiderlogger.error(f"[-] 视频获取推荐视频信息失败，跳过")
        if not is_qualified:
            logger.spiderlogger.info(f"[+] 视频id{video_id},视频链接：https://www.douyin.com/video/{video_id}  不符合要求")
            # 关闭当前页面
            await page.close()
            return



    async def get_author_info(self, page) -> dict:
        """
        获取视频信息
        :param page:
        :return:
        """
        # 获取视频作者
        result = {}
        author_element = await page.query_selector(
            '#douyin-right-container > div:nth-child(2) > div > div.lferVJ2i > div > div.UbblxGZr > div.WdX5lXbX')
        author_name_element = await author_element.query_selector('.j5WZzJdp')
        author_name = await author_name_element.inner_text()
        result['author_name'] = author_name
        # 获取author_element 中a标签的内容，即作者的主页链接
        author_link_element = await author_element.query_selector('a')
        author_link = await author_link_element.get_attribute('href')
        result['author_id'] = author_link.split('/')[-1]
        result['author_link'] = author_link
        # 获取视频作者的粉丝数和点赞数
        auth_info_elements = await page.query_selector_all('.JWilT3lH')
        for index, auth_info_element in enumerate(auth_info_elements):
            auth_info = await auth_info_element.inner_text()
            if index == 0:
                result['author_fans_count'] = convert_numbers(auth_info)
            if index == 1:
                result['author_like_count'] = convert_numbers(auth_info)
        # 存储作者信息 to reids
        result_json = json.dumps(result)
        r2.set(result['author_id'], result_json,ex=604800)
        return result

    async def get_video_info(self, page,video_id) -> dict:
        """
        获取视频信息
        :param page:
        :return:
        """
        result = {}
        # 获取点赞数
        like_count_element = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.xi78nG8b > div:nth-child(1) > span')
        like_count = await like_count_element.inner_text()
        result['like_count'] = convert_numbers(like_count)
        # 获取评论数
        comment_count_element = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.xi78nG8b > div:nth-child(2) > span')
        comment_count = await comment_count_element.inner_text()
        result['comment_count'] = convert_numbers(comment_count)
        # 获取收藏数
        collect_count_element = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.xi78nG8b > div:nth-child(3) > span')
        collect_count = await collect_count_element.inner_text()
        result['collect_count'] = convert_numbers(collect_count)
        # 获取分享数
        share_count_element = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.xi78nG8b > div.baUdKwAS._BMsHw2S > span')
        share_count = await share_count_element.inner_text()
        result['share_count'] = convert_numbers(share_count)
        publish_time = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.WPSxa4XK > span')
        publish_time = await publish_time.inner_text()
        publish_time = publish_time.split('：')[1]
        result['publish_time'] = publish_time
        # 存储视频信息 to reids
        result_json = json.dumps(result)
        r1.set(video_id, result_json,ex=86400)
        return result


    def is_qualified(self,video_info):
        """
        判断视频是否符合要求
        :param video_info:
        :return:
        """
        # 如果传入视频是启动视频，则返回True
        if video_info['video_id'] == self.start_video_id:
            return True
        # 判断后续条件
        if video_info['author']['author_fans_count'] >= self.maxium_fans_count:
            return False
        if video_info['video_detail']['like_count'] <= self.minimum_favorite_count:
            return False
        now = datetime.now()
        # 判断视频发布时间是否在day_gap天内
        publish_time = datetime.strptime(video_info['video_detail']['publish_time'], "%Y-%m-%d %H:%M")
        if (now - publish_time).days > self.day_gap:
            return False
        self.result.append(video_info)
        video_id = video_info['video_id']
        logger.spiderlogger.info(f"[+] 视频id{video_id},视频链接：https://www.douyin.com/video/{video_id}  符合要求")
        return True





    async def main(self):
        """
        异步入口主函数
        :return:
        """
        async with async_playwright() as playwright:
            return await self.on_start(playwright)
