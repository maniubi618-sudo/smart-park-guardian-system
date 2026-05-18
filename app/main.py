# 1. 项目入口：main.py
# 核心职责：
#
# 启动 FastAPI 服务；
# 注册所有业务模块的路由；
# 加载全局配置（如跨域、中间件）。
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.api.v1.endpoints import alarm_handle_record_router  # 导入报警记录接口路由
from app.api.v1.endpoints import alarm_router  # 导入告警记录接口路由
from app.api.v1.endpoints import camera_router  # 导入商品接口路由
from app.api.v1.endpoints import park_area_router  # 导入园区区域接口路由
from app.api.v1.endpoints import safety_analysis_router  # 导入安全分析路由
from app.api.v1.endpoints import sign_in_or_up_router  # 导入注册登录接口路由
from app.api.v1.endpoints import user_router  # 导入用户接口路由
from app.api.v1.endpoints import crop_disease_detection  # 导入农作物病害检测路由
from app.api.v1.endpoints import citrus_detection  # 导入柑橘检测路由
from app.api.v1.endpoints import config_router  # 导入配置管理路由
from app.middleware.jwt_middleware import JWTMiddleware
from app.services.thread_pool_manager import shutdown_executor
from app.utils.logger import get_logger

logger=get_logger()

@asynccontextmanager
async def lifespan(app66: FastAPI):
    # 启动前加载 OpenClaw 通知配置
    try:
        import json
        from app.services.openclaw_notification_service import OpenClawNotificationService
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "system_config.json")
        with open(config_path) as f:
            config = json.load(f)
        OpenClawNotificationService.configure(config.get("notification", {}))
        logger.info("OpenClaw通知服务配置完成")
    except Exception as e:
        logger.warning(f"OpenClaw通知配置加载失败(不影响系统运行): {e}")
    yield
    # 结束后要执行的
    shutdown_executor()


# 创建 FastAPI 实例
app = FastAPI(
    lifespan=lifespan,
    title="园区智能安防系统API",
    description="基于FASTAPI框架的后端服务",
    version="1.0.0"
)
# 配置允许跨域的源（前端地址）
origins = [
    "http://localhost:5173",  # 你的前端地址
    # 若需要，可添加其他允许的源，如 "http://localhost:3000" 等
]

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，方便局域网访问
    allow_credentials=True,
    allow_methods=["*"],    # 允许所有 HTTP 方法（GET/POST 等）
    allow_headers=["*"],    # 允许所有请求头
)

# 静态文件目录
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 手机摄像头页面路由
@app.get("/phone-camera")
async def get_phone_camera_page():
    """手机摄像头推流页面"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "phone-camera.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    return {"error": "页面不存在"}


@app.get("/phone-location")
async def get_phone_location_page():
    """手机位置获取页面"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "phone-location.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    return {"error": "页面不存在"}


# # 添加 JWT 中间件
# app.add_middleware(JWTMiddleware)

# 注册路由（给接口加统一前缀 /api/v1，方便版本管理）
# 这行代码的作用是：
# 整合接口：将 product.router 中收集的所有接口注册到主应用 app 中
# 设置访问路径前缀：为所有产品相关接口添加统一前缀 /api/v1/products
# 版本管理：通过 v1 这样的版本号，方便后续升级 API 版本
app.include_router(sign_in_or_up_router.router, prefix="/api/v1", tags=["注册登录"])
app.include_router(safety_analysis_router.router, prefix="/api/v1/safety_analysis", tags=["安防分析控制"])
app.include_router(alarm_handle_record_router.router,prefix="/api/v1/alarm_handle_records",tags=["告警处理记录"])
app.include_router(alarm_router.router,prefix="/api/v1/alarms",tags=["告警管理"])
app.include_router(user_router.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(camera_router.router, prefix="/api/v1/camera_infos", tags=["摄像头管理"])
app.include_router(park_area_router.router, prefix="/api/v1/park_areas", tags=["园区区域管理"])
app.include_router(crop_disease_detection.router, prefix="/api/v1", tags=["农作物病害检测"])
app.include_router(citrus_detection.router, prefix="/api/v1", tags=["柑橘成熟度检测"])
app.include_router(config_router.router, prefix="/api/v1", tags=["配置管理"])

# 根路径
@app.get("/")
def read_root():
    return {"status": "运行中", "service": "YOLO安全监测系统-MVP"}

# 启动服务（开发环境用，生产环境用 uvicorn 命令启动）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8089)