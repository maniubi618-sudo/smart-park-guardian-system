from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, status, Path, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import socket
import os
from app.JSON_schemas.Result_pydantic import Result
from app.JSON_schemas.camera_info_pydantic import CameraInfoResponse, CameraInfoCreate, CameraInfoUpdate, CameraInfoPageResponse, CameraStatusReport
from app.dependencies.db import get_db  # 获取数据库会话的依赖
from app.services.camera_info_service import CameraInfoService  # 导入service层代码负责业务逻辑
from app.dependencies.security import get_current_active_user, User
from app.services.phone_camera_manager import phone_camera_manager
from app.utils.logger import get_logger

logger = get_logger()

# 获取本地IP地址
def get_local_ip():
    try:
        # 不同操作系统的命令
        if os.name == 'nt':  # Windows
            import subprocess
            output = subprocess.check_output(['ipconfig', '/all'], universal_newlines=True)
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if 'IPv4 Address' in line or 'IPv4 地址' in line:
                    # 提取IP地址
                    parts = line.split(':')
                    if len(parts) > 1:
                        ip = parts[1].strip()
                        # 处理"(首选)"或"(Preferred)"后缀
                        if '(首选)' in ip:
                            ip = ip.replace('(首选)', '').strip()
                        if '(Preferred)' in ip:
                            ip = ip.replace('(Preferred)', '').strip()
                        # 排除环回地址和169.254开头的自动专用IP
                        if ip != '127.0.0.1' and not ip.startswith('169.254.'):
                            # 优先选择192.168、10或172.16-31开头的私有IP
                            if ip.startswith('192.168.') or ip.startswith('10.') or (ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31):
                                return ip
        
        # 如果Windows命令失败或其他系统，使用原方法
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# 创建路由实例（tags 用于 API 文档分类）
router = APIRouter()

# 定义分析帧的请求模型
from pydantic import BaseModel

class AnalyzeFrameRequest(BaseModel):
    image: str  # Base64编码的图像
    analysis_mode: str  # 分析模式

# 1. GET /api/v1/camera_infos/status_report：获取摄像头状态统计
@router.get("/status_report", response_model=Result[CameraStatusReport], summary="获取摄像头状态统计")
async def get_camera_status_report(
    db: Session = Depends(get_db)
):
    """
    获取摄像头状态统计信息，如 "在线 48/50 路，2 路离线"

    Args:
        db (Session): 数据库会话

    Returns:
        Result[CameraStatusReport]: 包含摄像头状态统计数据的统一响应结果
    """
    result = await CameraInfoService.get_camera_status_report(db)
    return result

# 2. GET /api/v1/camera_infos/search：根据条件获取摄像头信息（支持分页）
# 注意：这个路由必须放在 /{camera_info_id} 之前，避免路由冲突
@router.get("/search", response_model=Result[CameraInfoPageResponse], summary="根据条件获取摄像头信息（支持分页）", status_code=status.HTTP_200_OK)
async def search_camera_infos(
        park_area_id: Annotated[Optional[int], Query(description="园区区域ID")] = None,
        analysis_mode: Annotated[Optional[int], Query(description="分析模式: 0-无，1-全部(安全规范+区域入侵+火警)，2-安全规范，3-区域入侵，4-火警")] = None,
        camera_status: Annotated[Optional[int], Query(description="摄像头状态: 0-离线，1-在线(未开启安防检测)，2-在线(安防检测中)")] = None,
        skip: Annotated[int, Query(description="跳过的记录数")] = 0,
        limit: Annotated[int, Query(description="限制返回的记录数")] = 10,
        db: Session = Depends(get_db)
):
    """
    根据条件获取摄像头信息（支持分页）

    Args:
        park_area_id (Optional[int]): 园区区域ID
        analysis_mode (Optional[int]): 分析模式
        camera_status (Optional[int]): 摄像头状态: 0-离线，1-在线(未开启安防检测)，2-在线(安防检测中)
        skip (int): 跳过的记录数
        limit (int): 限制返回的记录数
        db (Session): 数据库会话

    Returns:
        Result[CameraInfoPageResponse]: 包含摄像头信息分页结果的统一响应
    """
    result = await CameraInfoService.get_camera_infos_with_condition(
        db, park_area_id, analysis_mode, camera_status, skip, limit
    )
    return result

# 3. GET /api/v1/camera_infos/local_ip: 获取本地IP地址
@router.get("/local_ip", summary="获取本地IP地址")
async def get_local_ip_address():
    """
    获取本地IP地址，用于手机摄像头连接
    
    Returns:
        Result: 包含本地IP地址的统一响应
    """
    ip = get_local_ip()
    return Result.SUCCESS(data={"ip": ip})

