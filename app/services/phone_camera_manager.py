from typing import List, Optional
from fastapi import WebSocket
from app.utils.logger import get_logger

logger = get_logger()


class PhoneCameraManager:
    def __init__(self):
        self.phone_connection: Optional[WebSocket] = None
        self.viewer_connections: List[WebSocket] = []
        self.phone_meta = {}
        self.phone_connected = False

    async def connect_phone(self, websocket: WebSocket):
        # 先强制断开旧连接
        if self.phone_connection:
            try:
                await self.phone_connection.close()
                logger.info("强制关闭旧手机连接")
            except:
                logger.info("旧手机连接已失效")
            self.phone_connection = None
            self.phone_connected = False

        await websocket.accept()
        self.phone_connection = websocket
        self.phone_connected = True
        logger.info("新手机摄像头已连接")
        # 通知所有观看端
        await self.broadcast_to_viewers({
            "type": "phone_connected",
            "meta": self.phone_meta
        })

    async def connect_viewer(self, websocket: WebSocket):
        await websocket.accept()
        self.viewer_connections.append(websocket)
        logger.info(f"观看端已连接，当前观看端数: {len(self.viewer_connections)}")
        # 如果手机已连接，发送状态
        if self.phone_connected:
            await websocket.send_json({
                "type": "phone_connected",
                "meta": self.phone_meta
            })

    def disconnect_phone(self):
        logger.info("正在断开手机摄像头连接...")
        if self.phone_connection:
            try:
                # 尝试发送关闭消息
                import asyncio
                asyncio.create_task(self.phone_connection.close())
            except:
                pass
        self.phone_connection = None
        self.phone_connected = False
        self.phone_meta = {}
        logger.info("手机摄像头已断开")
        # 通知所有观看端
        import asyncio
        asyncio.create_task(self.broadcast_to_viewers({
            "type": "phone_disconnected"
        }))

    def disconnect_viewer(self, websocket: WebSocket):
        if websocket in self.viewer_connections:
            self.viewer_connections.remove(websocket)
            logger.info(f"观看端已断开，当前观看端数: {len(self.viewer_connections)}")

    async def forward_from_phone(self, data):
        """将手机端的数据转发给所有观看端"""
        if not self.viewer_connections:
            logger.debug("没有观看端连接，跳过转发")
            return
        
        valid_viewers = []
        data_type = "bytes" if isinstance(data, bytes) else "text"
        data_size = len(data) if isinstance(data, bytes) else len(str(data))
        
        logger.info(f"转发{data_type}数据({data_size}字节)到{len(self.viewer_connections)}个观看端")
        
        for viewer in self.viewer_connections:
            try:
                if isinstance(data, bytes):
                    await viewer.send_bytes(data)
                else:
                    await viewer.send_text(data)
                valid_viewers.append(viewer)
                logger.debug("成功转发数据到一个观看端")
            except Exception as e:
                logger.error(f"转发数据到观看端失败: {e}")
                continue
        self.viewer_connections = valid_viewers

    async def broadcast_to_viewers(self, message: dict):
        """向所有观看端广播JSON消息"""
        valid_viewers = []
        for viewer in self.viewer_connections:
            try:
                await viewer.send_json(message)
                valid_viewers.append(viewer)
            except Exception as e:
                logger.error(f"广播消息到观看端失败: {e}")
                continue
        self.viewer_connections = valid_viewers

    def update_phone_meta(self, meta: dict):
        self.phone_meta = meta
        logger.info(f"手机元数据已更新: {meta}")
        # 向所有观看端广播更新后的meta
        import asyncio
        asyncio.create_task(self.broadcast_to_viewers({
            "type": "phone_connected",
            "meta": self.phone_meta
        }))

    def get_status(self):
        return {
            "phone_connected": self.phone_connected,
            "phone_meta": self.phone_meta,
            "viewer_count": len(self.viewer_connections)
        }


# 创建全局手机摄像头管理器
phone_camera_manager = PhoneCameraManager()
