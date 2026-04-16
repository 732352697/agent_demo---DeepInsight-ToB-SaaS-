"""Streamlit Web 应用 - DeepInsight 多智能体直播助手 (ToB SaaS 版本)"""

import streamlit as st
import time
import re
import json
import os
from datetime import datetime

import bcrypt
from multi_agent_core import (
    AgentCallbackHandler,
    run_director_agent,
    run_tech_anchor_agent,
    run_field_control_agent,
    extract_script_text,
    extract_obs_commands,
    run_business_agent,
    parse_business_assets,
    run_tutor_agent,
    run_judge_agent,
    parse_judge_report,
)
from obs_client import OBSController
from db_manager import (
    init_database,
    save_live_record,
    update_live_record,
    get_user_records,
    get_record_by_id,
    delete_record,
    get_record_count,
)


# ========== SaaS 多租户认证配置 ==========
USERS_CONFIG = {
    "admin": {
        "name": "Administrator",
        "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
    },
    "test": {
        "name": "Test User",
        "password": bcrypt.hashpw("test123".encode(), bcrypt.gensalt()).decode(),
    }
}


def init_session_state():
    """初始化 session state"""
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'name' not in st.session_state:
        st.session_state.name = None


def login_user(username: str, password: str) -> bool:
    """验证用户登录"""
    if username not in USERS_CONFIG:
        return False
    
    stored_hash = USERS_CONFIG[username]['password']
    if bcrypt.checkpw(password.encode(), stored_hash.encode()):
        st.session_state.authentication_status = True
        st.session_state.username = username
        st.session_state.name = USERS_CONFIG[username]['name']
        return True
    return False


def logout_user():
    """退出登录"""
    st.session_state.authentication_status = False
    st.session_state.username = None
    st.session_state.name = None
    st.session_state.messages = []
    st.session_state.current_outline = None
    st.session_state.current_topic = None
    st.session_state.action_queue = []
    st.session_state.business_assets_generated = False
    st.session_state.course_material = ""
    st.session_state.tutor_messages = []
    st.session_state.loaded_evaluation = ""
    st.session_state.is_history_mode = False
    st.session_state.director_outline = None
    st.session_state.anchor_output = None
    st.session_state.raw_script = None
    st.session_state.loaded_assets = {}


def render_login_page():
    """渲染登录页面"""
    st.set_page_config(
        page_title="DeepInsight - 登录",
        layout="centered",
    )
    
    st.title("🎙️ DeepInsight AI 直播助手")
    st.markdown("### ToB SaaS 企业版登录")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submit = st.form_submit_button("登录", type="primary")
            
            if submit:
                if login_user(username, password):
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
        
        st.markdown("---")
        st.markdown("**测试账号：**")
        st.code("admin / admin123")
        st.code("test / test123")
    
    st.stop()


# 初始化数据库
init_database()

# 初始化 session state
init_session_state()

# 检查登录状态
if not st.session_state.authentication_status:
    render_login_page()


# ========== 安全同步TTS生成函数 - 子进程隔离法 ==========
import subprocess
import base64
from mutagen.mp3 import MP3

def autoplay_audio(file_path: str, placeholder):
    """独立的前端播报渲染器"""
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
        placeholder.markdown(md, unsafe_allow_html=True)

def generate_tts_sync(text_content: str, file_path: str) -> bool:
    """使用 subprocess 调用系统命令，彻底物理隔离 asyncio 环境"""
    try:
        cmd = ["edge-tts", "--voice", "zh-CN-YunxiNeural", "--text", text_content, "--write-media", file_path]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"TTS CLI 生成致命错误: {e}")
        return False


# ========== 历史记录持久化函数 (基于 SQLite) ==========

def load_history():
    """加载当前用户的历史直播记录"""
    username = st.session_state.get('username')
    if not username:
        return []
    return get_user_records(username)


def save_to_history(live_topic: str, assets: dict, evaluation: str = "", action_queue: list = None, 
                    outline: str = "", anchor_output: str = "", raw_script: str = "", 
                    messages: list = None, tutor_messages: list = None):
    """保存直播资产和复盘报告到当前用户的历史记录"""
    username = st.session_state.get('username')
    if not username:
        return False
    
    return save_live_record(
        username=username,
        topic=live_topic,
        action_queue=action_queue or [],
        business_assets=assets or {},
        evaluation_report=evaluation,
        director_outline=outline,
        anchor_output=anchor_output,
        raw_script=raw_script,
        messages=messages or [],
        tutor_messages=tutor_messages or []
    )

def pack_assets_markdown(assets: dict, topic: str) -> str:
    """将商业资产打包成 Markdown 格式"""
    md = f"""# 🎙️ DeepInsight 直播商业资产包

**直播主题**: {topic}
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📚 第一部分：直播配套课程讲义

{assets.get('course_material', '（未生成）')}

---

## 📕 第二部分：小红书爆款引流文案

{assets.get('xiaohongshu', '（未生成）')}

---

## 🎵 第三部分：抖音短视频分镜脚本

{assets.get('douyin', '（未生成）')}

---

*本资产包由 DeepInsight AI 直播助手自动生成*


"""

    return md


