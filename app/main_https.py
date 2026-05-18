# 项目入口：main_https.py
# HTTPS 版本启动文件
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uvicorn
from app.api.v1.endpoints import alarm_handle_record_router  # 导入报警记录接口路由
from app.api.v1.endpoints import alarm_router  # 导入告警记录接口路由
from app.api.v1.endpoints import camera_router  # 导入商品接口路由
from app.api.v1.endpoints import park_area_router  # 导入园区区域接口路由
from app.api.v1.endpoints import safety_analysis_router  # 导入安全分析路由
from app.api.v1.endpoints import sign_in_or_up_router  # 导入注册登录接口路由
from app.api.v1.endpoints import user_router  # 导入用户接口路由
from app.middleware.jwt_middleware import JWTMiddleware
from app.services.thread_pool_manager import shutdown_executor
from app.utils.logger import get_logger

logger = get_logger()


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
        logger.info("OpenClaw通知服务配置完成(HTTPS)")
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

# 挂载路由（注意：路径前缀为 /api/v1/xxx）
app.include_router(sign_in_or_up_router.router, prefix="/api/v1/signinorup", tags=["注册登录"])  # 注册登录路由
app.include_router(user_router.router, prefix="/api/v1/users", tags=["用户信息"])  # 用户信息路由
app.include_router(alarm_router.router, prefix="/api/v1/alarms", tags=["告警信息"])  # 告警信息路由
app.include_router(alarm_handle_record_router.router, prefix="/api/v1/alarm_handle_records", tags=["告警处理记录"])  # 告警处理记录路由
app.include_router(camera_router.router, prefix="/api/v1/camera_infos", tags=["摄像头信息"])  # 摄像头信息路由
app.include_router(park_area_router.router, prefix="/api/v1/park_areas", tags=["园区区域信息"])  # 园区区域信息路由
app.include_router(safety_analysis_router.router, prefix="/api/v1/safety_analysis", tags=["安全分析"])  # 安全分析路由

if __name__ == "__main__":
    # 获取本地IP地址
    import socket
    def get_local_ip():
        try:
            # 获取所有网络接口的IP地址
            import socket
            import os
            
            # 尝试使用ipconfig命令获取IP地址
            if os.name == 'nt':  # Windows
                import subprocess
                output = subprocess.check_output(['ipconfig', '/all'], universal_newlines=True, stderr=subprocess.STDOUT)
                lines = output.split('\n')
                private_ips = []
                for line in lines:
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
                                    private_ips.append(ip)
                # 如果找到私有IP，返回第一个
                if private_ips:
                    return private_ips[0]
            
            # 如果ipconfig命令失败或没有找到私有IP，使用socket方法
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"获取IP地址失败: {e}")
            return "127.0.0.1"
    
    local_ip = get_local_ip()
    
    # SSL证书路径
    cert_dir = os.path.dirname(__file__)
    cert_file = os.path.join(cert_dir, "server.crt")
    key_file = os.path.join(cert_dir, "server.key")
    
    print("\n" + "=" * 50)
    print("  📷 园区智能安防系统 - HTTPS 启动")
    print("=" * 50)
    print()
    print(f"  💻 API文档 (HTTPS):")
    print(f"     https://localhost:8443/docs")
    print()
    print(f"  📱 手机摄像头页面:")
    print(f"     https://{local_ip}:8443/phone-camera")
    print()
    print("  ⚠️  首次访问需信任自签名证书")
    print("     浏览器提示'不安全' → 点击'继续前往'")
    print("=" * 50 + "\n")
    
    # 启动HTTPS服务器
    uvicorn.run(
        "app.main_https:app",
        host="0.0.0.0",
        port=8443,
        ssl_certfile=cert_file,
        ssl_keyfile=key_file
    )
