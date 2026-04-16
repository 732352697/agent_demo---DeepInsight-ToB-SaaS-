import asyncio
import edge_tts

async def test():
    c = edge_tts.Communicate("测试语音", voice="zh-CN-YunxiNeural")
    await c.save("test_audio.mp3")
    return "OK"

print(asyncio.run(test()))