st.set_page_config(
    page_title="DeepInsight AI 编程直播助手",
    layout="centered",
)

# 初始化 OBS 控制器（保持连接状态）
if "obs_controller" not in st.session_state:
    st.session_state.obs_controller = OBSController()
if "obs_connected" not in st.session_state:
    st.session_state.obs_connected = False

# ==================== 侧边栏 ====================
with st.sidebar:
    # 用户信息区域
    st.markdown("---")
    st.markdown("### 👤 当前用户")
    st.markdown(f"**登录账号**: {st.session_state.get('name', '未知')}")
    st.markdown(f"**用户名**: `{st.session_state.get('username', '')}`")
    
    if st.button("🚪 退出登录", key="logout_btn"):
        logout_user()
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 🎛️ OBS 导播台状态")

    if st.button("🔗 测试连接 OBS"):
        obs_ctrl = st.session_state.obs_controller
        success, msg = obs_ctrl.connect()
        if success:
            st.session_state.obs_connected = True
            st.session_state.obs_connection_msg = msg
            st.success(f"🟢 {msg}")
        else:
            st.session_state.obs_connected = False
            st.session_state.obs_connection_msg = msg
            st.error(f"🔴 {msg}")

    # 显示连接状态
    if st.session_state.get("obs_connected", False):
        st.markdown("🟢 **OBS 已连接**")
    else:
        msg = st.session_state.get("obs_connection_msg", "")
        if msg:
            st.error(f"🔴 {msg}")
        else:
            st.markdown("🔴 **OBS 未连接**")
        st.info("请确保 OBS 已启动且已开启 WebSocket 服务器")

    st.markdown("---")

    # ==================== 历史直播工作台 ====================
    st.markdown("### 🗂️ 历史直播工作台")

    history = load_history()

    if history:
        history_options = [f"#{r['id']} {r['topic'][:30]} ({r['created_at'][:10]})" for r in history]
        history_options.insert(0, "选择历史记录...")

        selected_history = st.selectbox("历史直播", history_options, index=0, key="history_select")

        if selected_history != "选择历史记录...":
            selected_idx = history_options.index(selected_history) - 1
            selected_record = history[selected_idx]

            st.markdown(f"**主题**: {selected_record.get('topic', '')}")
            st.markdown(f"**时间**: {selected_record.get('created_at', '')}")

            if selected_record.get('business_assets'):
                st.markdown("#### 已生成资产")
                assets = selected_record['business_assets']
                if assets.get('course_material'):
                    st.markdown("✅ 课程讲义")
                if assets.get('xiaohongshu'):
                    st.markdown("✅ 小红书文案")
                if assets.get('douyin'):
                    st.markdown("✅ 短视频脚本")

            if selected_record.get('evaluation_report'):
                with st.expander("查看复盘报告"):
                    st.markdown(selected_record['evaluation_report'])

            if st.button("🔄 加载此记录到主工作区", key="load_history_btn"):
                st.session_state.is_history_mode = True
                st.session_state.current_topic = selected_record.get('topic', '')
                st.session_state.action_queue = selected_record.get('action_queue', [])
                st.session_state.business_assets_generated = bool(selected_record.get('business_assets', {}).get('course_material', ''))
                st.session_state.course_material = selected_record.get('business_assets', {}).get('course_material', '')
                st.session_state.loaded_assets = selected_record.get('business_assets', {})
                st.session_state.loaded_evaluation = selected_record.get('evaluation_report', '')
                st.session_state.current_outline = selected_record.get('director_outline', '')
                st.session_state.director_outline = selected_record.get('director_outline', '')
                st.session_state.anchor_output = selected_record.get('anchor_output', '')
                st.session_state.raw_script = selected_record.get('raw_script', '')
                st.session_state.messages = selected_record.get('messages', [])
                st.session_state.tutor_messages = selected_record.get('tutor_messages', [])
                
                st.rerun()

            if st.button("📥 重新下载此资产包", key="redownload_btn"):
                assets_dict = selected_record.get('business_assets', {})
                assets_md = pack_assets_markdown(assets_dict, selected_record.get('topic', ''))
                st.download_button(
                    label="📥 下载 Markdown",
                    data=assets_md,
                    file_name=f"DeepInsight_商业资产包_{selected_record.get('created_at', '').replace(':', '-')}.md",
                    mime="text/markdown",
                    key="download_btn"
                )
    else:
        st.info("暂无历史记录")

    st.markdown("---")

    if st.button("✨ 开启全新直播策划", type="primary"):
        st.session_state.messages = []
        st.session_state.current_outline = None
        st.session_state.current_topic = None
        st.session_state.action_queue = []
        st.session_state.business_assets_generated = False
        st.session_state.course_material = ""
        st.session_state.tutor_messages = []
        st.session_state.loaded_evaluation = ""
        st.session_state.is_history_mode = False
        st.session_state.director_outline = None
        st.session_state.anchor_output = None
        st.session_state.raw_script = None
        st.session_state.loaded_assets = {}
        st.rerun()

    st.markdown("---")


