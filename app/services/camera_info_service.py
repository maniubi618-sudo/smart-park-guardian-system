import asyncio
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime
import pytz
from io import BytesIO
import base64
from PIL import Image

import cv2
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect

from app.JSON_schemas.Result_pydantic import Result
from app.JSON_schemas.camera_info_pydantic import CameraInfoResponse, CameraInfoCreate, CameraInfoUpdate, \
    CameraInfoPageResponse, CameraStatusReport
from app.crud.camera_crud import (
    get_camera_info,
    get_camera_infos_with_condition as crud_get_camera_infos_with_condition,
    create_camera_info as crud_create_camera_info,
    update_camera_info as crud_update_camera_info,
    delete_camera_infos as crud_delete_camera_infos,
    get_camera_status_stats as crud_get_camera_status_stats
)
from app.crud.park_area_crud import get_park_area as crud_get_park_area
from app.DB_models.camera_info_db import CameraInfoDB
from app.services.thread_pool_manager import executor as db_executor
from app.services.detection_service import DetectionService
from app.services.safety_analysis_service import SafetyAnalysisService
from app.services.storage_service import StorageService
from app.utils.oss_utils import get_now
from app.DB_models.alarm_db import AlarmDB
from app.crud.alarm_crud import create_alarm
from app.services.alarm_broadcast_service import sync_broadcast_alarm
from app.utils.logger import get_logger

logger = get_logger()


