import time
import json
import re
from DrissionPage import ChromiumPage, ChromiumOptions

# 连接浏览器
co = ChromiumOptions()
co.set_local_port(9222)
page = ChromiumPage(co)

# 尝试使用抖音移动端网页版
keyword = "AI编程副业"
print("=== 尝试抖音移动端网页版 ===")
page.get(f'https://m.douyin.com/search/{keyword}?type=video')
page.wait.load_start()
time.sleep(5)

# 滚动页面
page.scroll.to_bottom()
time.sleep(2)

# 获取所有链接
print("\n=== 获取所有链接 ===")
all_links = page.eles('tag:a')
count = 0
video_links = []
for link in all_links:
    try:
        href = link.attr('href')
        if href:
            if 'video' in href.lower() or '/aweme/' in href:
                print(f"视频链接: {href[:80]}")
                video_links.append(href)
                count += 1
                if count >= 15:
                    break
    except:
        pass

print(f"\n找到 {count} 个视频链接")

# 如果移动端不行，尝试桌面端的发现页
if count == 0:
    print("\n=== 尝试桌面端发现页 ===")
    page.get('https://www.douyin.com/discover')
    page.wait.load_start()
    time.sleep(5)
    
    page.scroll.to_bottom()
    time.sleep(2)
    
    all_links2 = page.eles('tag:a')
    count2 = 0
    for link in all_links2[:50]:
        try:
            href = link.attr('href')
            if href and 'video' in href.lower():
                print(f"视频链接: {href[:80]}")
                count2 += 1
                if count2 >= 10:
                    break
        except:
            pass
    print(f"发现页找到 {count2} 个视频链接")

# 尝试获取页面中的JSON数据
print("\n=== 尝试获取JSON数据 ===")
html = page.html
# 尝试匹配 JSON 数据
json_matches = re.findall(r'{[^{}]*"aweme_info"[^{}]*}', html)
print(f"找到 {len(json_matches)} 个可能的JSON")

# 获取 window.__DATA__ 
data = page.run_js('return window.__INITIAL_STATE__')
if data:
    print("找到 __INITIAL_STATE__")
    print(str(data)[:500])

print("\n=== 调试完成 ===")
input("按回车键退出...")
