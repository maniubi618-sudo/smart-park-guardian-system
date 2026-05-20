# 园区智能安防系统

基于YOLO模型的园区安全规范监测系统，使用计算机视觉技术实时检测园区内的安全隐患，包括未戴安全帽、未穿反光衣、区域入侵、火焰和烟雾等。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      前端应用 (Vue 3)                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │ 仪表盘  │ │ 告警管理 │ │ 摄像头  │ │ 用户管理 │ │ 地图管理 │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ AI助手  │ │ 设置管理 │ │ 园区管理 │ │ 手机定位 │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
└────────────────────┬────────────────────────────────────────┘
                   │ HTTP/WebSocket
                   │
┌──────────────────┴───────────────────────────────────────────┐
│              后端服务 (FastAPI)                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │ 认证模块 │ │ 告警模块 │ │ 摄像头  │ │ 用户模块 │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │ 园区模块 │ │ WebSocket│ │ YOLO模型 │ │ AI助手  │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │
┌──────────────────┴───────────────────────────────────────────┐
│              数据层 (MySQL + 阿里云OSS)                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ 用户数据 │ │ 告警数据 │ │ 摄像头  │              │
│  └─────────┘ └─────────┘ └─────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## 项目简介

本项目是一个智能安防监控系统，通过连接园区内的摄像头，利用YOLO目标检测模型实时分析视频流，自动识别并报警以下安全隐患：

- 安全规范违规：未戴安全帽、未穿反光衣
- 区域入侵：检测禁止进入区域的人体或车辆
- 火警隐患：检测火焰和烟雾
- **支持手机摄像头**：可通过手机浏览器连接作为实时监控设备，支持闪光灯控制和画面实时分析

系统采用前后端分离架构：
- **后端**：FastAPI构建RESTful API服务，支持实时告警推送、告警处理记录、摄像头管理等功能
- **前端**：Vue 3 + Vite构建现代化Web应用，提供直观的用户界面和丰富的数据可视化

### 主要功能模块

1. **视频流采集与模型推理模块**
   - 拉取指定摄像头RTSP流
   - 调用YOLO模型实时检测安全隐患场景
   - 检测到异常时触发告警并生成截图
   - 支持4种分析模式：全部检测、安全规范检测、区域入侵检测、火警检测

2. **AI智能问答助手**
   - 基于腾讯混元大模型
   - 可咨询园区安全相关问题
   - 结合历史告警数据提供智能分析

3. **告警管理模块**
   - 告警数据存储与状态管理
   - 支持告警状态更新（未处理→处理中→已解决/误报）
   - 通过WebSocket推送实时告警到前端
   - 告警处理记录全程跟踪

4. **摄像头管理模块**
   - 摄像头基础信息CRUD操作
   - 摄像头在线/离线状态检测
   - RTSP连接测试功能
   - 支持本地视频文件分析
   - **手机摄像头功能**
     - 支持手机浏览器访问作为实时监控摄像头
     - 手机端支持闪光灯控制
     - 手机摄像头画面实时分析功能（不存入数据库）
     - 分析结果实时显示和告警提示

5. **地图展示模块**
   - 基于Leaflet和高德地图
   - 展示摄像头分布
   - 告警位置可视化

6. **用户与权限模块**
   - 用户注册、登录和JWT认证
   - 基于角色的权限控制（管理员、安保管理员、普通操作员）

7. **数据统计与分析模块**
   - 告警统计报表
   - 今日告警处理情况分析
   - 高风险区域排名

## 项目结构

