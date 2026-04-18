from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.JSON_schemas.Result_pydantic import Result
from app.services.safety_analysis_service import SafetyAnalysisService
from app.services.websocket_manager import manager
from app.services.ai_assistant_service import AIAssistantService
from app.services.historical_analysis_service import HistoricalAnalysisService
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Path, Query
from typing import Annotated

# 创建路由实例（tags 用于 API 文档分类）
router = APIRouter()

# 1. GET /api/v1/safety_analysis/start/{camera_id}：启动某个摄像头的安防分析
@router.get("/start/{camera_id}", response_model=Result, summary="启动某监控摄像头的安防分析", status_code=200)
def start_monitoring(
    camera_id: Annotated[str, Path(title="摄像头ID", description="摄像头唯一标识")],
    db: Session = Depends(get_db)
):
    """
    启动某个摄像头的安防分析功能

    Args:
        camera_id (str): 摄像头唯一标识
        db (Session): 数据库会话

    Returns:
        Result: 启动操作结果的统一响应，包含操作状态码、消息和数据
        - code: 业务状态码（1表示成功，0表示失败）
        - msg: 操作结果消息
        - data: 操作相关数据，可能包含摄像头ID、分析模式和线程信息
    """
    # 调用Service层处理所有业务逻辑
    return SafetyAnalysisService.start_safety_analysis(camera_id, db)

# 2. GET /api/v1/safety_analysis/stop/{camera_id}：关闭某个摄像头的安防分析
@router.get("/stop/{camera_id}", response_model=Result, summary="关闭某监控摄像头的安防分析", status_code=200)
def stop_monitoring(
    camera_id: Annotated[str, Path(title="摄像头ID", description="摄像头唯一标识")],
    db: Session = Depends(get_db)
):
    """
    关闭某个摄像头的安防分析功能

    Args:
        camera_id (str): 摄像头唯一标识
        db (Session): 数据库会话

    Returns:
        Result: 关闭操作结果的统一响应，包含操作状态码、消息和数据
        - code: 业务状态码（1表示成功，0表示失败）
        - msg: 操作结果消息
        - data: 操作相关数据，可能包含摄像头ID、分析模式和线程信息
    """
    return SafetyAnalysisService.stop_safety_analysis(camera_id, db)

# 3. ws://后端服务器IP:运行端口/api/v1/safety_analysis/ws :WebSocket端点, 用于建立连接，后端实时推送告警
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点，用于建立连接，后端实时推送告警

    Args:
        websocket (WebSocket): WebSocket连接对象
    """
    # 接受WebSocket连接
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            # 可以处理来自客户端的消息（如果需要）
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 4. POST /api/v1/safety_analysis/ai-question : AI智能问答
@router.post("/ai-question", response_model=Result, summary="AI智能问答助手", status_code=200)
def ai_question(
    question: Annotated[str, Query(title="用户问题", description="向AI助手提问")],
    db: Session = Depends(get_db)
):
    """
    AI智能问答助手 - 基于历史数据回答问题

    Args:
        question (str): 用户问题
        db (Session): 数据库会话

    Returns:
        Result: 包含AI回答的结果
    """
    result = AIAssistantService.handle_question(question, db)
    return Result.SUCCESS(result, "AI回答成功")

# 5. GET /api/v1/safety_analysis/statistics : 获取告警统计
@router.get("/statistics", response_model=Result, summary="获取告警统计分析", status_code=200)
def get_statistics(
    days: Annotated[int, Query(title="统计天数", description="统计最近多少天的数据", ge=1, le=365)] = 30,
    db: Session = Depends(get_db)
):
    """
    获取告警统计分析

    Args:
        days (int): 统计天数，默认30天
        db (Session): 数据库会话

    Returns:
        Result: 包含统计分析结果
    """
    result = HistoricalAnalysisService.get_alarm_statistics(db, days)
    if result["success"]:
        return Result.SUCCESS(result["data"], "获取统计成功")
    return Result.ERROR(result.get("error", "获取统计失败"))

# 6. GET /api/v1/safety_analysis/trend : 获取每日告警趋势
@router.get("/trend", response_model=Result, summary="获取每日告警趋势", status_code=200)
def get_trend(
    days: Annotated[int, Query(title="天数", description="查询最近多少天", ge=1, le=365)] = 30,
    db: Session = Depends(get_db)
):
    """
    获取每日告警趋势

    Args:
        days (int): 天数，默认30天
        db (Session): 数据库会话

    Returns:
        Result: 包含趋势数据
    """
    result = HistoricalAnalysisService.get_daily_trend(db, days)
    if result["success"]:
        return Result.SUCCESS(result["data"], "获取趋势成功")
    return Result.ERROR(result.get("error", "获取趋势失败"))

# 7. GET /api/v1/safety_analysis/hourly-distribution : 获取24小时告警分布
@router.get("/hourly-distribution", response_model=Result, summary="获取24小时告警分布", status_code=200)
def get_hourly_distribution(
    days: Annotated[int, Query(title="统计天数", description="统计最近多少天的数据", ge=1, le=365)] = 30,
    db: Session = Depends(get_db)
):
    """
    获取24小时告警分布

    Args:
        days (int): 统计天数，默认30天
        db (Session): 数据库会话

    Returns:
        Result: 包含小时分布数据
    """
    result = HistoricalAnalysisService.get_hourly_distribution(db, days)
    if result["success"]:
        return Result.SUCCESS(result["data"], "获取分布成功")
    return Result.ERROR(result.get("error", "获取分布失败"))

# 8. GET /api/v1/safety_analysis/area-ranking : 获取区域告警排名
@router.get("/area-ranking", response_model=Result, summary="获取区域告警排名", status_code=200)
def get_area_ranking(
    days: Annotated[int, Query(title="统计天数", description="统计最近多少天的数据", ge=1, le=365)] = 30,
    db: Session = Depends(get_db)
):
    """
    获取区域告警排名

    Args:
        days (int): 统计天数，默认30天
        db (Session): 数据库会话

    Returns:
        Result: 包含区域排名数据
    """
    result = HistoricalAnalysisService.get_area_ranking(db, days)
    if result["success"]:
        return Result.SUCCESS(result["data"], "获取排名成功")
    return Result.ERROR(result.get("error", "获取排名失败"))

# 9. GET /api/v1/safety_analysis/prediction : 获取告警预测
@router.get("/prediction", response_model=Result, summary="获取告警预测", status_code=200)
def get_prediction(
    days: Annotated[int, Query(title="预测天数", description="预测未来多少天", ge=1, le=30)] = 7,
    db: Session = Depends(get_db)
):
    """
    获取告警预测

    Args:
        days (int): 预测天数，默认7天
        db (Session): 数据库会话

    Returns:
        Result: 包含预测数据
    """
    result = HistoricalAnalysisService.get_prediction(db, days)
    if result["success"]:
        return Result.SUCCESS(result["data"], "获取预测成功")
    return Result.ERROR(result.get("error", "获取预测失败"))

# 10. GET /api/v1/safety_analysis/report : 获取综合分析报告
@router.get("/report", response_model=Result, summary="获取综合分析报告", status_code=200)
def get_comprehensive_report(
    db: Session = Depends(get_db)
):
    """
    获取综合分析报告

    Args:
        db (Session): 数据库会话

    Returns:
        Result: 包含综合报告数据
    """
    result = HistoricalAnalysisService.get_comprehensive_report(db)
    if result["success"]:
        return Result.SUCCESS(result["data"], "获取报告成功")
    return Result.ERROR(result.get("error", "获取报告失败"))