if "messages" not in st.session_state:
    st.session_state.messages = []

if "is_history_mode" not in st.session_state:
    st.session_state.is_history_mode = False

if "director_outline" not in st.session_state:
    st.session_state.director_outline = None

if "anchor_output" not in st.session_state:
    st.session_state.anchor_output = None

if "raw_script" not in st.session_state:
    st.session_state.raw_script = None

if "loaded_assets" not in st.session_state:
    st.session_state.loaded_assets = {}


st.title("DeepInsight AI 编程直播助手")
st.markdown("**双 Agent 协作：直播策划 -> 技术主播 -> AI 语音 -> OBS 导播**")

if st.session_state.is_history_mode:
    st.success("📂 历史会话回显模式 - 仅展示历史数据，不会触发任何 LLM 调用")
    st.info(f"🎯 正在回显历史会话: {st.session_state.get('current_topic', '未命名')}")

st.markdown("---")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def render_director_section():
    """渲染直播策划大纲"""
    if st.session_state.director_outline:
        st.divider()
        st.markdown("### 第一阶段：直播策划")
        st.markdown("### 直播大纲与分镜")
        st.markdown(st.session_state.director_outline)


def render_anchor_section():
    """渲染技术主播代码和话术"""
    if st.session_state.anchor_output:
        st.divider()
        st.markdown("### 第二阶段：技术主播")
        
        code_start = st.session_state.anchor_output.find("```python")
        code_end = st.session_state.anchor_output.find("```", code_start + 10) if code_start != -1 else -1

        if code_start != -1 and code_end != -1:
            code_block = st.session_state.anchor_output[code_start:code_end + 3]
            st.markdown("### 实战代码 Demo")
            st.markdown(code_block)
            post_code_content = st.session_state.anchor_output[code_end + 3:]
            script_start = post_code_content.find("【极客风口播逐字稿】")
            if script_start != -1:
                rest_output = post_code_content[script_start:]
            else:
                rest_output = post_code_content
        else:
            st.markdown(st.session_state.anchor_output)
            script_start = st.session_state.anchor_output.find("【极客风口播逐字稿】")
            if script_start != -1:
                rest_output = st.session_state.anchor_output[script_start:]
            else:
                rest_output = ""

        if rest_output.strip():
            st.markdown("### 极客风口播逐字稿")
            st.markdown(rest_output)


def render_tts_section():
    """渲染 TTS 语音"""
    if st.session_state.get("raw_script"):
        st.divider()
        with st.spinner("检查语音文件..."):
            if os.path.exists("live_audio.mp3"):
                st.markdown("### AI 主播语音")
                st.audio("live_audio.mp3", format="audio/mp3")
            else:
                st.info("语音文件未生成，但文字稿已准备就绪")


def render_obs_commands():
    """渲染 OBS 指令"""
    if st.session_state.get("action_queue"):
        has_obs = any(item.get("type") == "obs" for item in st.session_state.action_queue)
        if has_obs:
            st.divider()
            st.markdown("### 自动化导播台监控")
            st.markdown("**📡 检测到 OBS 场景切换指令：**")

            scene_icons = {
                "主播近景": "🎤",
                "代码实战": "💻",
                "数据图表": "📊"
            }

            obs_count = 0
            for item in st.session_state.action_queue:
                if item.get("type") == "obs":
                    obs_count += 1
                    scene_name = item.get("scene", "未知")
                    icon = scene_icons.get(scene_name, "🎬")
                    st.markdown(f"{icon} **{obs_count}. 切换至 -> {scene_name}**")