# 4. GET /api/v1/camera_infos/{camera_info_id}：获取单个摄像头信息
@router.get("/{camera_info_id}", response_model=Result[CameraInfoResponse], summary="获取单个摄像头信息", status_code=status.HTTP_200_OK)
async def read_camera_info(
    camera_info_id: Annotated[int, Path(title="摄像头信息ID", description="摄像头信息唯一标识")],
    db: Session = Depends(get_db)
):
    """
    根据ID获取单个摄像头信息

    Args:
        camera_info_id (int): 摄像头信息唯一标识
        db (Session): 数据库会话

    Returns:
        Result[CameraInfoResponse]: 包含摄像头信息的统一响应结果
    """
    result = await CameraInfoService.get_camera_info(db, camera_info_id)
    return result

# 4. POST /api/v1/camera_infos：创建新摄像头信息
@router.post("/", response_model=Result[CameraInfoResponse], summary="创建新摄像头信息", status_code=status.HTTP_201_CREATED)
async def create_new_camera_info(
    camera_info: CameraInfoCreate,
    db: Session = Depends(get_db)
):
    """
    创建新的摄像头信息

    Args:
        camera_info (CameraInfoCreate): 摄像头信息创建数据
        db (Session): 数据库会话

    Returns:
        Result[CameraInfoResponse]: 包含创建的摄像头信息的统一响应结果
    """
    result = await CameraInfoService.create_camera_info(db, camera_info)
    return result

# 5. PUT /api/v1/camera_infos/{camera_info_id}：更新摄像头信息
@router.put("/{camera_info_id}", response_model=Result[CameraInfoResponse], summary="更新摄像头信息", status_code=status.HTTP_200_OK)
async def update_camera_info(
    camera_info_id: Annotated[int, Path(title="摄像头信息ID", description="摄像头信息唯一标识")],
    camera_info_update: CameraInfoUpdate,
    db: Session = Depends(get_db)
):
    """
    更新摄像头信息

    Args:
        camera_info_id (int): 摄像头信息唯一标识
        camera_info_update (CameraInfoUpdate): 摄像头信息更新数据
        db (Session): 数据库会话

    Returns:
        Result[CameraInfoResponse]: 包含更新后的摄像头信息的统一响应结果
    """
    result = await CameraInfoService.update_camera_info(db, camera_info_id, camera_info_update)
    return result

# 6. DELETE /api/v1/camera_infos/{camera_info_ids}：删除摄像头信息（支持单个或批量删除）
@router.delete("/{camera_info_ids}", response_model=Result, status_code=status.HTTP_200_OK, summary="删除摄像头信息（支持单个或批量删除）")
async def remove_camera_info(
    camera_info_ids: Annotated[str, Path(min_length=1, title="摄像头信息ID列表", description="摄像头信息ID列表，多个ID之间用英文逗号分隔")],
    db: Session = Depends(get_db)
):
    """
    删除摄像头信息（支持单个或批量删除）

    Args:
        camera_info_ids (str): 摄像头信息ID列表，多个ID之间用英文逗号分隔
        db (Session): 数据库会话

    Returns:
        Result: 删除操作结果的统一响应
    """
    result = await CameraInfoService.delete_camera_infos(db, camera_info_ids)
    return result

# 7. GET /api/v1/camera_infos/test/{camera_id} :测试摄像头能否连接
@router.get("/test/{camera_id}", response_model=Result, summary="测试摄像头连接状态", status_code=status.HTTP_200_OK)
async def test_camera_connection_status(
    camera_id: Annotated[int, Path(title="摄像头ID", description="摄像头唯一标识")],
    db: Session = Depends(get_db)
):
    """
    测试摄像头连接状态

    Args:
        camera_id (int): 摄像头唯一标识
        db (Session): 数据库会话

    Returns:
        Result: 测试结果的统一响应
    """
    result = await CameraInfoService.test_camera_connection(camera_id, db)
    return result


# 8. GET /api/v1/camera_infos/preview/{camera_id} :获取摄像头预览图像
@router.get("/preview/{camera_id}", response_model=Result, summary="获取摄像头预览图像", status_code=status.HTTP_200_OK)
async def get_camera_preview_image(
    camera_id: Annotated[int, Path(title="摄像头ID", description="摄像头唯一标识")],
    db: Session = Depends(get_db)
):
    """
    获取摄像头预览图像

    Args:
        camera_id (int): 摄像头唯一标识
        db (Session): 数据库会话

    Returns:
        Result: 包含预览图像Base64数据的统一响应
    """
    result = await CameraInfoService.get_camera_preview(db, camera_id)
    return result