class CameraInfoService:
    @staticmethod
    async def get_camera_info(db: Session, camera_info_id: int) -> Result[CameraInfoResponse]:
        """
        获取单个摄像头信息

        Args:
            db: 数据库会话
            camera_info_id: 摄像头信息ID

        Returns:
            Result[CameraInfoResponse]: 包含摄像头信息的响应对象
        """
        # 使用线程池执行数据库操作
        camera_info_with_park_area = await asyncio.get_event_loop().run_in_executor(
            db_executor,
            get_camera_info,
            db, camera_info_id
        )

        # 检查摄像头信息是否存在
        if not camera_info_with_park_area:
            return Result.ERROR("未找到指定的摄像头信息")

        # 从联表查询结果中提取信息
        camera_info = camera_info_with_park_area[0]  # CameraInfoDB instance
        park_area_name = camera_info_with_park_area[1]  # Park area name

        # 转换为响应模型
        camera_response = CameraInfoResponse(
            camera_id=camera_info.camera_id,
            camera_name=camera_info.camera_name,
            park_area_id=camera_info.park_area_id,
            park_area=park_area_name,
            install_position=camera_info.install_position,
            rtsp_url=camera_info.rtsp_url,
            analysis_mode=camera_info.analysis_mode,
            camera_status=camera_info.camera_status,
            create_time=camera_info.create_time,
            update_time=camera_info.update_time
        )

        return Result.SUCCESS(camera_response)

    @staticmethod
    async def get_camera_status_report(db: Session) -> Result[CameraStatusReport]:
        """
        获取摄像头状态统计报告

        Args:
            db: 数据库会话

        Returns:
            Result[CameraStatusReport]: 包含摄像头状态统计数据的响应对象
        """
        try:
            # 使用线程池执行数据库操作
            online_count, total_count = await asyncio.get_event_loop().run_in_executor(
                db_executor,
                crud_get_camera_status_stats,
                db
            )

            # 计算离线摄像头数
            offline_count = total_count - online_count

            return Result.SUCCESS(CameraStatusReport(
                online_count=online_count,
                total_count=total_count,
                offline_count=offline_count
            ))
        except Exception as e:
            return Result.ERROR(f"查询摄像头状态统计失败: {str(e)}")

    @staticmethod
    async def get_camera_infos_with_condition(
            db: Session,
            park_area_id: Optional[int] = None,
            analysis_mode: Optional[int] = None,
            camera_status: Optional[int] = None,
            skip: int = 0,
            limit: int = 10
    ) -> Result[CameraInfoPageResponse]:
        """
        根据条件获取摄像头信息（支持分页）

        Args:
            db: 数据库会话
            park_area_id: 园区位置ID
            analysis_mode: 分析模式
            camera_status: 摄像头状态
            skip: 跳过的记录数
            limit: 限制返回的记录数

        Returns:
            Result[CameraInfoPageResponse]: 包含摄像头信息列表和分页信息的响应对象
        """
        try:
            # 使用线程池执行数据库操作，分别获取符合条件的总记录数和当前页数据
            total, camera_infos_with_details = await asyncio.get_event_loop().run_in_executor(
                    db_executor,
                    crud_get_camera_infos_with_condition,
                    db, park_area_id, analysis_mode, camera_status, skip, limit
                )
            
            # 转换查询结果为CameraInfoResponse对象
            camera_responses = []
            for camera_info_row in camera_infos_with_details:
                # 从联表查询结果中提取信息
                camera_info = camera_info_row[0]  # CameraInfoDB instance
                park_area_name = camera_info_row[1]  # Park area name
                
                camera_response = CameraInfoResponse(
                    camera_id=camera_info.camera_id,
                    camera_name=camera_info.camera_name,
                    park_area_id=camera_info.park_area_id,
                    park_area=park_area_name,
                    install_position=camera_info.install_position,
                    rtsp_url=camera_info.rtsp_url,
                    analysis_mode=camera_info.analysis_mode,
                    camera_status=camera_info.camera_status,
                    create_time=camera_info.create_time,
                    update_time=camera_info.update_time
                )
                camera_responses.append(camera_response)

            return Result.SUCCESS(CameraInfoPageResponse(total=total, rows=camera_responses))
        except Exception as e:
            return Result.ERROR(f"查询摄像头信息失败: {str(e)}")

    @staticmethod
    async def create_camera_info(db: Session, camera_info: CameraInfoCreate) -> Result[CameraInfoResponse]:
        """
        创建新摄像头信息

        Args:
            db: 数据库会话
            camera_info: 摄像头信息创建请求数据

        Returns:
            Result[CameraInfoResponse]: 包含创建的摄像头信息的响应对象
        """
        try:
            # 检查园区区域是否存在
            park_area = await asyncio.get_event_loop().run_in_executor(
                db_executor,
                crud_get_park_area,
                db, camera_info.park_area_id
            )
            if not park_area:
                return Result.ERROR("指定的园区区域不存在")

            # 使用线程池执行数据库操作
            db_camera_info, park_area_name = await asyncio.get_event_loop().run_in_executor(
                db_executor,
                crud_create_camera_info,
                db, camera_info
            )

            # 转换为响应模型
            camera_response = CameraInfoResponse(
                camera_id=db_camera_info.camera_id,
                camera_name=db_camera_info.camera_name,
                park_area_id=db_camera_info.park_area_id,
                park_area=park_area_name,
                install_position=db_camera_info.install_position,
                rtsp_url=db_camera_info.rtsp_url,
                analysis_mode=db_camera_info.analysis_mode,
                camera_status=db_camera_info.camera_status,
                create_time=db_camera_info.create_time,
                update_time=db_camera_info.update_time
            )

            return Result.SUCCESS(camera_response, "摄像头信息创建成功")
        except Exception as e:
            return Result.ERROR(f"创建摄像头信息失败: {str(e)}")

    @staticmethod
    async def update_camera_info(
            db: Session,
            camera_info_id: int,
            camera_info_update: CameraInfoUpdate
    ) -> Result[CameraInfoResponse]:
        """
        修改摄像头信息

        Args:
            db: 数据库会话
            camera_info_id: 摄像头信息ID
            camera_info_update: 摄像头信息更新数据

        Returns:
            Result[CameraInfoResponse]: 包含更新后的摄像头信息的响应对象
        """
        try:
            # 检查园区区域是否存在（如果提供了park_area_id）
            if camera_info_update.park_area_id is not None:
                park_area = await asyncio.get_event_loop().run_in_executor(
                    db_executor,
                    crud_get_park_area,
                    db, camera_info_update.park_area_id
                )
                if not park_area:
                    return Result.ERROR("指定的园区区域不存在")

            # 使用线程池执行数据库操作
            updated_camera_info_with_park_area = await asyncio.get_event_loop().run_in_executor(
                db_executor,
                crud_update_camera_info,
                db, camera_info_id, camera_info_update
            )

            # 检查摄像头信息是否存在
            if not updated_camera_info_with_park_area:
                return Result.ERROR("未找到指定的摄像头信息")

            # 从联表查询结果中提取信息
            updated_camera_info = updated_camera_info_with_park_area[0]  # CameraInfoDB instance
            park_area_name = updated_camera_info_with_park_area[1]  # Park area name

            # 转换为响应模型
            camera_response = CameraInfoResponse(
                camera_id=updated_camera_info.camera_id,
                camera_name=updated_camera_info.camera_name,
                park_area_id=updated_camera_info.park_area_id,
                park_area=park_area_name,
                install_position=updated_camera_info.install_position,
                rtsp_url=updated_camera_info.rtsp_url,
                analysis_mode=updated_camera_info.analysis_mode,
                camera_status=updated_camera_info.camera_status,
                create_time=updated_camera_info.create_time,
                update_time=updated_camera_info.update_time
            )

            return Result.SUCCESS(camera_response, "摄像头信息更新成功")
        except Exception as e:
            return Result.ERROR(f"更新摄像头信息失败: {str(e)}")

    @staticmethod
    async def delete_camera_infos(db: Session, camera_info_ids_str: str) -> Result:
        """
        服务层处理摄像头信息删除业务逻辑并构造响应结果

        Args:
            db: 数据库会话
            camera_info_ids_str: 摄像头信息ID字符串（逗号分隔）

        Returns:
            Result: 包含删除结果的响应对象
        """
        # 解析ID列表，支持单个ID或多个ID（用逗号分隔）
        try:
            ids = [int(camera_id.strip()) for camera_id in camera_info_ids_str.split(',') if camera_id.strip()]
            if not ids:
                return Result.ERROR("无效的ID参数")
        except ValueError:
            return Result.ERROR("ID参数格式错误，请提供有效的数字ID")

        # 使用线程池执行数据库操作
        deleted_count = await asyncio.get_event_loop().run_in_executor(
            db_executor, crud_delete_camera_infos, db, ids
        )

        # 构造并返回响应结果
        if deleted_count == 0:
            return Result.ERROR("删除失败: 没有找到指定的任意一个摄像头信息")
        elif deleted_count < len(ids):
            return Result.SUCCESS(
                {"deleted_count": deleted_count},
                f"部分删除成功: 成功删除{deleted_count}条记录"
            )
        else:
            return Result.SUCCESS(
                {"deleted_count": deleted_count},
                f"批量删除成功: 共删除{deleted_count}条记录"
            )

    # rtsp流连通性检测方法

    @classmethod
    async def test_camera_connection(cls, camera_id, db):
        def _test_connection():
            result_container = {}

            def connection_task():
                try:
                    camera_info_result0 = get_camera_info(db, camera_id)
                    if not camera_info_result0:
                        result_container['result'] = Result.ERROR(f"未找到ID为 {camera_id} 的摄像头信息")
                        return

                    # 从元组中提取CameraInfoDB对象
                    camera_info0 = camera_info_result0[0]  # CameraInfoDB instance
                    rtsp_url = camera_info0.rtsp_url

                    is_local_camera = False
                    if rtsp_url == "0":  # RTSP地址为0时，使用本地摄像头（USB摄像头）
                        rtsp_url = 0  # OpenCV使用0表示默认摄像头设备
                        is_local_camera = True
                    elif rtsp_url.startswith("local:"):# 测试时，服务器本地视频充当实时视频流
                        file_name = rtsp_url[6:]
                        project_root = Path(__file__).parent.parent.parent
                        rtsp_url = project_root / 'app' / 'test_videos' / file_name
                        # 检查该文件是否存在
                        if not rtsp_url.exists():
                            result_container['result'] = Result.ERROR(f"本地测试视频文件 {rtsp_url} 不存在，无法进行连接测试")
                            return

                    # 本地摄像头使用 DirectShow 后端（Windows）
                    if is_local_camera:
                        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_DSHOW)
                    else:
                        cap = cv2.VideoCapture(rtsp_url)
                    # 本地摄像头不支持设置超时属性
                    if not is_local_camera:
                        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
                        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 3000)

                    result_container['is_opened'] = cap.isOpened()
                    if cap.isOpened():
                        cap.release()
                        if is_local_camera:
                            result_container['result'] = Result.SUCCESS(True, "本地摄像头连接成功")
                        else:
                            result_container['result'] = Result.SUCCESS(True, "RTSP流连接成功")
                    else:
                        if is_local_camera:
                            result_container['result'] = Result.ERROR("本地摄像头连接失败，请检查摄像头是否被占用或是否存在")
                        else:
                            result_container['result'] = Result.ERROR("RTSP流连接失败")

                except Exception as e:
                    result_container['result'] = Result.ERROR(f"测试连接时发生错误: {str(e)}")

            # 在单独线程中执行连接测试
            thread = threading.Thread(target=connection_task)
            thread.daemon = True
            thread.start()

            # 等待最多5秒
            thread.join(timeout=5.0)

            # 检查线程是否完成
            if thread.is_alive():
                return Result.ERROR("RTSP流连接超时（超过5秒）")

            return result_container['result']

        # 使用线程池执行阻塞的视频连接测试
        test_result = await asyncio.get_event_loop().run_in_executor(db_executor, _test_connection)
        
        # 根据测试结果更新摄像头状态
        # 首先获取摄像头当前状态
        camera_info_result = await asyncio.get_event_loop().run_in_executor(
            db_executor, get_camera_info, db, camera_id
        )
        
        if camera_info_result:
            # 从元组中提取CameraInfoDB对象
            camera_info = camera_info_result[0]  # CameraInfoDB instance
            current_status = camera_info.camera_status
            
            if test_result.code == 1:  # 成功
                # 如果摄像头当前状态是2（在线且安防检测中），保持状态为2
                # 否则更新为1（在线但未开启安防检测）
                new_status = 2 if current_status == 2 else 1
                camera_update = CameraInfoUpdate(camera_status=new_status)
                await asyncio.get_event_loop().run_in_executor(
                    db_executor,
                    crud_update_camera_info,
                    db, camera_id, camera_update
                )
            elif test_result.code == 0:  # 失败
                # 更新摄像头状态为离线（值为0）
                camera_update = CameraInfoUpdate(camera_status=0)
                await asyncio.get_event_loop().run_in_executor(
                    db_executor,
                    crud_update_camera_info,
                    db, camera_id, camera_update
                )
        
        return test_result

    @staticmethod
    async def get_camera_preview(db: Session, camera_id: int) -> Result:
        """
        获取摄像头预览图像

        Args:
            db: 数据库会话
            camera_id: 摄像头ID

        Returns:
            Result: 包含预览图像Base64数据的响应对象
        """
        import base64
        from io import BytesIO
        from PIL import Image

        def _capture_preview():
            try:
                # 获取摄像头信息
                camera_info_result = get_camera_info(db, camera_id)
                if not camera_info_result:
                    return Result.ERROR(f"未找到ID为 {camera_id} 的摄像头信息")

                camera_info = camera_info_result[0]
                rtsp_url = camera_info.rtsp_url

                # 处理不同类型的视频源
                is_local_camera = False
                if rtsp_url == "0":  # 本地摄像头
                    rtsp_url = 0
                    is_local_camera = True
                elif rtsp_url.startswith("local:"):
                    file_name = rtsp_url[6:]
                    project_root = Path(__file__).parent.parent.parent
                    rtsp_url = project_root / 'app' / 'test_videos' / file_name
                    if not rtsp_url.exists():
                        return Result.ERROR(f"本地测试视频文件 {rtsp_url} 不存在")

                # 打开视频流
                if is_local_camera:
                    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_DSHOW)
                else:
                    cap = cv2.VideoCapture(rtsp_url)
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)

                if not cap.isOpened():
                    return Result.ERROR("无法打开摄像头视频流")

                # 读取一帧图像
                ret, frame = cap.read()
                cap.release()

                if not ret or frame is None:
                    return Result.ERROR("无法读取视频帧")

                # 将OpenCV图像(BGR)转换为RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 转换为PIL Image
                pil_image = Image.fromarray(frame_rgb)

                # 调整图像大小以减小传输数据量
                max_size = (640, 480)
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)

                # 转换为Base64
                buffer = BytesIO()
                pil_image.save(buffer, format='JPEG', quality=85)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                return Result.SUCCESS({
                    "image": f"data:image/jpeg;base64,{img_base64}",
                    "camera_name": camera_info.camera_name,
                    "timestamp": datetime.now(pytz.timezone('Asia/Shanghai')).isoformat()
                }, "预览图像获取成功")

            except Exception as e:
                return Result.ERROR(f"获取预览图像失败: {str(e)}")

        # 使用线程池执行
        return await asyncio.get_event_loop().run_in_executor(db_executor, _capture_preview)

    @staticmethod
    async def stream_camera_preview(websocket, camera_id: int, db: Session):
        """
        通过WebSocket流式传输摄像头预览

        Args:
            websocket: WebSocket连接对象
            camera_id: 摄像头ID
            db: 数据库会话
        """
        import base64
        from io import BytesIO
        from PIL import Image
        import asyncio

        cap = None
        try:
            # 获取摄像头信息
            camera_info_result = get_camera_info(db, camera_id)
            if not camera_info_result:
                await websocket.send_json({"error": "未找到摄像头信息"})
                return

            camera_info = camera_info_result[0]
            rtsp_url = camera_info.rtsp_url

            # 处理不同类型的视频源
            is_local_camera = False
            if rtsp_url == "0":  # 本地摄像头
                rtsp_url = 0
                is_local_camera = True
            elif rtsp_url.startswith("local:"):
                file_name = rtsp_url[6:]
                project_root = Path(__file__).parent.parent.parent
                rtsp_url = project_root / 'app' / 'test_videos' / file_name
                if not rtsp_url.exists():
                    await websocket.send_json({"error": "本地测试视频文件不存在"})
                    return

            # 打开视频流
            if is_local_camera:
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(rtsp_url)
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)

            if not cap.isOpened():
                await websocket.send_json({"error": "无法打开摄像头"})
                return

            # 持续发送视频帧
            while True:
                # 读取一帧
                ret, frame = cap.read()
                if not ret or frame is None:
                    await asyncio.sleep(0.1)
                    continue

                # 转换为RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 转换为PIL Image并调整大小
                pil_image = Image.fromarray(frame_rgb)
                max_size = (640, 480)
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)

                # 转换为Base64
                buffer = BytesIO()
                pil_image.save(buffer, format='JPEG', quality=85)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                # 发送到WebSocket
                await websocket.send_json({
                    "image": f"data:image/jpeg;base64,{img_base64}",
                    "timestamp": datetime.now(pytz.timezone('Asia/Shanghai')).isoformat()
                })

                # 控制帧率（约10fps）
                await asyncio.sleep(0.1)

        except WebSocketDisconnect:
            # 客户端断开连接
            logger.info(f"摄像头 {camera_id} 分析测试WebSocket连接已断开")
        except Exception as e:
            logger.error(f"摄像头 {camera_id} 分析测试发生错误: {str(e)}")
            try:
                await websocket.send_json({"error": f"错误: {str(e)}"})
            except:
                pass
        finally:
            if cap:
                cap.release()
                logger.info(f"摄像头 {camera_id} 视频流已释放")

    @staticmethod
    async def stream_camera_analysis(websocket, camera_id: int, db: Session, write_to_database: bool = False):
        """
        摄像头分析测试的WebSocket流
        启动该功能调取对应摄像头，并对摄像头获取到图像进行分析
        同时显示对应摄像头获取的图像以便调整摄像头

        Args:
            websocket: WebSocket连接对象
            camera_id: 摄像头ID
            db: 数据库会话
            write_to_database: 是否将警告信息写入数据库
        """
        cap = None
        try:
            # 获取摄像头信息
            camera_info = db.query(CameraInfoDB).filter(CameraInfoDB.camera_id == camera_id).first()
            if not camera_info:
                await websocket.send_json({"error": "摄像头不存在"})
                return

            # 打开摄像头
            rtsp_url = camera_info.rtsp_url
            if rtsp_url == "0":
                # 本地摄像头
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            else:
                # 网络摄像头
                cap = cv2.VideoCapture(rtsp_url)

            if not cap.isOpened():
                await websocket.send_json({"error": "无法打开摄像头"})
                return

            # 持续发送视频帧和分析结果
            while True:
                # 检查是否有WebSocket消息需要处理
                try:
                    # 非阻塞地检查WebSocket消息
                    message = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                    if message.get('action') == 'update_write_to_database':
                        write_to_database = message.get('write_to_database', False)
                        logger.info(f"更新write_to_database值为: {write_to_database}")
                except asyncio.TimeoutError:
                    # 没有消息，继续
                    pass
                except Exception as e:
                    # 发生错误，可能是连接已关闭
                    logger.error(f"接收WebSocket消息失败: {str(e)}")
                    break
                
                # 读取一帧
                ret, frame = cap.read()
                if not ret or frame is None:
                    await asyncio.sleep(0.1)
                    continue

                # 转换为RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 转换为PIL Image并调整大小，减小图像尺寸以提高传输速度
                pil_image = Image.fromarray(frame_rgb)
                max_size = (480, 360)  # 减小图像尺寸
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)

                # 转换为Base64，降低质量以减小数据量
                buffer = BytesIO()
                pil_image.save(buffer, format='JPEG', quality=75)  # 降低图像质量
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                # 使用真实的检测服务进行分析
                analysis_results = []
                helmet_detected = False
                vest_detected = False
                fire_detected = False
                smoke_detected = False
                person_count = 0
                vehicle_count = 0
                intrusion_detected = False
                
                # 转换为OpenCV格式
                frame_cv = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                
                # 并行执行所有检测任务
                try:
                    def detect_helmet():
                        result = DetectionService.helmet_model(frame_cv, imgsz=640)[0]
                        head_class_id = 0
                        for box in result.boxes:
                            class_id = int(box.cls[0])
                            if class_id == head_class_id:
                                return True
                        return False
                    
                    def detect_vest():
                        result = DetectionService.vest_model(frame_cv, imgsz=640)[0]
                        no_vest_class_id = 0
                        for box in result.boxes:
                            class_id = int(box.cls[0])
                            if class_id == no_vest_class_id:
                                return True
                        return False
                    
                    def detect_fire_smoke():
                        result = DetectionService.fire_smoke_model(frame_cv, imgsz=640)[0]
                        for box in result.boxes:
                            return True, True
                        return False, False
                    
                    def detect_person_vehicle():
                        result = DetectionService.person_vehicle_model(frame_cv, classes=[0,1,2,3,4,5,6,7], imgsz=640)[0]
                        p_count = 0
                        v_count = 0
                        for box in result.boxes:
                            class_id = int(box.cls[0])
                            if class_id == 0:
                                p_count += 1
                            elif class_id in [1, 2, 3, 4, 5, 6, 7]:
                                v_count += 1
                        return p_count, v_count
                    
                    # 并行执行所有检测任务
                    helmet_detected, vest_detected, (fire_detected, smoke_detected), (person_count, vehicle_count) = await asyncio.gather(
                        asyncio.to_thread(detect_helmet),
                        asyncio.to_thread(detect_vest),
                        asyncio.to_thread(detect_fire_smoke),
                        asyncio.to_thread(detect_person_vehicle)
                    )
                except Exception as e:
                    logger.error(f"检测任务执行失败: {str(e)}")
                    # 发生错误时设置默认值
                    helmet_detected = False
                    vest_detected = False
                    fire_detected = False
                    smoke_detected = False
                    person_count = 0
                    vehicle_count = 0
                
                # 检测区域入侵（人员或车辆）
                intrusion_detected = person_count > 0 or vehicle_count > 0
                
                # 生成分析结果
                analysis_results = [
                    {"label": "未戴安全帽", "value": "检测到" if helmet_detected else "未检测到"},
                    {"label": "未穿反光衣", "value": "检测到" if vest_detected else "未检测到"},
                    {"label": "火焰检测", "value": "检测到" if fire_detected else "未检测到"},
                    {"label": "烟雾检测", "value": "检测到" if smoke_detected else "未检测到"},
                    {"label": "人员检测", "value": f"{person_count}人"},
                    {"label": "车辆检测", "value": f"{vehicle_count}辆"},
                    {"label": "区域入侵", "value": "检测到" if intrusion_detected else "未检测到"}
                ]
                
                # 检测告警情况并创建告警记录
                if write_to_database and (helmet_detected or vest_detected or fire_detected or intrusion_detected or person_count > 0):
                    # 将告警处理放到后台执行，避免阻塞视频流
                    async def process_alarm():
                        # 保存告警截图
                        snapshot_url = ""
                        try:
                            snapshot_url = StorageService.upload_alarm_snapshot(frame_cv, camera_id)
                            logger.info(f"告警截图上传成功: {snapshot_url}")
                        except Exception as e:
                            logger.error(f"上传告警截图失败: {str(e)}")
                            snapshot_url = ""
                        
                        # 确定告警类型
                        alarm_type = 0  # 默认为安全规范
                        if fire_detected or smoke_detected:
                            alarm_type = 2  # 火警
                        elif person_count > 0 or vehicle_count > 0:
                            alarm_type = 1  # 区域入侵
                        elif helmet_detected or vest_detected:
                            alarm_type = 0  # 安全规范
                        
                        # 创建告警记录（无论是否有截图都创建）
                        try:
                            alarm = create_alarm(db, camera_id, alarm_type, 0, get_now(), snapshot_url if snapshot_url else "")
                            logger.info(f"告警记录创建成功: alarm_id={alarm.alarm_id}, camera_id={camera_id}, alarm_type={alarm_type}, snapshot={snapshot_url}")
                            # 广播告警
                            sync_broadcast_alarm(alarm)
                        except Exception as e:
                            logger.error(f"创建告警记录失败: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
                    
                    # 创建后台任务处理告警
                    asyncio.create_task(process_alarm())

                # 确保 analysis_results 有值
                if not analysis_results:
                    analysis_results = [
                        {"label": "未戴安全帽", "value": "未检测到" if not helmet_detected else "检测到"},
                        {"label": "未穿反光衣", "value": "未检测到" if not vest_detected else "检测到"},
                        {"label": "火焰检测", "value": "未检测到" if not fire_detected else "检测到"},
                        {"label": "烟雾检测", "value": "未检测到" if not smoke_detected else "检测到"},
                        {"label": "人员检测", "value": f"{person_count}人"},
                        {"label": "车辆检测", "value": f"{vehicle_count}辆"},
                        {"label": "区域入侵", "value": "未检测到" if not intrusion_detected else "检测到"}
                    ]

                # 发送到WebSocket
                try:
                    await websocket.send_json({
                        "image": f"data:image/jpeg;base64,{img_base64}",
                        "timestamp": datetime.now(pytz.timezone('Asia/Shanghai')).isoformat(),
                        "results": analysis_results
                    })
                    logger.info(f"分析结果已发送: 人员{person_count}人, 车辆{vehicle_count}辆, 安全帽{'检测到' if helmet_detected else '未检测到'}, 反光衣{'检测到' if vest_detected else '未检测到'}")
                except Exception as e:
                    logger.error(f"发送WebSocket消息失败: {str(e)}")
                    # 发送失败，说明客户端已断开连接，跳出循环
                    break

                # 控制帧率（约10fps）
                await asyncio.sleep(0.1)

        except WebSocketDisconnect:
            # 客户端断开连接
            pass
        except Exception as e:
            try:
                await websocket.send_json({"error": f"错误: {str(e)}"})
            except:
                pass
        finally:
            if cap:
                cap.release()

    @staticmethod
    async def analyze_single_frame(image_base64: str, analysis_mode: str, db: Session):
        """
        分析单个视频帧，用于本地视频分析功能
        
        Args:
            image_base64 (str): Base64编码的图像
            analysis_mode (str): 分析模式
            db (Session): 数据库会话
        
        Returns:
            dict: 分析结果
        """
        logger = get_logger()
        try:
            # 解码Base64图像
            import base64
            from io import BytesIO
            import numpy as np
            
            # 移除data:image/jpeg;base64,前缀
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',')[1]
            
            # 解码Base64
            image_data = base64.b64decode(image_base64)
            image_np = np.frombuffer(image_data, dtype=np.uint8)
            frame_cv = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
            
            if frame_cv is None:
                return {"error": "无法解码图像"}

            # 初始化检测结果
            helmet_detected = False
            vest_detected = False
            fire_detected = False
            smoke_detected = False
            person_count = 0
            vehicle_count = 0
            intrusion_detected = False
            
            # 检测安全帽（未戴安全帽）- 在线程中运行避免阻塞
            try:
                def detect_helmet():
                    result = DetectionService.helmet_model(frame_cv, imgsz=640)[0]
                    head_class_id = 0
                    confidence_threshold = 0.5
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        if class_id == head_class_id and confidence >= confidence_threshold:
                            return True
                    return False
                helmet_detected = await asyncio.to_thread(detect_helmet)
            except Exception as e:
                logger.error(f"安全帽检测失败: {str(e)}")
            
            # 检测反光衣（未穿反光衣）- 在线程中运行避免阻塞
            try:
                def detect_vest():
                    result = DetectionService.vest_model(frame_cv, imgsz=640)[0]
                    no_vest_class_id = 0
                    confidence_threshold = 0.5
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        if class_id == no_vest_class_id and confidence >= confidence_threshold:
                            return True
                    return False
                vest_detected = await asyncio.to_thread(detect_vest)
            except Exception as e:
                logger.error(f"反光衣检测失败: {str(e)}")
            
            # 检测火焰和烟雾 - 在线程中运行避免阻塞
            try:
                def detect_fire_smoke():
                    result = DetectionService.fire_smoke_model(frame_cv, imgsz=640)[0]
                    fire_detected = False
                    smoke_detected = False
                    confidence_threshold = 0.5
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        if confidence >= confidence_threshold:
                            if class_id == 0:
                                fire_detected = True
                            elif class_id == 1:
                                smoke_detected = True
                    return fire_detected, smoke_detected
                fire_detected, smoke_detected = await asyncio.to_thread(detect_fire_smoke)
            except Exception as e:
                logger.error(f"火焰烟雾检测失败: {str(e)}")
            
            # 检测人员和车辆 - 在线程中运行避免阻塞
            try:
                def detect_person_vehicle():
                    result = DetectionService.person_vehicle_model(frame_cv, classes=[0,1,2,3,4,5,6,7], imgsz=640)[0]
                    person_count = 0
                    vehicle_count = 0
                    confidence_threshold = 0.5
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        if confidence >= confidence_threshold:
                            if class_id == 0:  # person
                                person_count += 1
                            elif class_id in [1, 2, 3, 4, 5, 6, 7]:  # car, truck, bus, etc.
                                vehicle_count += 1
                    return person_count, vehicle_count
                person_count, vehicle_count = await asyncio.to_thread(detect_person_vehicle)
            except Exception as e:
                logger.error(f"人员车辆检测失败: {str(e)}")
            
            # 简单的区域入侵检测（如果检测到人员或车辆，就认为有入侵）
            intrusion_detected = person_count > 0 or vehicle_count > 0
            
            # 生成分析结果
            analysis_results = [
                {"label": "未戴安全帽", "value": "未检测到" if not helmet_detected else "检测到"},
                {"label": "未穿反光衣", "value": "未检测到" if not vest_detected else "检测到"},
                {"label": "火焰检测", "value": "未检测到" if not fire_detected else "检测到"},
                {"label": "烟雾检测", "value": "未检测到" if not smoke_detected else "检测到"},
                {"label": "人员检测", "value": f"{person_count}人"},
                {"label": "车辆检测", "value": f"{vehicle_count}辆"},
                {"label": "区域入侵", "value": "未检测到" if not intrusion_detected else "检测到"}
            ]

            return {"results": analysis_results}
        except Exception as e:
            logger.error(f"分析单个视频帧失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"分析失败: {str(e)}"}