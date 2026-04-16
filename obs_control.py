import obsws_python as obs
import time

print("🔌 正在绕过 n8n，直接连接本地 OBS...")

# 连接本地 OBS（因为之前关闭了密码鉴权，所以不需要填密码）
client = obs.ReqClient(host='localhost', port=4455)
print("✅ 连接成功！3秒后执行黑客级画面切换...")

time.sleep(3)

# 精准下达场景切换指令
client.set_current_program_scene("代码实操")
print("🎬 画面已成功切换至【代码实操】！全自动化底层跑通！")