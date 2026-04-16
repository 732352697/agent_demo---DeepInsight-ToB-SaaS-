#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爆款视频数据爬虫 - 支持 B站、抖音、小红书

使用 Playwright 模拟真实浏览器，自动抓取各平台热门视频数据
保存为 JSON 格式，方便后续分析和使用
"""

import asyncio
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright


class VideoCrawler:
    """视频数据爬虫类"""
    
    def __init__(self, headless: bool = False):
        """
        初始化爬虫
        
        Args:
            headless: 是否使用无头模式（不显示浏览器窗口）
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright: Optional[Playwright] = None
        self.results: Dict[str, List[Dict]] = {}
        self.context = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def start_browser(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        # 启动 Chromium 浏览器，禁用自动化特征以绕过检测
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',  # 禁用自动化检测
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--disable-popup-blocking',
            ]
        )
        # 创建新的浏览器上下文，设置更真实的视口和用户代理
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def create_page(self) -> Page:
        """
        创建新的页面
        
        Returns:
            Page 对象
        """
        page = await self.context.new_page()
        # 设置默认超时
        page.set_default_timeout(30000)
        return page
    
    async def crawl_bilibili(self, keyword: str, top_n: int = 10) -> List[Dict]:
        """
        爬取 B站 视频数据
        
        Args:
            keyword: 搜索关键词
            top_n: 获取前 N 个视频
            
        Returns:
            视频数据列表
        """
        print(f"\n{'='*50}")
        print(f"正在爬取 B站: {keyword}")
        print(f"{'='*50}")
        
        videos = []
        page = await self.create_page()
        
        try:
            # 访问 B站搜索页面
            search_url = f"https://search.bilibili.com/all?keyword={keyword}&search_type=video"
            await page.goto(search_url)
            
            # 等待页面加载
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(3)  # 额外等待
            
            # 尝试多种选择器
            try:
                await page.wait_for_selector('.video-list-item', timeout=15000)
            except:
                try:
                    await page.wait_for_selector('.bili-video-card', timeout=15000)
                except:
                    await page.wait_for_selector('[class*="video-card"]', timeout=15000)
            
            # 滚动页面以加载更多内容
            for _ in range(3):
                await page.evaluate('window.scrollBy(0, 800)')
                await asyncio.sleep(1)
            
            # 获取视频元素列表 - 尝试多种选择器
            video_elements = []
            for selector in ['.video-list-item', '.bili-video-card', '[class*="video-card"]', '.video-item']:
                video_elements = await page.query_selector_all(selector)
                if video_elements:
                    print(f"  使用选择器: {selector}")
                    break
            
            video_elements = video_elements[:top_n]
            
            for idx, element in enumerate(video_elements):
                try:
                    # 获取标题 - 尝试多种选择器
                    title = ""
                    for selector in ['.title', '[class*="title"]', '.bili-video-card__title', '.video-title']:
                        title_elem = await element.query_selector(selector)
                        if title_elem:
                            title = await title_elem.inner_text()
                            break
                    title = title.strip() if title else "未知标题"
                    
                    # 获取视频链接 - 尝试多种选择器
                    bvid = ""
                    video_url = ""
                    for selector in ['a.title', 'a[class*="title"]', '.bili-video-card__link', 'a']:
                        link_elem = await element.query_selector(selector)
                        if link_elem:
                            href = await link_elem.get_attribute('href') or await link_elem.get_attribute('to')
                            if href:
                                if '/video/' in href:
                                    bvid = href.split('/')[-1].split('?')[0]
                                elif href.startswith('BV'):
                                    bvid = href.split('?')[0]
                                video_url = f"https://www.bilibili.com/video/{bvid}" if bvid else href
                                break
                    
                    # 获取封面图 - 尝试多种选择器
                    cover = ""
                    for selector in ['img', '[class*="cover"] img', '.bili-video-card__image img']:
                        cover_elem = await element.query_selector(selector)
                        if cover_elem:
                            cover = await cover_elem.get_attribute('src') or await cover_elem.get_attribute('data-src')
                            break
                    
                    # 获取统计数据 - 尝试多种选择器
                    stats_text = ""
                    for selector in ['.stats', '[class*="stats"]', '.bili-video-card__stats']:
                        stats_elem = await element.query_selector(selector)
                        if stats_elem:
                            stats_text = await stats_elem.inner_text()
                            break
                    
                    # 解析播放量
                    play_match = re.search(r'(\d+\.?\d*万?)', stats_text)
                    play_count = play_match.group(1) if play_match else "0"
                    
                    # 解析点赞数 - 尝试找第二或第三个数字
                    nums = re.findall(r'(\d+\.?\d*万?)', stats_text)
                    like_count = nums[1] if len(nums) > 1 else (nums[0] if nums else "0")
                    danmu_count = nums[2] if len(nums) > 2 else "0"
                    
                    # 获取作者信息 - 尝试多种选择器
                    author = ""
                    for selector in ['.up-name', '[class*="up"]', '.bili-video-card__author']:
                        author_elem = await element.query_selector(selector)
                        if author_elem:
                            author = await author_elem.inner_text()
                            break
                    author = author.strip() if author else "未知作者"
                    
                    video_info = {
                        "rank": idx + 1,
                        "title": title,
                        "video_url": video_url,
                        "bvid": bvid,
                        "cover": cover,
                        "play_count": play_count,
                        "like_count": like_count,
                        "danmu_count": danmu_count,
                        "author": author,
                        "platform": "bilibili"
                    }
                    videos.append(video_info)
                    print(f"  [{idx+1}] {title[:30]}... | 播放: {play_count} | 点赞: {like_count}")
                    
                except Exception as e:
                    print(f"  解析第 {idx+1} 个视频失败: {e}")
                    continue
                    
        except Exception as e:
            print(f"B站爬取失败: {e}")
        finally:
            await page.close()
        
        return videos
    
    async def crawl_douyin(self, keyword: str, top_n: int = 10) -> List[Dict]:
        """
        爬取 抖音 网页版 视频数据
        
        Args:
            keyword: 搜索关键词
            top_n: 获取前 N 个视频
            
        Returns:
            视频数据列表
        """
        print(f"\n{'='*50}")
        print(f"正在爬取 抖音: {keyword}")
        print(f"{'='*50}")
        
        videos = []
        page = await self.create_page()
        
        try:
            # 访问抖音搜索结果页
            search_url = f"https://www.douyin.com/search/{keyword}?search_source=normal_search&type=video"
            await page.goto(search_url)
            
            # 等待页面加载
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(5)  # 额外等待
            
            # 等待视频列表加载 - 尝试多种选择器
            try:
                await page.wait_for_selector('.video-card', timeout=20000)
            except:
                try:
                    await page.wait_for_selector('[class*="video-card"]', timeout=15000)
                except:
                    await asyncio.sleep(3)
            
            # 滚动加载更多视频
            for _ in range(5):
                await page.evaluate('window.scrollBy(0, 1000)')
                await asyncio.sleep(1)
            
            # 获取视频卡片列表 - 尝试多种选择器
            video_elements = []
            for selector in ['.video-card', '[class*="video-card"]', '[class*="VideoCard"]', '.douyin-right-card']:
                video_elements = await page.query_selector_all(selector)
                if video_elements:
                    print(f"  使用选择器: {selector}")
                    break
            
            video_elements = video_elements[:top_n]
            
            for idx, element in enumerate(video_elements):
                try:
                    # 获取标题
                    title_elem = await element.query_selector('[class*="title"]')
                    title = await title_elem.inner_text() if title_elem else ""
                    
                    # 获取视频链接
                    link_elem = await element.query_selector('a')
                    href = await link_elem.get_attribute('href') if link_elem else ""
                    if href and not href.startswith('http'):
                        href = "https://www.douyin.com" + href
                    
                    # 获取封面图
                    cover_elem = await element.query_selector('img')
                    cover = await cover_elem.get_attribute('src') if cover_elem else ""
                    
                    # 获取统计数据（播放量、点赞）
                    stats_elems = await element.query_selector_all('[class*="count"]')
                    play_count = "0"
                    like_count = "0"
                    
                    for stat_elem in stats_elems:
                        stat_text = await stat_elem.inner_text()
                        if '播放' in stat_text:
                            play_count = stat_text.replace('播放', '')
                        elif '赞' in stat_text:
                            like_count = stat_text.replace('赞', '')
                    
                    # 获取作者
                    author_elem = await element.query_selector('[class*="author"]')
                    author = await author_elem.inner_text() if author_elem else ""
                    
                    video_info = {
                        "rank": idx + 1,
                        "title": title.strip(),
                        "video_url": href or "",
                        "cover": cover,
                        "play_count": play_count.strip(),
                        "like_count": like_count.strip(),
                        "author": author.strip() if author else "",
                        "platform": "douyin"
                    }
                    videos.append(video_info)
                    print(f"  [{idx+1}] {title[:30]}... | 播放: {play_count} | 点赞: {like_count}")
                    
                except Exception as e:
                    print(f"  解析第 {idx+1} 个视频失败: {e}")
                    continue
                    
        except Exception as e:
            print(f"抖音爬取失败: {e}")
        finally:
            await page.close()
        
        return videos
    
    async def crawl_xiaohongshu(self, keyword: str, top_n: int = 10) -> List[Dict]:
        """
        爬取 小红书 视频数据
        
        Args:
            keyword: 搜索关键词
            top_n: 获取前 N 个视频
            
        Returns:
            视频数据列表
        """
        print(f"\n{'='*50}")
        print(f"正在爬取 小红书: {keyword}")
        print(f"{'='*50}")
        
        videos = []
        page = await self.create_page()
        
        try:
            # 访问小红书搜索页面
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51"
            await page.goto(search_url)
            
            # 等待页面加载
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(5)  # 额外等待
            
            # 等待内容加载 - 尝试多种选择器
            try:
                await page.wait_for_selector('.note-item', timeout=20000)
            except:
                try:
                    await page.wait_for_selector('[class*="note-item"]', timeout=15000)
                except:
                    await asyncio.sleep(3)
            
            # 滚动加载更多
            for _ in range(5):
                await page.evaluate('window.scrollBy(0, 800)')
                await asyncio.sleep(1)
            
            # 获取笔记列表 - 尝试多种选择器
            note_elements = []
            for selector in ['.note-item', '[class*="note-item"]', '[class*="note-card"]', '.feed-item']:
                note_elements = await page.query_selector_all(selector)
                if note_elements:
                    print(f"  使用选择器: {selector}")
                    break
            
            note_elements = note_elements[:top_n]
            
            for idx, element in enumerate(note_elements):
                try:
                    # 获取标题/描述
                    title_elem = await element.query_selector('.title')
                    if not title_elem:
                        title_elem = await element.query_selector('[class*="title"]')
                    title = await title_elem.inner_text() if title_elem else ""
                    
                    # 获取视频/笔记链接
                    link_elem = await element.query_selector('a')
                    href = await link_elem.get_attribute('href') if link_elem else ""
                    if href and not href.startswith('http'):
                        href = "https://www.xiaohongshu.com" + href
                    
                    # 获取封面图
                    cover_elem = await element.query_selector('img')
                    cover = await cover_elem.get_attribute('src') if cover_elem else ""
                    if not cover:
                        cover_elem = await element.query_selector('[class*="cover"] img')
                        cover = await cover_elem.get_attribute('src') if cover_elem else ""
                    
                    # 获取作者
                    author_elem = await element.query_selector('.author')
                    if not author_elem:
                        author_elem = await element.query_selector('[class*="author"]')
                    author = await author_elem.inner_text() if author_elem else ""
                    
                    # 获取点赞数
                    like_elem = await element.query_selector('.count')
                    if not like_elem:
                        like_elem = await element.query_selector('[class*="like"]')
                    like_count = await like_elem.inner_text() if like_elem else "0"
                    
                    # 获取收藏数
                    collect_elem = await element.query_selector('[class*="collect"] .count')
                    collect_count = await collect_elem.inner_text() if collect_elem else "0"
                    
                    video_info = {
                        "rank": idx + 1,
                        "title": title.strip(),
                        "video_url": href or "",
                        "cover": cover,
                        "like_count": like_count.strip(),
                        "collect_count": collect_count.strip(),
                        "author": author.strip() if author else "",
                        "platform": "xiaohongshu"
                    }
                    videos.append(video_info)
                    print(f"  [{idx+1}] {title[:30]}... | 点赞: {like_count} | 收藏: {collect_count}")
                    
                except Exception as e:
                    print(f"  解析第 {idx+1} 个笔记失败: {e}")
                    continue
                    
        except Exception as e:
            print(f"小红书爬取失败: {e}")
        finally:
            await page.close()
        
        return videos
    
    async def crawl_all(self, keyword: str, platforms: List[str] = None, top_n: int = 10) -> Dict[str, List[Dict]]:
        """
        爬取所有指定平台的数据
        
        Args:
            keyword: 搜索关键词
            platforms: 要爬取的平台列表，默认 ['bilibili', 'douyin', 'xiaohongshu']
            top_n: 每个平台获取前 N 个视频
            
        Returns:
            各平台视频数据的字典
        """
        if platforms is None:
            platforms = ['bilibili', 'douyin', 'xiaohongshu']
        
        print(f"\n{'#'*60}")
        print(f"# 开始爬取: {keyword}")
        print(f"# 目标平台: {', '.join(platforms)}")
        print(f"# 每个平台获取前 {top_n} 个视频")
        print(f"{'#'*60}")
        
        self.results = {}
        
        for platform in platforms:
            if platform == 'bilibili':
                self.results['bilibili'] = await self.crawl_bilibili(keyword, top_n)
            elif platform == 'douyin':
                self.results['douyin'] = await self.crawl_douyin(keyword, top_n)
            elif platform == 'xiaohongshu':
                self.results['xiaohongshu'] = await self.crawl_xiaohongshu(keyword, top_n)
            # 避免请求过快
            await asyncio.sleep(1)
        
        return self.results
    
    def save_to_json(self, filepath: str = None) -> str:
        """
        保存结果到 JSON 文件
        
        Args:
            filepath: 保存路径，默认使用 timestamp_关键词_videos.json
            
        Returns:
            保存的文件路径
        """
        if not self.results:
            print("没有数据可保存")
            return ""
        
        # 生成默认文件名
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"videos_{timestamp}.json"
        
        # 添加元信息
        output_data = {
            "metadata": {
                "crawl_time": datetime.now().isoformat(),
                "platforms": list(self.results.keys()),
                "total_videos": sum(len(v) for v in self.results.values())
            },
            "data": self.results
        }
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n数据已保存到: {filepath}")
        return filepath


async def main():
    """
    主函数 - 示例用法
    """
    # 搜索关键词
    keyword = "AI编程副业"
    
    # 是否显示浏览器（调试时设为 True）
    headless = False
    
    # 要爬取的平台
    platforms = ['bilibili', 'douyin', 'xiaohongshu']
    
    # 每个平台获取的视频数量
    top_n = 10
    
    # 使用异步上下文管理器
    async with VideoCrawler(headless=headless) as crawler:
        # 执行爬取
        results = await crawler.crawl_all(
            keyword=keyword,
            platforms=platforms,
            top_n=top_n
        )
        
        # 保存结果
        crawler.save_to_json()
    
    print("\n爬取完成!")
    
    # 打印汇总
    for platform, videos in results.items():
        print(f"\n{platform}: 共获取 {len(videos)} 个视频")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
