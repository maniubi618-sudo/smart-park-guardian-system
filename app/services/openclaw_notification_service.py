import os
import shutil
import requests
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger()

SNAPSHOT_DIR = Path(__file__).parent.parent / "snapshots"
QQ_MEDIA_DIR = os.path.expanduser("~/.openclaw/media/qqbot")


class OpenClawNotificationService:
    """Sends alarm notifications via OpenClaw hooks → QQ agent → QQ Bot (supports images)."""

    _enabled = False
    _gateway_url = "http://127.0.0.1:18789"
    _hook_path = "/hooks/park-alarm"
    _auth_token = "park-alarm-hook-token-2026"
    _timeout_seconds = 10

    @classmethod
    def configure(cls, config: dict):
        cls._enabled = config.get("enableOpenClaw", False)
        cls._gateway_url = config.get("openclawGatewayUrl", cls._gateway_url)
        cls._auth_token = config.get("openclawAuthToken", cls._auth_token)
        cls._timeout_seconds = config.get("openclawTimeout", 10)

    @classmethod
    def send_alarm_notification(cls, alarm_dict: dict) -> bool:
        if not cls._enabled:
            return False

        alarm_type_desc = alarm_dict.get("alarm_type_desc", "未知")
        camera_name = alarm_dict.get("camera_name", "")
        park_area = alarm_dict.get("park_area", "")
        alarm_time = alarm_dict.get("alarm_time", "")
        alarm_id = alarm_dict.get("alarm_id", "")
        snapshot_url = alarm_dict.get("snapshot_url", "")

        # 复制截图到 QQ media 目录，用完整绝对路径
        media_filename = cls._copy_to_qq_media(snapshot_url)
        media_tag = f"<qqmedia>{os.path.join(QQ_MEDIA_DIR, media_filename)}</qqmedia>" if media_filename else ""

        try:
            response = requests.post(
                f"{cls._gateway_url}{cls._hook_path}",
                headers={
                    "Authorization": f"Bearer {cls._auth_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "alarm_id": alarm_id,
                    "alarm_type_desc": alarm_type_desc,
                    "camera_name": camera_name,
                    "park_area": park_area,
                    "alarm_time": alarm_time,
                    "media_tag": media_tag,
                },
                timeout=cls._timeout_seconds,
            )
            if response.status_code == 200:
                logger.info(f"OpenClaw QQ通知已发送: Alarm#{alarm_id}")
                return True
            else:
                logger.error(f"OpenClaw通知失败: HTTP {response.status_code}, {response.text[:200]}")
        except requests.exceptions.Timeout:
            logger.error("OpenClaw通知超时")
        except requests.exceptions.ConnectionError:
            logger.error(f"OpenClaw通知失败: 无法连接 {cls._gateway_url}")
        except Exception as e:
            logger.error(f"OpenClaw通知异常: {e}")
        return False

    @classmethod
    def _copy_to_qq_media(cls, snapshot_url: str) -> str:
        """将截图复制到 QQ media 目录，返回文件名或空字符串"""
        if not snapshot_url:
            return ""
        filename = os.path.basename(snapshot_url)
        if not filename:
            return ""
        src = snapshot_url if os.path.isabs(snapshot_url) else str(SNAPSHOT_DIR / filename)
        if not os.path.exists(src):
            return ""
        try:
            os.makedirs(QQ_MEDIA_DIR, exist_ok=True)
            dst = os.path.join(QQ_MEDIA_DIR, filename)
            shutil.copy2(src, dst)
            return filename
        except Exception as e:
            logger.error(f"复制截图到QQ媒体目录失败: {e}")
            return ""
