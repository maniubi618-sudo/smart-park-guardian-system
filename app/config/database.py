from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.app_settings import settings

# 数据库连接URL（URL编码密码，防止@等特殊字符被误解析）
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{quote_plus(settings.MYSQL_PASSWORD)}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    "?charset=utf8mb4"
)

# 创建引擎（添加连接池配置）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=True,
    pool_size=10,              # 连接池大小
    max_overflow=20,           # 超过pool_size后最多可以创建的连接数
    pool_recycle=3600,         # 连接回收时间（秒），防止连接超时
    pool_pre_ping=True,        # 连接前ping一下，确保连接有效
    pool_timeout=30            # 获取连接的超时时间
)
# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 基类
Base = declarative_base()