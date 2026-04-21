from typing import List, Optional, Dict
from fastapi import WebSocket
from app.utils.logger import get_logger

logger = get_logger()


class PhoneCameraManager:
    def __init__(self):
        self.phone_connections: Dict[str, WebSocket] = {}
        self.phone_metas: Dict[str, dict] = {}
        self.viewer_connections: List[WebSocket] = []

    async def connect_phone(self, websocket: WebSocket, meta: dict = None):
        uid = None
        if meta and meta.get('uid'):
            uid = meta['uid']
            if uid in self.phone_connections:
                try:
                    await self.phone_connections[uid].close()
                    logger.info(f"强制关闭旧手机连接: {uid}")
                except:
                    logger.info(f"旧手机连接已失效: {uid}")
                del self.phone_connections[uid]

        await websocket.accept()

        if uid:
            self.phone_connections[uid] = websocket
            if meta:
                self.phone_metas[uid] = meta
            logger.info(f"新手机摄像头已连接: {uid}, 当前连接数: {len(self.phone_connections)}")
            await self.broadcast_phone_update(uid, "phone_connected", meta)
        else:
            logger.warning("手机连接但没有提供UID")
            self.phone_connections[f"unknown_{id(websocket)}"] = websocket

    async def connect_viewer(self, websocket: WebSocket):
        await websocket.accept()
        self.viewer_connections.append(websocket)
        logger.info(f"观看端已连接，当前观看端数: {len(self.viewer_connections)}")
        await self.send_all_phones_to_viewer(websocket)

    async def send_all_phones_to_viewer(self, websocket: WebSocket):
        for uid, meta in self.phone_metas.items():
            try:
                await websocket.send_json({
                    "type": "phone_connected",
                    "uid": uid,
                    "meta": meta
                })
            except Exception as e:
                logger.error(f"发送手机信息到观看端失败: {e}")

    def disconnect_phone(self, websocket: WebSocket):
        uid_to_remove = None
        for uid, conn in self.phone_connections.items():
            if conn == websocket:
                uid_to_remove = uid
                break

        if uid_to_remove:
            del self.phone_connections[uid_to_remove]
            meta = self.phone_metas.pop(uid_to_remove, {})
            logger.info(f"手机摄像头已断开: {uid_to_remove}, 当前连接数: {len(self.phone_connections)}")

            import asyncio
            asyncio.create_task(self.broadcast_phone_update(uid_to_remove, "phone_disconnected", meta))
        else:
            for uid in list(self.phone_connections.keys()):
                if "unknown" in uid and self.phone_connections[uid] == websocket:
                    del self.phone_connections[uid]
                    logger.info("未知手机连接已断开")
                    break

    def disconnect_viewer(self, websocket: WebSocket):
        if websocket in self.viewer_connections:
            self.viewer_connections.remove(websocket)
            logger.info(f"观看端已断开，当前观看端数: {len(self.viewer_connections)}")

    async def forward_from_phone(self, data, uid: str = None):
        if not self.viewer_connections:
            logger.debug("没有观看端连接，跳过转发")
            return

        valid_viewers = []
        data_type = "bytes" if isinstance(data, bytes) else "text"
        data_size = len(data) if isinstance(data, bytes) else len(str(data))

        logger.debug(f"转发{uid or '未知'}的{data_type}数据({data_size}字节)到{len(self.viewer_connections)}个观看端")

        for viewer in self.viewer_connections:
            try:
                if isinstance(data, bytes):
                    await viewer.send_bytes(data)
                else:
                    await viewer.send_text(data)
                valid_viewers.append(viewer)
            except Exception as e:
                logger.error(f"转发数据到观看端失败: {e}")
                continue
        self.viewer_connections = valid_viewers

    async def broadcast_phone_update(self, uid: str, event_type: str, meta: dict = None):
        valid_viewers = []
        for viewer in self.viewer_connections:
            try:
                await viewer.send_json({
                    "type": event_type,
                    "uid": uid,
                    "meta": meta or self.phone_metas.get(uid, {})
                })
                valid_viewers.append(viewer)
            except Exception as e:
                logger.error(f"广播消息到观看端失败: {e}")
                continue
        self.viewer_connections = valid_viewers

    def update_phone_meta(self, uid: str, meta: dict):
        self.phone_metas[uid] = meta
        logger.info(f"手机 {uid} 元数据已更新: {meta}")
        import asyncio
        asyncio.create_task(self.broadcast_phone_update(uid, "phone_connected", meta))

    def get_status(self):
        return {
            "phones": [
                {"uid": uid, "meta": meta}
                for uid, meta in self.phone_metas.items()
            ],
            "phone_count": len(self.phone_connections),
            "viewer_count": len(self.viewer_connections)
        }


phone_camera_manager = PhoneCameraManager()