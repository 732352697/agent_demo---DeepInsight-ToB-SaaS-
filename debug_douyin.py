import time
from DrissionPage import ChromiumPage, ChromiumOptions

# 连接浏览器
co = ChromiumOptions()
co.set_local_port(9222)
page = ChromiumPage(co)

# 访问抖音搜索页面
keyword = "AI编程副业"
page.get(f'https://www.douyin.com/search/{keyword}?type=video')
page.wait.load_start()
time.sleep(5)

# 滚动页面
page.scroll.to_bottom()
time.sleep(2)

# 获取页面中的所有链接
print("=== 页面中所有包含 'video' 的链接 ===")
all_links = page.eles('tag:a')
count = 0
for link in all_links:
    try:
        href = link.attr('href')
        if href and 'video' in href.lower():
            print(f"链接: {href}")
            count += 1
            if count > 20:
                break
    except:
        pass

print(f"\n总共找到 {count} 个包含 video 的链接")

# 尝试获取带有 data- 开头的元素
print("\n=== 尝试获取带有 data- 属性 的元素 ===")
data_elements = page.eles('[data-*]')
print(f"找到 {len(data_elements)} 个带 data- 属性的元素")

# 获取页面 HTML 的前 5000 字符来查看结构
print("\n=== 页面 HTML 结构预览 ===")
html = page.html
# 查找 video 相关的 class
import re
video_classes = re.findall(r'class="[^"]*video[^"]*"', html, re.I)
print("包含 video 的 class:")
for vc in set(video_classes[:20]):
    print(f"  {vc}")

input("按回车键退出...")
