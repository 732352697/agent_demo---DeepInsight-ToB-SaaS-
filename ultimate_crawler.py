import re
import os
import subprocess
import urllib.parse
import requests
import time
import json
import os
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

class UltimateCrawler:
    def __init__(self):
        print("正在尝试接管本地 Chrome 浏览器...")
        # 配置连接本地已经打开的 9222 端口的浏览器
        co = ChromiumOptions()
        co.set_local_port(9222)
        
        try:
            self.page = ChromiumPage(co)
            print("浏览器接管成功！风控护盾已开启。")
        except Exception as e:
            print(f"接管失败！请确保你已经通过命令行开启了 9222 端口的 Chrome 浏览器。\n错误信息: {e}")
            exit()

    def crawl_bilibili(self, keyword, top_n=10):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 开始强攻 B站: {keyword}")
        self.page.get(f'https://search.bilibili.com/all?keyword={keyword}&search_type=video')
        self.page.wait.load_start()
        time.sleep(3) # 模拟真人停顿
        
        # 模拟真人向下滚动两下
        self.page.scroll.to_bottom()
        time.sleep(1)
        self.page.scroll.to_bottom()
        time.sleep(2)

        videos = []
        # DrissionPage 强大的 css 定位
        cards = self.page.eles('.bili-video-card')
        
        for idx, card in enumerate(cards[:top_n]):
            try:
                title_ele = card.ele('.bili-video-card__info--tit', timeout=2)
                title = title_ele.text if title_ele else "未知标题"
                
                # 获取播放量和时间等统计信息
                stats = card.eles('.bili-video-card__stats--item')
                play_count = stats[0].text if len(stats) > 0 else "0"
                
                # 获取作者
                author_ele = card.ele('.bili-video-card__info--author', timeout=2)
                author = author_ele.text if author_ele else "未知作者"
                
                # 获取链接
                link = card.ele('tag:a').attr('href')
                if link and not link.startswith('http'):
                    link = 'https:' + link
                    
                videos.append({
                    "rank": idx + 1,
                    "title": title,
                    "play_count": play_count,
                    "author": author,
                    "video_url": link,
                    "platform": "bilibili"
                })
                print(f"  ✅ [B站] {title[:20]}... | 播放: {play_count} | 作者: {author}")
            except Exception as e:
                print(f"  ❌ 解析跳过: {e}")
                
        return videos

    def crawl_douyin(self, keyword, top_n=10):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 开始强攻 抖音: {keyword} (全自动 DOM + 滑块破解模式)")
        
        # 【修复点1】强制新开一个标签页，绝不覆盖之前的网页！
        tab = self.page.new_tab(f'https://www.douyin.com/search/{keyword}?type=video')
        tab.wait.load_start()
        time.sleep(random.randint(3, 7))

        # 【修复点2】全自动智能巡逻：检测并处理滑块验证码
        try:
            # 查找抖音常见的滑块按钮元素 (不同时期 class 可能变化，这是最常见的)
            slider = tab.ele('#secsdk-captcha-drag-wrapper', timeout=3)
            if not slider:
                slider = tab.ele('.secsdk-captcha-drag-icon', timeout=2)
                
            if slider:
                print("  ⚠️ 警报：检测到抖音滑块风控！正在启动全自动破解逻辑...")
                # 模拟真人鼠标：按住滑块 -> 向右匀速拖动约 160-200 像素 -> 松开
                # 注意：滑块距离每次可能不同，这里设定一个大概的拟人滑动动作
                tab.actions.hold(slider).move(180, 0, duration=1.2).release()
                print("  ✅ 自动滑块拖拽完成，等待页面刷新...")
                time.sleep(random.randint(3, 7)) # 等待验证通过后页面重新加载
        except Exception as e:
            # 如果没找到滑块，说明风控没触发，一切正常
            pass 

        # 模拟人手往下滚一滚，让视频卡片都渲染出来
        for _ in range(4):
            tab.scroll.down(600)
            time.sleep(random.randint(3, 7))
            
        videos = []
        try:
            # 注意：这里全部用 tab.eles 而不是 self.page.eles，确保只抓当前抖音标签页的数据
            links = tab.eles('@href:contains(/video/)')
            valid_count = 0
            
            for link_ele in links:
                if valid_count >= top_n: 
                    break
                
                href = link_ele.attr('href')
                if not href: continue
                if not href.startswith('http'): 
                    href = 'https:' + href
                
                # 去重
                if any(v['video_url'] == href for v in videos):
                    continue
                    
                # 往上找 3 层父节点，把整个视频卡片的框抓出来
                card = link_ele.parent(3)
                if not card: continue
                
                texts = card.text.split('\n') if card.text else []
                title = "未知标题"
                like_count = "0"
                author = "未知作者"
                
                for t in texts:
                    t = t.strip()
                    if not t: continue
                    if '赞' in t:
                        like_count = t.replace('赞', '')
                    elif len(t) > 10 and title == "未知标题":
                        title = t
                    elif len(t) < 15 and '赞' not in t and not t.isdigit() and t != title:
                        author = t
                
                videos.append({
                    "rank": valid_count + 1,
                    "title": title[:40] + '...',
                    "like_count": like_count,
                    "author": author,
                    "video_url": href,
                    "platform": "douyin"
                })
                print(f"  ✅ [抖音DOM提取] {title[:20]}... | 点赞: {like_count} | 作者: {author}")
                valid_count += 1
                
        except Exception as e:
            print(f"  ❌ 抖音DOM提取失败: {e}")
            
        return videos

    def crawl_xiaohongshu(self, keyword, top_n=10):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 开始强攻 小红书: {keyword}")
        self.page.get(f'https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51')
        self.page.wait.load_start()
        time.sleep(4)
        
        self.page.scroll.to_bottom()
        time.sleep(2)
        
        videos = []
        cards = self.page.eles('.note-item')
        
        for idx, card in enumerate(cards[:top_n]):
            try:
                title_ele = card.ele('.title', timeout=2)
                title = title_ele.text if title_ele else "未知"
                
                author_ele = card.ele('.name', timeout=2)
                author = author_ele.text if author_ele else "未知"
                
                like_ele = card.ele('.count', timeout=2)
                like_count = like_ele.text if like_ele else "0"
                
                link_ele = card.ele('tag:a', timeout=2)
                link = 'https://www.xiaohongshu.com' + link_ele.attr('href') if link_ele else ""
                
                videos.append({
                    "rank": idx + 1,
                    "title": title,
                    "author": author,
                    "like_count": like_count,
                    "video_url": link,
                    "platform": "xiaohongshu"
                })
                print(f"  ✅ [小红书] {title[:20]}... | 点赞: {like_count} | 作者: {author}")
            except Exception as e:
                pass
                
        return videos

