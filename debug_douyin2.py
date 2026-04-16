import time
import json
from DrissionPage import ChromiumPage, ChromiumOptions

# 连接浏览器
co = ChromiumOptions()
co.set_local_port(9222)
page = ChromiumPage(co)

# 访问抖音搜索页面
keyword = "AI编程副业"
page.get(f'https://www.douyin.com/search/{keyword}?type=video')
page.wait.load_start()
time.sleep(8)  # 等待页面完全加载

# 滚动页面加载更多
for i in range(3):
    page.scroll.to_bottom()
    time.sleep(2)

# 尝试获取嵌入的 JSON 数据
print("=== 尝试从页面获取 JSON 数据 ===")
html = page.html

# 查找 __UNIVERSAL_DATA_FOR_REHYDRATION__ 或类似的数据
import re

# 方法1: 查找 window.__INITIAL_DATA__
match = re.search(r'window\.__INITIAL_DATA__\s*=\s*({.*?});', html, re.DOTALL)
if match:
    print("找到 window.__INITIAL_DATA__")
    try:
        data = json.loads(match.group(1))
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    except:
        print("JSON 解析失败")

# 方法2: 查找 __UNIVERSAL_DATA_FOR_REHYDRATION__
match2 = re.search(r'__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.*?});', html, re.DOTALL)
if match2:
    print("\n找到 __UNIVERSAL_DATA_FOR_REHYDRATION__")
    try:
        data = json.loads(match2.group(1))
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    except:
        print("JSON 解析失败")

# 方法3: 获取页面中所有脚本内容
print("\n=== 查找数据脚本 ===")
scripts = page.eles('tag:script')
for script in scripts[:10]:
    try:
        src = script.attr('src')
        if src:
            print(f"Script src: {src[:80]}")
    except:
        pass

# 方法4: 尝试点击搜索结果（抖音可能需要交互才加载数据）
print("\n=== 尝试交互式加载 ===")
# 按Tab键尝试聚焦到搜索结果
page.actions.key('Tab')
page.actions.key('Tab')
time.sleep(2)

# 再滚动一次
page.scroll.to_bottom()
time.sleep(2)

# 再次检查页面
html2 = page.html
if 'video' in html2.lower():
    print("页面中包含 'video' 关键词")

# 方法5: 获取当前页面的URL
print(f"\n当前页面URL: {page.url}")

# 尝试获取抖音通用数据
print("\n=== 尝试获取抖音通用渲染数据 ===")
universal_data = page.run_js('return window.__UNIVERSAL_DATA_FOR_REHYDRATION__')
if universal_data:
    print("找到 universal data!")
    print(json.dumps(universal_data, indent=2, ensure_ascii=False)[:3000])

print("\n调试完成")
input("按回车键退出...")
