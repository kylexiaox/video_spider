# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import asyncio
import os
from pathlib import Path

import redis

from config import BASE_DIR
from playwright.async_api import async_playwright
import logger


# 连接到 Redis 服务器
r = redis.StrictRedis(host='localhost', port=6379, db=1)

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
    """

    def __init__(self, start_video_id, account_id='30365867345', result_count=20, minimum_fans_count=3000,
                 minimum_like_count=10000, day_gap=7):
        self.account_file = Path(BASE_DIR / "douyin_cookies" / (str(account_id) + ".json"))
        self.start_video_id = start_video_id
        self.result_count = result_count
        self.minimum_fans_count = minimum_fans_count
        self.minimum_like_count = minimum_like_count
        self.day_gap = day_gap

    async def start(self, playwright: async_playwright):
        """
        爬虫入口
        :return:
        """
        # 使用一chromium浏览器生成一个异步实例
        video_info = {}
        browser = await playwright.chromium.launch(headless=False)
        # 创建一个新的上下文
        context = await browser.new_context(storage_state=self.account_file)
        # 创建一个新的页面
        page = await context.new_page()
        # 组装douyin视频的url
        url = f"https://www.douyin.com/video/{self.start_video_id}"
        # 访问指定的 URL
        await page.goto(url)
        logger.spiderlogger.info(f"[+] 开始爬取抖音视频，起始视频id为{self.start_video_id}")
        # 等待页面加载完成
        await page.wait_for_url(url)
        await asyncio.sleep(5)
        author_info = await self.get_author_info(page)
        video_info['author'] = author_info
        video_detail_info = await self.get_video_info(page)
        video_info['video_detail'] = video_detail_info


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
        result['author_link'] = author_link
        # 获取视频作者的粉丝数和点赞数
        auth_info_elements = await page.query_selector_all('.JWilT3lH')
        for index, auth_info_element in enumerate(auth_info_elements):
            auth_info = await auth_info_element.inner_text()
            if index == 0:
                result['author_fans_count'] = auth_info
            if index == 1:
                result['author_like_count'] = auth_info
        return result

    async def get_video_info(self, page) -> dict:
        """
        获取视频信息
        :param page:
        :return:
        """

        result = {}
        # 获取点赞数
        like_count_element = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.xi78nG8b > div:nth-child(1) > span')
        like_count = await like_count_element.inner_text()
        result['like_count'] = like_count
        # 获取评论数
        comment_count_element = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.xi78nG8b > div:nth-child(2) > span')
        comment_count = await comment_count_element.inner_text()
        result['comment_count'] = comment_count
        # 获取收藏数
        collect_count_element = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.xi78nG8b > div:nth-child(3) > span')
        collect_count = await collect_count_element.inner_text()
        result['collect_count'] = collect_count
        # 获取分享数
        share_count_element = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.xi78nG8b > div.baUdKwAS._BMsHw2S > span')
        share_count = await share_count_element.inner_text()
        result['share_count'] = share_count
        publish_time = await page.query_selector('#douyin-right-container > div:nth-child(2) > div > div.leftContainer.gkVJg5wr > div.XYnWH9QO > div > div.YuF0Acwt > div.WPSxa4XK > span')
        publish_time = await publish_time.inner_text()
        publish_time = publish_time.index('：')[1]
        result['publish_time'] = publish_time
        return result

    async def main(self):
        """
        异步入口主函数
        :return:
        """
        async with async_playwright() as playwright:
            return await self.start(playwright)