def main():
    crawler = UltimateCrawler()
    keyword = "AI编程副业"
    
    # 开始执行三大平台抓取
    bili_data = crawler.crawl_bilibili(keyword)
    douyin_data = crawler.crawl_douyin(keyword)
    xhs_data = crawler.crawl_xiaohongshu(keyword)
    
    # 汇总数据
    final_data = {
        "metadata": {
            "crawl_time": datetime.now().isoformat(),
            "keyword": keyword,
            "total_videos": len(bili_data) + len(douyin_data) + len(xhs_data)
        },
        "data": {
            "bilibili": bili_data,
            "douyin": douyin_data,
            "xiaohongshu": xhs_data
        }
    }
    
    # 保存结果
    filename = f"verified_videos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 爬取大满贯！所有数据已绕过风控并成功保存至 {filename}")
    
    return final_data

if __name__ == "__main__":
    final_data = main()
    # ================= 新增：自动推送到 Dify 的代码 =================
    # 请将这里的 YOUR_DIFY_API_KEY 替换为你刚刚复制的密钥
    dify_api_key = "app-tLZRChjHqk6zWs5ivumrH7b4" 
    dify_api_url = "https://api.dify.ai/v1/chat-messages" # 如果你用的私有化部署，替换为你的域名
    
    print("\n🚀 正在将今日爆款数据发射至 Dify 1号智能体...")
    
    # 将 JSON 字典转为格式化的字符串
    data_str = json.dumps(final_data, ensure_ascii=False, indent=2)
    
    # 构造发给 Dify 的消息体
    payload = {
        "inputs": {}, 
        "query": (
            f"这是今天最新抓取的全网爆款视频数据：\n{data_str}\n\n"
            f"【最高指令约束】：\n"
            f"1. 必须严格深度分析这些点赞量和标题。\n"
            f"2. 必须输出整整 10 个短视频选题，少一个都不行！请用 1 到 10 明确标出序号。\n"
            f"3. 必须输出 2 个直播主题。\n"
            f"4. 不要省略、不要合并，请详细写出每个选题的钩子文案、痛点和内容结构！"
        ),
        "response_mode": "streaming",
        "user": "auto_crawler_bot"
    }
    
    headers = {
        "Authorization": f"Bearer {dify_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(dify_api_url, json=payload, headers=headers, stream=True)
        if response.status_code == 200:
            print("\n✅ Dify 1号智能体接收并处理成功！")
            print("================ Dify 的策划结果 ================")
            
            full_answer = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data:'):
                        try:
                            data = json.loads(line[5:])
                            if 'answer' in data:
                                chunk = data['answer']
                                print(chunk, end='', flush=True)
                                full_answer += chunk
                        except:
                            pass
            
            print("\n=================================================")
            
            md_filename = f"topics_{datetime.now().strftime('%Y%m%d')}.md"
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(full_answer)
            print(f"📝 结果已保存至 {md_filename}")
        else:
            print(f"❌ 推送给 Dify 失败，状态码: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")
        # 假设 full_answer 是 Dify 2号智能体返回的那一大段包含代码的文本
# full_answer = response.json().get('answer', '')

def sync_to_trae_cn(full_answer):
    print("\n🔗 正在启动 Trae CN 代码自动同步引擎...")
    
    # 1. 用正则表达式，精准把 Dify 生成的 Python 代码抠出来
    # 匹配 ```python 和 ``` 之间的所有内容
    code_match = re.search(r'```python\n(.*?)```', full_answer, re.DOTALL)
    
    if code_match:
        extracted_code = code_match.group(1)
        
        # 2. 在本地自动创建一个 Python 文件
        # 建议在你建一个专门放直播代码的文件夹
        save_dir = r"D:\Trae_Live_Codes" # 替换成你的实际路径
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        file_path = os.path.join(save_dir, "auto_generated_script.py")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(extracted_code)
        print(f"  ✅ 代码提取成功！已自动保存至: {file_path}")
        
        # 3. 【核心魔法】通过命令行直接唤醒 Trae CN 并打开这个文件！
        # 注意：需要确保 Trae 已经加入你电脑的环境变量。通常安装 Trae 时会自动加入。
        try:
            print("  🚀 正在自动唤醒 Trae CN...")
            # 使用 trae 命令打开文件（如果你用的是 Cursor 则是 cursor，VSCode 是 code）
            subprocess.Popen(["trae", file_path], shell=True)
            print("  🎉 同步完成！Trae CN 已就位，随时可开始直播演示！")
        except Exception as e:
            print(f"  ❌ 唤醒 Trae CN 失败，请检查命令行工具是否配置: {e}")
            # 备用方案：用系统默认程序打开
            os.startfile(file_path)
            
    else:
        print("  ⚠️ 未在 Dify 的回复中检测到 Python 代码块。")

# 测试调用
# sync_to_trae_cn(full_answer)