```
smart-park-guardian-system/
├── app/                          # 后端服务
│   ├── api/                      # API接口层
│   │   └── v1/
│   │       └── endpoints/        # 具体接口
│   │           ├── alarm_handle_record_router.py
│   │           ├── alarm_router.py
│   │           ├── camera_router.py
│   │           ├── park_area_router.py
│   │           ├── safety_analysis_router.py
│   │           ├── sign_in_or_up_router.py
│   │           └── user_router.py
│   ├── services/                 # 业务逻辑层
│   │   ├── ai_assistant_service.py      # AI问答服务
│   │   ├── alarm_broadcast_service.py   # 告警广播
│   │   ├── alarm_handle_record_service.py
│   │   ├── alarm_service.py
│   │   ├── camera_info_service.py
│   │   ├── detection_service.py         # YOLO检测服务
│   │   ├── historical_analysis_service.py
│   │   ├── park_area_service.py
│   │   ├── phone_camera_manager.py       # 手机摄像头管理
│   │   ├── safety_analysis_service.py    # 安防分析服务
│   │   ├── sign_in_or_up_service.py
│   │   ├── storage_service.py            # 阿里云OSS存储
│   │   ├── thread_pool_manager.py
│   │   ├── user_service.py
│   │   ├── video_service.py
│   │   ├── voice_broadcast_service.py    # 语音播报
│   │   └── websocket_manager.py          # WebSocket管理
│   ├── crud/                     # 数据访问层
│   ├── DB_models/               # 数据库模型
│   ├── JSON_schemas/            # Pydantic数据模型
│   ├── config/                   # 配置文件
│   ├── dependencies/             # 依赖项
│   ├── middleware/               # 中间件
│   ├── models/                   # YOLO模型文件
│   │   ├── helmet_model.pt       # 安全帽检测模型
│   │   ├── vest_model.pt         # 反光衣检测模型
│   │   ├── fire_smoke_seg_model.pt # 火焰烟雾检测模型
│   │   └── yolo11s.pt            # 人体车辆检测模型
│   ├── objects/                  # 业务对象
│   ├── static/                   # 静态文件
│   ├── utils/                    # 工具类
│   ├── main.py                   # HTTP模式入口
│   └── main_https.py             # HTTPS模式入口
├── park-safety-frontend/        # 前端项目
│   ├── src/
│   │   ├── components/           # 公共组件
│   │   │   ├── AIAssistant.vue   # AI助手组件
│   │   │   └── MainLayout.vue    # 主布局组件
│   │   ├── router/              # 路由配置
│   │   ├── stores/              # Pinia状态管理
│   │   │   ├── alarms.js
│   │   │   ├── areas.js
│   │   │   ├── auth.js
│   │   │   ├── cameras.js
│   │   │   ├── layout.js
│   │   │   └── users.js
│   │   ├── services/            # API服务
│   │   │   ├── api.js
│   │   │   └── websocket.js
│   │   ├── views/               # 页面组件
│   │   │   ├── alarms/          # 告警管理
│   │   │   ├── areas/           # 园区管理
│   │   │   ├── auth/            # 认证页面
│   │   │   ├── cameras/         # 摄像头管理
│   │   │   ├── dashboard/       # 仪表盘
│   │   │   ├── map/             # 地图展示
│   │   │   ├── settings/        # 设置管理
│   │   │   ├── users/           # 用户管理
│   │   │   └── PhoneLocation.vue # 手机定位
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   └── package.json
├── docs/                         # 文档目录
├── requirements.txt              # Python依赖
└── README.md
```

## 技术栈

### 后端技术栈

- **框架**：FastAPI
- **Python版本**：3.8+
- **数据库**：MySQL 5.7+ / SQLite
- **ORM**：SQLAlchemy 2.0
- **数据验证**：Pydantic
- **认证**：JWT (python-jose)
- **密码加密**：bcrypt
- **YOLO模型**：Ultralytics
- **对象存储**：阿里云OSS
- **WebSocket**：websockets
- **异步任务**：threading / concurrent.futures

### 前端技术栈

- **框架**：Vue 3 + Vite
- **状态管理**：Pinia
- **路由**：Vue Router
- **HTTP客户端**：Axios
- **UI组件库**：Element Plus
- **图表库**：ECharts
- **3D引擎**：Three.js
- **地图**：Leaflet + 高德地图
- **二维码**：QRCode
- **实时通信**：WebSocket

