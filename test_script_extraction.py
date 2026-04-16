#!/usr/bin/env python3
"""测试脚本提取逻辑"""

# 模拟技术主播Agent的输出
anchor_output = """实战代码 Demo

```python
# 示例代码
def hello():
    print("Hello, World!")
```

【极客风口播逐字稿】
[OBS_CMD:主播近景]
(开场音乐渐弱)
嘿！各位极客朋友们，大家晚上好！欢迎来到我们的技术直播间！我是你们的老朋友，技术主播CodeGeek！
(看向镜头，充满激情)
看到屏幕上这个酷炫的编辑器了吗？没错，今天我们要聊的就是——Cursor！但今天不是普通的介绍，而是深度解析它的最新更新！准备好迎接AI编程的新纪元了吗？
(挥手示意)
让我看看弹幕，有多少朋友已经在用Cursor了？打个1让我看看！还没用的朋友打个2！
(微笑)
哇，这么多1，看来大家都是懂行的！
[OBS_CMD:数据图表]"""

print("原始输出:")
print(anchor_output)
print("\n" + "="*50 + "\n")

# 模拟新的提取逻辑
code_start = anchor_output.find("```python")
code_end = anchor_output.find("```", code_start + 10) if code_start != -1 else -1

if code_start != -1 and code_end != -1:
    code_block = anchor_output[code_start:code_end + 3]
    print("提取的代码块:")
    print(code_block)
    print("\n" + "="*50 + "\n")
    
    # 提取代码块之后的内容
    post_code_content = anchor_output[code_end + 3:]
    
    # 找到【极客风口播逐字稿】标记
    script_start = post_code_content.find("【极客风口播逐字稿】")
    if script_start != -1:
        # 只提取【极客风口播逐字稿】部分
        rest_output = post_code_content[script_start:]
        print("提取的【极客风口播逐字稿】部分:")
        print(rest_output)
    else:
        # 如果没有找到标记，使用代码块之后的所有内容
        rest_output = post_code_content
        print("未找到【极客风口播逐字稿】标记，使用代码块之后的所有内容:")
        print(rest_output)
else:
    print("未找到代码块")
    # 尝试从完整输出中找到【极客风口播逐字稿】标记
    script_start = anchor_output.find("【极客风口播逐字稿】")
    if script_start != -1:
        rest_output = anchor_output[script_start:]
        print("提取的【极客风口播逐字稿】部分:")
        print(rest_output)
    else:
        rest_output = ""
        print("未找到【极客风口播逐字稿】标记")