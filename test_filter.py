#!/usr/bin/env python3
"""测试文本过滤规则"""

from multi_agent_core import extract_obs_commands

test_text = """极客风口播逐字稿
实战代码 Demo
【极客风口播逐字稿】
[OBS_CMD:主播近景]
(开场音乐渐弱)
（开场音乐响起，主播充满激情地面对镜头）
嘿！各位极客朋友们，大家晚上好！欢迎来到我们的技术直播间！我是你们的老朋友，技术主播CodeGeek！
(看向镜头，充满激情)
（看向镜头，微笑）
看到屏幕上这个酷炫的编辑器了吗？没错，今天我们要聊的就是——Cursor！但今天不是普通的介绍，而是深度解析它的最新更新！准备好迎接AI编程的新纪元了吗？
(挥手示意)
（拿起水杯喝了一口）
让我看看弹幕，有多少朋友已经在用Cursor了？打个1让我看看！还没用的朋友打个2！
(微笑)
（点头示意）
哇，这么多1，看来大家都是懂行的！
[OBS_CMD:数据图表]"""

print("原始文本:")
print(test_text)
print("\n" + "="*50 + "\n")

cleaned_text, obs_commands = extract_obs_commands(test_text)

print("清洗后的文本 (用于TTS):")
print(cleaned_text)
print("\n" + "="*50 + "\n")

print("提取的OBS指令:")
for cmd in obs_commands:
    print(f"{cmd['order']}. {cmd['scene']}")