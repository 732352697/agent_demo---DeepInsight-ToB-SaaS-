import shutil
import os

src_dir = r"c:\Users\Chen\Desktop\agent_demo"
dst_dir = r"c:\Users\Chen\Desktop\agent_demo\Export_Agent3"

files_to_copy = [
    "ultimate_crawler.py",
    "debug_douyin.py",
    "debug_douyin2.py",
    "debug_douyin3.py",
    "topics_20260311.md",
]

import glob

json_files = glob.glob(os.path.join(src_dir, "verified_videos_*.json"))
for f in json_files:
    files_to_copy.append(os.path.basename(f))

for f in files_to_copy:
    src = os.path.join(src_dir, f)
    dst = os.path.join(dst_dir, f)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"✅ 复制: {f}")
    else:
        print(f"❌ 不存在: {f}")

print(f"\n🎉 完成！共复制 {len(files_to_copy)} 个文件到 Export_Agent3")