# 9. ws://后端服务器IP:运行端口/api/v1/camera_infos/preview/{camera_id} :WebSocket端点, 用于实时视频流预览
@router.websocket("/preview/{camera_id}/ws")
async def websocket_camera_preview(
    websocket: WebSocket,
    camera_id: Annotated[int, Path(title="摄像头ID", description="摄像头唯一标识")],
    db: Session = Depends(get_db)
):
    """
    WebSocket端点，用于实时视频流预览

    Args:
        websocket (WebSocket): WebSocket连接对象
        camera_id (int): 摄像头唯一标识
        db (Session): 数据库会话
    """
    await websocket.accept()
    try:
        await CameraInfoService.stream_camera_preview(websocket, camera_id, db)
    except WebSocketDisconnect:
        pass


# 10. ws://后端服务器IP:运行端口/api/v1/camera_infos/analysis/{camera_id} :WebSocket端点, 用于摄像头分析测试
@router.websocket("/analysis/{camera_id}/ws")
async def websocket_camera_analysis(
    websocket: WebSocket,
    camera_id: Annotated[int, Path(title="摄像头ID", description="摄像头唯一标识")],
    db: Session = Depends(get_db)
):
    """
    WebSocket端点，用于摄像头分析测试

    Args:
        websocket (WebSocket): WebSocket连接对象
        camera_id (int): 摄像头唯一标识
        db (Session): 数据库会话
    """
    await websocket.accept()
    # 获取查询参数
    write_to_database = websocket.query_params.get("write_to_database", "false").lower() == "true"
    try:
        await CameraInfoService.stream_camera_analysis(websocket, camera_id, db, write_to_database)
    except WebSocketDisconnect:
        pass


# 11. POST /api/v1/camera_infos/analyze_frame：分析单个视频帧
@router.post("/analyze_frame", summary="分析单个视频帧")
async def analyze_frame(
    request: AnalyzeFrameRequest,
    db: Session = Depends(get_db)
):
    """
    分析单个视频帧，用于本地视频分析功能
    
    Args:
        request (AnalyzeFrameRequest): 包含Base64编码图像和分析模式的请求
        db (Session): 数据库会话
    
    Returns:
        dict: 分析结果
    """
    result = await CameraInfoService.analyze_single_frame(request.image, request.analysis_mode, db)
    return result


# ========== 手机摄像头相关路由 ==========

# 12. GET /api/v1/camera_infos/phone_camera/status: 获取手机摄像头状态
@router.get("/phone_camera/status", summary="获取手机摄像头状态")
async def get_phone_camera_status():
    """
    获取手机摄像头的连接状态和观看端数量
    """
    return Result.SUCCESS(data=phone_camera_manager.get_status())


# 13. ws://后端服务器IP:运行端口/api/v1/camera_infos/phone_camera/phone: 手机端推流WebSocket端点
@router.websocket("/phone_camera/phone")
async def websocket_phone_camera_phone(websocket: WebSocket):
    """
    手机端WebSocket端点，用于推送摄像头画面
    """
    await phone_camera_manager.connect_phone(websocket)
    try:
        while True:
            data = await websocket.receive()
            logger.info(f"收到手机端数据: {'bytes' if 'bytes' in data else 'text'}, 大小: {len(data['bytes'] if 'bytes' in data else data['text'])}")
            if "text" in data:
                try:
                    import json
                    msg = json.loads(data["text"])
                    if msg.get("type") == "meta":
                        phone_camera_manager.update_phone_meta(msg.get("data", {}))
                except Exception as parse_err:
                    logger.debug(f"解析文本消息失败(可能是保活消息): {parse_err}")
                await phone_camera_manager.forward_from_phone(data["text"])
            elif "bytes" in data:
                await phone_camera_manager.forward_from_phone(data["bytes"])
    except WebSocketDisconnect:
        phone_camera_manager.disconnect_phone()
        logger.info("手机端WebSocket断开连接")
    except Exception as e:
        phone_camera_manager.disconnect_phone()
        logger.error(f"手机端WebSocket异常: {e}")


# 14. ws://后端服务器IP:运行端口/api/v1/camera_infos/phone_camera/viewer: 观看端WebSocket端点
@router.websocket("/phone_camera/viewer")
async def websocket_phone_camera_viewer(websocket: WebSocket):
    """
    观看端WebSocket端点，用于接收手机摄像头画面
    """
    await phone_camera_manager.connect_viewer(websocket)
    try:
        # 观看端只接收，不发送，所以使用一个无限循环来保持连接
        while True:
            # 使用 asyncio.sleep 来避免阻塞
            import asyncio
            await asyncio.sleep(3600)  # 每小时检查一次
    except WebSocketDisconnect:
        phone_camera_manager.disconnect_viewer(websocket)
    except Exception as e:
        phone_camera_manager.disconnect_viewer(websocket)


