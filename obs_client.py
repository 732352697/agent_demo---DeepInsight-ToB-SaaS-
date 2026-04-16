"""OBS WebSocket 控制模块 - 用于实现无人导播。"""

import os
import asyncio
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv

try:
    import obsws_python as obs
    OBS_WS_AVAILABLE = True
except ImportError:
    OBS_WS_AVAILABLE = False


class OBSController:
    """OBS WebSocket 控制器类。"""

    def __init__(self, host: str = "localhost", port: int = 4455, password: Optional[str] = None):
        """初始化 OBS 控制器。

        Args:
            host: OBS WebSocket 服务器地址，默认 localhost
            port: OBS WebSocket 端口，默认 4455
            password: OBS WebSocket 密码，从环境变量读取
        """
        load_dotenv()
        self.host = host
        self.port = port
        self.password = password or os.getenv("OBS_WS_PASSWORD")
        self.client: Optional[obs.ReqClient] = None
        self.connected = False

    def connect(self) -> Tuple[bool, str]:
        """连接到 OBS WebSocket。

        Returns:
            (连接是否成功, 消息)
        """
        if not OBS_WS_AVAILABLE:
            return False, "obsws-python 库未安装，请运行: pip install obsws-python"

        try:
            self.client = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password,
                timeout=5
            )
            self.connected = True
            return True, "连接成功"
        except ConnectionRefusedError:
            self.connected = False
            return False, "无法连接到 OBS，请确保 OBS 已启动且 WebSocket 服务器已开启"
        except Exception as e:
            self.connected = False
            return False, f"连接失败: {str(e)}"

    def disconnect(self):
        """断开与 OBS 的连接。"""
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        self.connected = False
        self.client = None

    def switch_scene(self, scene_name: str) -> Tuple[bool, str]:
        """切换 OBS 场景。

        Args:
            scene_name: 目标场景名称

        Returns:
            (切换是否成功, 消息)
        """
        if not self.connected or not self.client:
            return False, "未连接到 OBS，请先点击'测试连接 OBS'按钮"

        try:
            self.client.set_current_program_scene(scene_name)
            return True, f"已切换到场景: {scene_name}"
        except Exception as e:
            return False, f"切换场景失败: {str(e)}"

    def get_current_scene(self) -> Tuple[Optional[str], str]:
        """获取当前场景。

        Returns:
            (当前场景名称, 消息)
        """
        if not self.connected or not self.client:
            return None, "未连接到 OBS"

        try:
            response = self.client.get_current_program_scene()
            return response.name, "获取当前场景成功"
        except Exception as e:
            return None, f"获取当前场景失败: {str(e)}"

    def get_scene_list(self) -> Tuple[List[Dict], str]:
        """获取场景列表。

        Returns:
            (场景列表, 消息)
        """
        if not self.connected or not self.client:
            return [], "未连接到 OBS"

        try:
            response = self.client.get_scene_list()
            scenes = [{"name": s.name, "index": s.index} for s in response.scenes]
            return scenes, "获取场景列表成功"
        except Exception as e:
            return [], f"获取场景列表失败: {str(e)}"

    def test_connection(self) -> Tuple[bool, str]:
        """测试 OBS 连接状态。

        Returns:
            (连接是否成功, 消息)
        """
        if not self.connected:
            return self.connect()

        try:
            self.client.get_version()
            return True, "OBS 连接正常"
        except Exception as e:
            self.connected = False
            return False, f"连接已断开: {str(e)}"


def create_obs_controller() -> OBSController:
    """创建 OBS 控制器的便捷函数。

    Returns:
        OBSController 实例
    """
    return OBSController()