def render_full_drill_button():
    """渲染全自动演练按钮"""
    if not st.session_state.is_history_mode and st.session_state.get("action_queue") and st.session_state.get("obs_connected"):
        has_text = any(item.get("type") == "text" for item in st.session_state.action_queue)
        if has_text:
            st.markdown("---")
            if st.button("🚀 开始全自动无人直播演练", type="primary"):
                st.write("=== 开始调试 ===")
                st.write("1. action_queue 是否存在:", "action_queue" in st.session_state)
                st.write("2. action_queue 内容:", st.session_state.get("action_queue", "未找到"))
                st.write("3. obs_connected:", st.session_state.get("obs_connected", False))
                
                try:
                    action_queue = st.session_state.get("action_queue", [])
                    if not action_queue:
                        st.error("🚨 严重错误：在系统记忆中找不到剧本队列！请确认是否已生成剧本，并存入了 st.session_state.action_queue。")
                        st.stop()
                        
                    st.info(f"🔍 自检通过：共找到 {len(action_queue)} 条演练指令。")
                    
                    if not st.session_state.get("obs_connected", False):
                        st.error("🔴 请先在左侧边栏点击【🔗 测试连接 OBS】确保绿灯亮起！")
                        st.stop()
                    
                    obs_ctrl = st.session_state.obs_controller
                    test_success, test_msg = obs_ctrl.test_connection()
                    if not test_success:
                        st.error(f"🔴 OBS 连接已断开: {test_msg}")
                        st.session_state.obs_connected = False
                        st.stop()
                    
                    status_placeholder = st.empty()
                    audio_player_box = st.empty()
                    
                    status_placeholder.info("🚀 全自动无人直播演练正式开始！")
                    
                    for i, chunk in enumerate(action_queue):
                        try:
                            if chunk["type"] == "obs":
                                scene_name = chunk["scene"]
                                status_placeholder.success(f"🎛️ 正在切换 OBS 场景 ➡️ 【{scene_name}】")
                                obs_ctrl.switch_scene(scene_name)
                                time.sleep(0.5)

                            elif chunk["type"] == "text":
                                text_content = chunk["content"]
                                status_placeholder.info(f"🎤 正在播报: {text_content[:20]}...")

                                audio_file = f"chunk_{i}.mp3"
                                if generate_tts_sync(text_content, audio_file):
                                    autoplay_audio(audio_file, audio_player_box)
                                    audio_length = MP3(audio_file).info.length
                                    time.sleep(audio_length + 0.2)
                                    audio_player_box.empty()
                                else:
                                    st.error(f"❌ 语音段 {i} 生成失败！")
                        except Exception as chunk_error:
                            st.error(f"执行步骤 {i} 时出错: {chunk_error}")
                            continue
                            
                    status_placeholder.success("🎉 全自动直播演练圆满完成！")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"💥 系统崩溃拦截: {str(e)}")


def render_live_workspace():
    """渲染完整的直播工作区（历史模式或新生成模式）"""
    render_director_section()
    render_anchor_section()
    render_tts_section()
    render_obs_commands()
    render_full_drill_button()


if st.session_state.is_history_mode:
    render_live_workspace()
elif st.session_state.director_outline and st.session_state.anchor_output:
    render_live_workspace()