## 项目运行

### 环境要求

- Python 3.8+
- Node.js 16+
- MySQL 5.7+ (可选，默认使用SQLite)
- pip包管理工具

### 后端安装步骤

1. 进入项目目录：
   ```bash
   cd smart-park-guardian-system
   ```

2. 创建并激活虚拟环境：
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   复制`.envexample`文件为`.env`，并根据实际情况修改配置：
   ```bash
   copy .envexample .env   # Windows
   # 或
   cp .envexample .env     # Linux/Mac
   ```

   主要配置项包括：
   - 数据库连接信息（MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE）
   - 阿里云OSS配置（用于存储告警截图）
   - 腾讯混元API密钥（HUNYUAN_API_KEY，用于AI助手功能）
   - 安全配置（SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES）

5. 启动服务：
   - **普通模式**（用于基本功能）：
     ```bash
     python app/main.py
     ```
     或使用uvicorn命令启动：
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port 8089
     ```

   - **HTTPS模式**（用于手机摄像头功能）：
     ```bash
     python app/main_https.py
     ```
     或使用uvicorn命令启动：
     ```bash
     uvicorn app.main_https:app --host 0.0.0.0 --port 8443 --ssl-keyfile=app/server.key --ssl-certfile=app/server.crt
     ```

   - **使用启动脚本**（Windows）：
     - `start-basic.bat` - 启动普通HTTP后端（端口8089）
     - `start-all.bat` - 启动所有服务
     - `start-simple.bat` - 简化启动

   **注意**：手机摄像头功能需要使用HTTPS模式（端口8443），因为浏览器要求在HTTPS或localhost环境中才能访问摄像头。

### 前端安装步骤

1. 进入前端项目目录：
   ```bash
   cd park-safety-frontend
   ```

2. 安装依赖：
   ```bash
   npm install
   ```

3. 启动开发服务器：
   ```bash
   npm run dev
   ```

4. 访问前端应用：
   打开浏览器访问 http://localhost:3000

### 前端构建部署

生产环境构建：
```bash
npm run build
```

构建产物将生成在 `dist` 目录，可部署到任何静态文件服务器（如Nginx）。

## API文档

项目启动后，可通过以下地址访问API文档：
- Swagger UI: http://localhost:8089/docs
- ReDoc: http://localhost:8089/redoc

## 登录账户

可以使用数据库管理软件（比如DBeaver），查看账户信息。默认管理员用户名通常为 `admin`。

## 前端功能模块

### 1. 认证系统
- 用户登录/注册
- JWT令牌管理
- 路由权限守卫

### 2. 仪表盘
- 实时统计数据展示（今日告警、摄像头状态、未处理告警）
- 告警趋势图表
- 最近未处理告警列表

### 3. 告警管理
- 告警列表展示
- 多条件筛选搜索
- 告警处理功能
- 告警状态管理
- 告警详情查看

### 4. 摄像头管理
- 摄像头状态统计
- 摄像头CRUD操作
- 实时状态监控
- 分析模式配置（全部/安全规范/区域入侵/火警）
- RTSP连接测试
- 实时视频预览
- 本地视频分析
- **手机摄像头功能**

### 5. 地图管理
- 摄像头分布可视化
- 基于Leaflet和 高德地图
- 点击查看摄像头详情

### 6. AI助手
- 基于腾讯混元大模型
- 智能问答交互
- 结合园区安全数据分析

### 7. 园区管理
- 园区区域信息管理
- 区域与摄像头关联

### 8. 用户管理
- 用户信息管理
- 角色权限管理
- 用户CRUD操作

### 9. 设置管理
- 系统参数配置
- 个性化设置

## 快速启动指南

### 1. 启动后端服务

#### 选项A：普通模式（仅基本功能）
```bash
# 激活虚拟环境
venv\Scripts\activate

# 启动后端服务
python app/main.py
```

后端服务将在 `http://localhost:8089` 启动，API文档可通过 `http://localhost:8089/docs` 访问。

