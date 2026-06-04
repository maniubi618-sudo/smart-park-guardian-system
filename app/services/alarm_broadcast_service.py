#  告警广播服务模块
import asyncio
import base64
import os
import threading

from app.objects.alarm_case import AlarmCase
from app.services.websocket_manager import manager
from app.services.voice_broadcast_service import VoiceBroadcastService
from app.utils.logger import get_logger

logger = get_logger()

# -------------------------- 全局异步广播任务处理（使用独立线程运行事件循环，避免与FastAPI主线程冲突） --------------------------
# 1. 创建独立的asyncio事件循环，专门处理WebSocket广播（避免与FastAPI主循环冲突）
broadcast_loop = asyncio.new_event_loop()
# 2. 启动事件循环的守护线程（后台运行，不阻塞主程序退出）
broadcast_thread = threading.Thread(
    target=broadcast_loop.run_forever,
    daemon=True,
    name="WebSocket-Broadcast-Loop"
)
broadcast_thread.start()

def _snapshot_data_url_from_local_path(snapshot_url: str):
    """本地截图路径转 data URL；远端 URL 保持只发 snapshot_url。"""
    if not snapshot_url:
        return None

    first_snapshot = snapshot_url.split(",", 1)[0].strip()
    if not first_snapshot or first_snapshot.startswith(("http://", "https://")):
        return None

    if not os.path.isabs(first_snapshot):
        first_snapshot = os.path.abspath(first_snapshot)

    if not os.path.exists(first_snapshot):
        return None

    try:
        with open(first_snapshot, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception as e:
        logger.error(f"读取告警截图生成 data URL 失败: {e}")
        return None

async def _async_broadcast_alarm(alarm):
    """内部异步广播告警函数（供事件循环调用）"""
    alarm_dict = {
        "alarm_id": alarm.alarm_id,
        "camera_id": alarm.camera_id,
        "alarm_type": alarm.alarm_type,
        "alarm_status": alarm.alarm_status,
        "alarm_time": alarm.alarm_time.isoformat() if alarm.alarm_time else None,
        "snapshot_url": alarm.snapshot_url,
    }
    snapshot_data_url = _snapshot_data_url_from_local_path(alarm.snapshot_url)
    if snapshot_data_url:
        alarm_dict["snapshotDataUrl"] = snapshot_data_url
    await manager.broadcast(alarm_dict)

def sync_broadcast_alarm(alarm):
    """同步接口：将告警广播任务提交到全局事件循环（线程安全）"""
    logger.info(f"广播告警: Alarm ID={alarm.alarm_id}, 类型={AlarmCase.descs[alarm.alarm_type]}")
    asyncio.run_coroutine_threadsafe(
        _async_broadcast_alarm(alarm),
        loop=broadcast_loop
    )
    
    # 语音播报已禁用 - 如需开启请取消下方注释
    # try:
    #     import threading
    #     voice_thread = threading.Thread(
    #         target=VoiceBroadcastService.get_alarm_voice_text,
    #         args=(alarm.alarm_type, getattr(alarm, 'camera_name', '')),
    #         daemon=True,
    #         name="Voice-Broadcast"
    #     )
    #     voice_thread.start()
    # except Exception as e:
    #     logger.error(f"启动语音播报线程失败：{str(e)}")