if prompt := st.chat_input("请输入直播主题，例如：'规划一场关于最近 Cursor 更新的直播'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.is_history_mode = False

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        director_callback = AgentCallbackHandler()
        anchor_callback = AgentCallbackHandler()

        try:
            with st.status("直播编导 Agent 正在全网检索并撰写分镜...", state="running"):
                st.markdown("### 第一阶段：直播策划")
                director_outline = run_director_agent(prompt, director_callback)
                st.markdown("### 直播大纲与分镜")
                st.markdown(director_outline)

            if director_callback.thought_steps:
                with st.expander("策划 Agent 思考过程", expanded=False):
                    for step in director_callback.thought_steps:
                        st.markdown(f"**{step['icon']} {step['title']}**")
                        st.markdown(step['content'])
                        st.divider()

            st.divider()

            with st.status("技术主播 Agent 正在接手，准备实战代码与话术...", state="running"):
                st.markdown("### 第二阶段：技术主播")
                anchor_output = run_tech_anchor_agent(director_outline, anchor_callback)

                st.markdown("### 实战代码 Demo")
                code_start = anchor_output.find("```python")
                code_end = anchor_output.find("```", code_start + 10) if code_start != -1 else -1

                if code_start != -1 and code_end != -1:
                    code_block = anchor_output[code_start:code_end + 3]
                    st.markdown(code_block)
                    post_code_content = anchor_output[code_end + 3:]
                    
                    script_start = post_code_content.find("【极客风口播逐字稿】")
                    if script_start != -1:
                        rest_output = post_code_content[script_start:]
                    else:
                        rest_output = post_code_content
                else:
                    st.markdown(anchor_output)
                    script_start = anchor_output.find("【极客风口播逐字稿】")
                    if script_start != -1:
                        rest_output = anchor_output[script_start:]
                    else:
                        rest_output = ""

                if rest_output.strip():
                    st.markdown("### 极客风口播逐字稿")
                    st.markdown(rest_output)

            if anchor_callback.thought_steps:
                with st.expander("主播 Agent 思考过程", expanded=False):
                    for step in anchor_callback.thought_steps:
                        st.markdown(f"**{step['icon']} {step['title']}**")
                        st.markdown(step['content'])
                        st.divider()

            st.divider()

            with st.spinner("正在生成主播语音包..."):
                if rest_output.strip():
                    cleaned_text, obs_commands = extract_obs_commands(rest_output)
                else:
                    cleaned_text, obs_commands = extract_obs_commands(anchor_output)

                tts_result = generate_tts_sync(cleaned_text, "live_audio.mp3")

                if tts_result:
                    st.markdown("### AI 主播语音")
                    st.audio("live_audio.mp3", format="audio/mp3")
                else:
                    st.warning("AI 语音生成失败，但文字稿已准备就绪")

            if obs_commands:
                st.divider()
                st.markdown("### 自动化导播台监控")
                st.markdown("**📡 检测到 OBS 场景切换指令：**")

                scene_icons = {
                    "主播近景": "🎤",
                    "代码实战": "💻",
                    "数据图表": "📊"
                }

                for cmd in obs_commands:
                    icon = scene_icons.get(cmd["scene"], "🎬")
                    st.markdown(f"{icon} **{cmd['order']}. 切换至 -> {cmd['scene']}**")

                st.session_state.obs_commands = obs_commands
                st.session_state.raw_script = rest_output
                
                raw_script = rest_output
                obs_pattern = r'\[OBS_CMD:\s*([^\]]+)\]'
                parts = re.split(f'({obs_pattern})', raw_script)
                
                action_queue = []
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    obs_match = re.match(obs_pattern, part)
                    if obs_match:
                        action_queue.append({"type": "obs", "scene": obs_match.group(1).strip()})
                    elif part:
                        sentences = re.split(r'([。！？.!?])', part)
                        current_text = ""
                        for sent in sentences:
                            current_text += sent
                            if sent in '。！？.!?':
                                if current_text.strip():
                                    action_queue.append({"type": "text", "content": current_text.strip()})
                                current_text = ""
                        if current_text.strip():
                            action_queue.append({"type": "text", "content": current_text.strip()})
                
                st.session_state.action_queue = action_queue
                st.session_state.action_queue_built = True

                st.markdown("---")
                if st.button("🚀 开始全自动无人直播演练", type="primary"):
                    st.write("=== 开始调试 ===")
                    st.write("1. action_queue 是否存在:", "action_queue" in st.session_state)
                    st.write("2. action_queue 内容:", st.session_state.get("action_queue", "未找到"))
                    st.write("3. obs_connected:", st.session_state.get("obs_connected", False))
                    
                    try:
                        action_queue = st.session_state.get("action_queue", [])
                        if not action_queue:
                            st.error("🚨 严重错误：在系统记忆中找不到剧本队列！请确认是否已生成剧本，并存入了 st.session_state.action_queue。")
                            st.stop()
                            
                        st.info(f"🔍 自检通过：共找到 {len(action_queue)} 条演练指令。")
                        
                        if not st.session_state.get("obs_connected", False):
                            st.error("🔴 请先在左侧边栏点击【🔗 测试连接 OBS】确保绿灯亮起！")
                            st.stop()
                        
                        obs_ctrl = st.session_state.obs_controller
                        test_success, test_msg = obs_ctrl.test_connection()
                        if not test_success:
                            st.error(f"🔴 OBS 连接已断开: {test_msg}")
                            st.session_state.obs_connected = False
                            st.stop()
                        
                        status_placeholder = st.empty()
                        audio_player_box = st.empty()
                        
                        status_placeholder.info("🚀 全自动无人直播演练正式开始！")
                        
                        for i, chunk in enumerate(action_queue):
                            try:
                                if chunk["type"] == "obs":
                                    scene_name = chunk["scene"]
                                    status_placeholder.success(f"🎛️ 正在切换 OBS 场景 ➡️ 【{scene_name}】")
                                    obs_ctrl.switch_scene(scene_name)
                                    time.sleep(0.5)

                                elif chunk["type"] == "text":
                                    text_content = chunk["content"]
                                    status_placeholder.info(f"🎤 正在播报: {text_content[:20]}...")

                                    audio_file = f"chunk_{i}.mp3"
                                    if generate_tts_sync(text_content, audio_file):
                                        autoplay_audio(audio_file, audio_player_box)
                                        audio_length = MP3(audio_file).info.length
                                        time.sleep(audio_length + 0.2)
                                        audio_player_box.empty()
                                    else:
                                        st.error(f"❌ 语音段 {i} 生成失败！")
                            except Exception as chunk_error:
                                st.error(f"执行步骤 {i} 时出错: {chunk_error}")
                                continue
                                
                        status_placeholder.success("🎉 全自动直播演练圆满完成！")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"💥 系统崩溃拦截: {str(e)}")
            else:
                st.info("未检测到 OBS 指令，请确保剧本中使用了 [OBS_CMD: 场景名称] 格式")

            final_response = f"### 直播策划完成\n\n**大纲与分镜：**\n\n{director_outline}\n\n---\n\n**代码与话术：**\n\n{anchor_output}"

            st.session_state.current_outline = director_outline
            st.session_state.current_topic = prompt
            st.session_state.director_outline = director_outline
            st.session_state.anchor_output = anchor_output
            st.session_state.is_history_mode = False

            messages = st.session_state.messages
            tutor_messages = st.session_state.get("tutor_messages", [])
            save_to_history(
                prompt, 
                st.session_state.get("loaded_assets", {}), 
                st.session_state.get("loaded_evaluation", ""), 
                st.session_state.get("action_queue", []),
                director_outline,
                anchor_output,
                rest_output,
                messages,
                tutor_messages
            )

        except Exception as e:
            final_response = f"抱歉，发生了一些错误：{str(e)}"
            st.error(final_response)

    st.session_state.messages.append({"role": "assistant", "content": final_response})