#### 选项B：HTTPS模式（支持手机摄像头）
```bash
# 激活虚拟环境
venv\Scripts\activate

# 启动HTTPS后端服务
python app/main_https.py
```

HTTPS后端服务将在 `https://localhost:8443` 启动，API文档可通过 `https://localhost:8443/docs` 访问。

**注意**：首次访问HTTPS时，浏览器会提示"不安全"，点击"高级" → "继续前往"即可信任自签名证书。

### 2. 启动前端服务

```bash
# 进入前端目录
cd park-safety-frontend

# 安装依赖（首次运行）
npm install

# 启动前端开发服务器
npm run dev
```

前端服务将在 `http://localhost:3000` 启动。

### 3. 访问系统

打开浏览器访问 `http://localhost:3000`，使用数据库中的账户登录系统。

## 手机摄像头功能使用指南

### 功能概述

手机摄像头功能允许您使用手机浏览器访问系统，将手机作为实时监控摄像头，支持画面推流、闪光灯控制和实时分析。

### 工作原理

系统使用以下方式获取和构建连接地址：
1. **自动检测当前设备IP地址**：通过WebRTC STUN服务器获取本机在局域网中的真实IP地址
2. **构建HTTPS连接地址**：使用检测到的IP地址构建 `https://{本机IP}:8443/phone-camera` 格式的地址
3. **生成二维码**：便于手机浏览器扫描访问

### 使用步骤

1. **打开手机摄像头弹窗**
   - 进入摄像头管理页面
   - 点击"手机摄像头"按钮
   - 系统会自动检测当前设备的局域网IP地址

2. **连接手机**
   - 切换到"手机连接"标签页
   - 页面会显示使用**当前设备IP地址**构建的连接地址
   - 使用手机浏览器扫描二维码或输入显示的连接地址
   - 确保手机和电脑在同一局域网内

3. **开启摄像头**
   - 在手机浏览器中点击"启用摄像头"按钮
   - 允许浏览器访问摄像头权限

4. **查看和分析画面**
   - 切换到"手机推流观看"标签页查看实时画面
   - 选择分析模式并点击"开始分析"
   - 系统会自动分析画面并在检测到告警时弹出提示

5. **手机端控制**
   - 在手机浏览器中可控制闪光灯开关
   - 可切换前后摄像头
   - 支持拍照功能

### 注意事项

- 手机和电脑必须连接到同一Wi-Fi网络
- 需要允许浏览器访问摄像头权限
- 建议使用HTTPS连接以获得更好的兼容性
- 手机摄像头分析数据不存入数据库，仅用于实时显示和告警

## AI助手功能

AI助手基于腾讯混元大模型，可以回答关于园区安全管理的各类问题。

### 使用方式

1. 点击左侧导航栏的"AI助手"
2. 在对话框中输入您的问题
3. AI助手将结合系统数据和知识库给出回答

### 支持的问答类型

- 告警数据查询与分析
- 安全规范咨询
- 摄像头状态查询
- 系统使用帮助
- 其他园区安全管理相关问题

## 常见问题

### Q1: 前端无法连接后端API？

**A**: 请确保：
- 后端服务已启动（默认端口8089）
- 前端开发服务器已启动（默认端口3000）
- 检查浏览器控制台是否有CORS错误

### Q2: 手机摄像头无法连接？

**A**: 请确保：
- 后端使用HTTPS模式运行（端口8443）
- 手机和电脑在同一局域网内
- 浏览器已信任自签名证书

### Q3: YOLO模型检测不准确？

**A**: 可根据实际场景需求重新训练模型，当前包含：
- 安全帽检测模型
- 反光衣检测模型
- 火焰烟雾检测模型
- 人体车辆检测模型

### Q4: 告警未收到推送？

**A**: 请检查：
- WebSocket连接是否正常
- 浏览器通知权限是否开启
- 告警规则是否正确配置