# ==================== 弹幕互动区 ====================
if st.session_state.get("current_outline"):
    st.divider()
    st.markdown("### 💬 实时弹幕互动区")

    # 弹幕输入框
    danmu = st.chat_input("模拟观众发送弹幕（例如：Cursor收费吗？）")

    if danmu:
        with st.chat_message("user"):
            st.write(danmu)

        with st.chat_message("assistant"):
            try:
                st.markdown("### 🎯 场控答疑")
                field_callback = AgentCallbackHandler()
                reply_text = run_field_control_agent(danmu, st.session_state.current_outline, field_callback)

                st.markdown(reply_text)

                # 生成回复语音
                with st.spinner("正在生成场控回复语音..."):
                    tts_result = generate_tts_sync(reply_text, "reply_audio.mp3")
                    if tts_result:
                        st.markdown("### 🎤 场控语音回复")
                        st.audio("reply_audio.mp3", format="audio/mp3")
                    else:
                        st.warning("语音生成失败，但文字回复已准备就绪")

            except Exception as e:
                st.error(f"场控答疑出错：{str(e)}")


# ==================== 商业化与营销分发引擎 ====================
st.divider()
st.markdown("💰 **直播后商业资产一键生成引擎**")

if st.session_state.get("action_queue") is not None and (st.session_state.get("action_queue") or st.session_state.get("director_outline")):
    if st.session_state.get("business_assets_generated", False) and st.session_state.get("course_material", ""):
        if st.session_state.is_history_mode:
            st.info("📂 历史模式：仅展示商业资产")
        
        asset_1 = st.session_state.get("course_material", "")
        assets = st.session_state.get("loaded_assets", {})
        asset_2 = assets.get("xiaohongshu", "")
        asset_3 = assets.get("douyin", "")

        tab1, tab2, tab3 = st.tabs([
            "📚 知识沉淀 (课程讲义)",
            "📕 公域引流 (小红书文案)",
            "🎵 裂变传播 (短视频分镜)"
        ])

        with tab1:
            if asset_1:
                st.markdown(asset_1)
                st.success("📚 课程讲义已生成，可直接复制使用！")
            else:
                st.warning("未能生成课程讲义")

        with tab2:
            if asset_2:
                st.markdown(asset_2)
                st.success("📕 小红书文案已生成，可直接复制使用！")
            else:
                st.warning("未能生成小红书文案")

        with tab3:
            if asset_3:
                st.markdown(asset_3)
                st.success("🎵 短视频脚本已生成，可直接复制使用！")
            else:
                st.warning("未能生成短视频脚本")

        if asset_1 or asset_2 or asset_3:
            assets_dict = {
                "course_material": asset_1 or "",
                "xiaohongshu": asset_2 or "",
                "douyin": asset_3 or ""
            }
            assets_md = pack_assets_markdown(assets_dict, st.session_state.get("current_topic", ""))
            st.download_button(
                label="📥 一键下载全套商业资产 (Markdown)",
                data=assets_md,
                file_name=f"DeepInsight_商业资产包_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
    else:
        st.markdown("✅ 检测到剧本数据，可以生成商业变现资产")

        if not st.session_state.is_history_mode:
            if st.button("🎁 一键提取商业变现资产 (课程 / 小红书 / 短视频)", type="primary"):
                with st.spinner("🚀 顶级知识IP操盘手正在为你打造变现资产..."):
                    try:
                        action_queue = st.session_state.get("action_queue", [])
                        if not action_queue:
                            st.error("剧本队列为空，无法生成商业资产")
                            st.stop()

                        full_script_parts = []
                        for item in action_queue:
                            if item.get("type") == "text":
                                full_script_parts.append(item.get("content", ""))
                        full_script = "\n".join(full_script_parts)

                        if not full_script.strip():
                            st.error("未找到有效的文本内容，请确认剧本是否包含口播稿")
                            st.stop()

                        business_callback = AgentCallbackHandler()
                        business_output = run_business_agent(full_script, business_callback)

                        if business_callback.thought_steps:
                            with st.expander("商业运营 Agent 思考过程", expanded=False):
                                for step in business_callback.thought_steps:
                                    st.markdown(f"**{step['icon']} {step['title']}**")
                                    st.markdown(step['content'])
                                    st.divider()

                        asset_1, asset_2, asset_3 = parse_business_assets(business_output)

                        st.success("✅ 商业资产生成完成！")

                        if asset_1:
                            st.session_state.course_material = asset_1
                            st.session_state.business_assets_generated = True

                        tab1, tab2, tab3 = st.tabs([
                            "📚 知识沉淀 (课程讲义)",
                            "📕 公域引流 (小红书文案)",
                            "🎵 裂变传播 (短视频分镜)"
                        ])

                        with tab1:
                            if asset_1:
                                st.markdown(asset_1)
                                st.success("📚 课程讲义已生成，可直接复制使用！")
                            else:
                                st.warning("未能生成课程讲义")

                        with tab2:
                            if asset_2:
                                st.markdown(asset_2)
                                st.success("📕 小红书文案已生成，可直接复制使用！")
                            else:
                                st.warning("未能生成小红书文案")

                        with tab3:
                            if asset_3:
                                st.markdown(asset_3)
                                st.success("🎵 短视频脚本已生成，可直接复制使用！")
                            else:
                                st.warning("未能生成短视频脚本")

                        if asset_1 or asset_2 or asset_3:
                            current_topic = st.session_state.get("current_topic", "未命名直播")
                            assets_dict = {
                                "course_material": asset_1 or "",
                                "xiaohongshu": asset_2 or "",
                                "douyin": asset_3 or ""
                            }
                            action_queue = st.session_state.get("action_queue", [])
                            director_outline = st.session_state.get("director_outline", "")
                            anchor_output = st.session_state.get("anchor_output", "")
                            raw_script = st.session_state.get("raw_script", "")
                            messages = st.session_state.get("messages", [])
                            tutor_messages = st.session_state.get("tutor_messages", [])
                            save_to_history(
                                current_topic, 
                                assets_dict, 
                                st.session_state.get("loaded_evaluation", ""), 
                                action_queue,
                                director_outline,
                                anchor_output,
                                raw_script,
                                messages,
                                tutor_messages
                            )
                            st.session_state.loaded_assets = assets_dict

                            assets_md = pack_assets_markdown(assets_dict, current_topic)
                            st.download_button(
                                label="📥 一键下载全套商业资产 (Markdown)",
                                data=assets_md,
                                file_name=f"DeepInsight_商业资产包_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown"
                            )

                    except Exception as e:
                        st.error(f"商业资产生成出错：{str(e)}")
else:
    st.info("ℹ️ 请先完成直播策划，生成剧本后即可提取商业变现资产")


# ==================== VIP 课后助教模块 ====================
st.divider()
st.markdown("👨‍🏫 **专属 VIP 课后助教 (基于本场直播知识库)**")

if "tutor_messages" not in st.session_state:
    st.session_state.tutor_messages = []

if "business_assets_generated" not in st.session_state:
    st.session_state.business_assets_generated = False

if "course_material" not in st.session_state:
    st.session_state.course_material = ""

if st.session_state.get("business_assets_generated", False) and st.session_state.get("course_material", ""):
    if st.session_state.is_history_mode:
        st.info("📂 历史模式：仅展示助教对话记录")
    else:
        st.success("✅ 已加载本场直播课程讲义，可以开始提问")

    for msg in st.session_state.tutor_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.is_history_mode:
        if prompt := st.chat_input("向助教提问本节课相关的代码问题..."):
            st.session_state.tutor_messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                try:
                    with st.spinner("VIP 助教正在思考..."):
                        course_material = st.session_state.course_material
                        chat_history = st.session_state.tutor_messages[:-1]

                        tutor_callback = AgentCallbackHandler()
                        answer = run_tutor_agent(
                            user_question=prompt,
                            course_material=course_material,
                            chat_history=chat_history,
                            callback=tutor_callback
                        )

                        st.markdown(answer)
                        st.session_state.tutor_messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error(f"助教回答出错：{str(e)}")
else:
    st.info("ℹ️ 请先在上方点击【一键提取商业变现资产】生成课程讲义，然后就可以向助教提问了")


# ==================== 智能复盘与评分引擎 ====================
st.divider()
st.markdown("📊 **直播全链路智能复盘报告 (LLM-as-a-Judge)**")

if st.session_state.get("action_queue") is not None and (st.session_state.get("action_queue") or st.session_state.get("director_outline")):
    if st.session_state.get("loaded_evaluation", ""):
        if st.session_state.is_history_mode:
            st.info("📂 历史模式：仅展示复盘报告")
        
        loaded_eval = st.session_state.loaded_evaluation
        report = parse_judge_report(loaded_eval)

        if report["radar"]:
            st.markdown("### 🎯 核心指标雷达")
            col1, col2, col3 = st.columns(3)

            import re
            geek_score = 0
            interaction_score = 0
            commerce_score = 0

            geek_match = re.search(r"极客硬核度得分[：:]\s*(\d+)", report["radar"])
            if geek_match:
                geek_score = int(geek_match.group(1))

            interaction_match = re.search(r"互动引导率得分[：:]\s*(\d+)", report["radar"])
            if interaction_match:
                interaction_score = int(interaction_match.group(1))

            commerce_match = re.search(r"商业转化埋点得分[：:]\s*(\d+)", report["radar"])
            if commerce_match:
                commerce_score = int(commerce_match.group(1))

            with col1:
                st.metric("极客硬核度", f"{geek_score}分", delta=None)
            with col2:
                st.metric("互动引导率", f"{interaction_score}分", delta=None)
            with col3:
                st.metric("商业转化埋点", f"{commerce_score}分", delta=None)

            avg_score = (geek_score + interaction_score + commerce_score) / 3
            st.progress(avg_score / 100, text=f"综合健康度: {avg_score:.1f}分")

        if report["highlights"]:
            st.markdown("### ✨ 高光时刻")
            st.markdown(report["highlights"])

        if report["risks"]:
            st.markdown("### ⚠️ 流失风险点")
            st.markdown(report["risks"])

        if report["suggestions"]:
            st.markdown("### 💡 下期优化建议")
            st.markdown(report["suggestions"])
    else:
        st.markdown("✅ 检测到剧本数据，可以生成复盘报告")

        if not st.session_state.is_history_mode:
            if st.button("📈 一键生成本场直播体检报告", type="primary"):
                with st.spinner("🔍 LLM 裁判正在对本场直播进行全链路复盘..."):
                    try:
                        action_queue = st.session_state.get("action_queue", [])
                        if not action_queue:
                            st.error("剧本队列为空，无法生成复盘报告")
                            st.stop()

                        full_script_parts = []
                        for item in action_queue:
                            if item.get("type") == "text":
                                full_script_parts.append(item.get("content", ""))
                        full_script = "\n".join(full_script_parts)

                        if not full_script.strip():
                            st.error("未找到有效的文本内容，请确认剧本是否包含口播稿")
                            st.stop()

                        danmu_history = ""
                        if "messages" in st.session_state:
                            danmu_messages = [m for m in st.session_state.messages if m.get("role") == "user"]
                            if danmu_messages:
                                danmu_history = "\n".join([f"观众提问: {m['content']}" for m in danmu_messages])

                        judge_callback = AgentCallbackHandler()
                        judge_output = run_judge_agent(full_script, danmu_history, judge_callback)

                        if judge_callback.thought_steps:
                            with st.expander("裁判 Agent 思考过程", expanded=False):
                                for step in judge_callback.thought_steps:
                                    st.markdown(f"**{step['icon']} {step['title']}**")
                                    st.markdown(step['content'])
                                    st.divider()

                        report = parse_judge_report(judge_output)

                        st.success("✅ 直播体检报告生成完成！")

                        if report["radar"]:
                            st.markdown("### 🎯 核心指标雷达")
                            col1, col2, col3 = st.columns(3)

                            import re
                            geek_score = 0
                            interaction_score = 0
                            commerce_score = 0

                            geek_match = re.search(r"极客硬核度得分[：:]\s*(\d+)", report["radar"])
                            if geek_match:
                                geek_score = int(geek_match.group(1))

                            interaction_match = re.search(r"互动引导率得分[：:]\s*(\d+)", report["radar"])
                            if interaction_match:
                                interaction_score = int(interaction_match.group(1))

                            commerce_match = re.search(r"商业转化埋点得分[：:]\s*(\d+)", report["radar"])
                            if commerce_match:
                                commerce_score = int(commerce_match.group(1))

                            with col1:
                                st.metric("极客硬核度", f"{geek_score}分", delta=None)
                            with col2:
                                st.metric("互动引导率", f"{interaction_score}分", delta=None)
                            with col3:
                                st.metric("商业转化埋点", f"{commerce_score}分", delta=None)

                            avg_score = (geek_score + interaction_score + commerce_score) / 3
                            st.progress(avg_score / 100, text=f"综合健康度: {avg_score:.1f}分")

                        if report["highlights"]:
                            st.markdown("### ✨ 高光时刻")
                            st.markdown(report["highlights"])

                        if report["risks"]:
                            st.markdown("### ⚠️ 流失风险点")
                            st.markdown(report["risks"])

                        if report["suggestions"]:
                            st.markdown("### 💡 下期优化建议")
                            st.markdown(report["suggestions"])

                        st.success("📊 复盘报告已生成完毕，可作为下期直播的重要参考！")

                        current_topic = st.session_state.get("current_topic", "未命名直播")
                        assets_dict = st.session_state.get("loaded_assets", {})
                        action_queue = st.session_state.get("action_queue", [])
                        director_outline = st.session_state.get("director_outline", "")
                        anchor_output = st.session_state.get("anchor_output", "")
                        raw_script = st.session_state.get("raw_script", "")
                        messages = st.session_state.get("messages", [])
                        tutor_messages = st.session_state.get("tutor_messages", [])

                        history = load_history()
                        if history and len(history) > 0:
                            last_record = history[-1]
                            record_id = last_record.get('id')
                            if record_id:
                                update_live_record(
                                    username=st.session_state.username,
                                    record_id=record_id,
                                    evaluation_report=judge_output,
                                    director_outline=director_outline,
                                    anchor_output=anchor_output,
                                    raw_script=raw_script,
                                    messages=messages,
                                    tutor_messages=tutor_messages,
                                    business_assets=assets_dict,
                                    action_queue=action_queue
                                )

                    except Exception as e:
                        st.error(f"复盘报告生成出错：{str(e)}")
else:
    st.info("ℹ️ 请先完成直播策划，生成剧本后即可生成复盘报告")
