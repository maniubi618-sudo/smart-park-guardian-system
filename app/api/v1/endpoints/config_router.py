#!/usr/bin/env python3
"""
配置管理 API
提供获取和更新系统配置的接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import sys
import os

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.services.config_manager import get_config_manager
from app.services.citrus_detector import get_citrus_detector
from app.services.pest_detector import get_pest_detector

router = APIRouter(prefix="/config", tags=["配置管理"])


class ConfigUpdate(BaseModel):
    """配置更新请求模型"""
    detection: Dict[str, Any] = None
    agriculture: Dict[str, Any] = None
    system: Dict[str, Any] = None
    notification: Dict[str, Any] = None


@router.get("/", summary="获取完整配置")
async def get_config():
    """获取系统完整配置"""
    config_mgr = get_config_manager()
    return {
        "success": True,
        "data": config_mgr.get_config()
    }


@router.put("/", summary="更新配置")
async def update_config(config: ConfigUpdate):
    """更新系统配置"""
    try:
        config_mgr = get_config_manager()
        
        # 构建更新数据
        update_data = {}
        if config.detection:
            update_data["detection"] = config.detection
        if config.agriculture:
            update_data["agriculture"] = config.agriculture
        if config.system:
            update_data["system"] = config.system
        if config.notification:
            update_data["notification"] = config.notification
        
        if update_data:
            config_mgr.update_config(update_data)
            
            # 更新检测服务的配置
            try:
                citrus_detector = get_citrus_detector()
                citrus_detector.update_from_config()
            except:
                pass
                
            try:
                pest_detector = get_pest_detector()
                pest_detector.update_from_config()
            except:
                pass
        
        return {
            "success": True,
            "message": "配置更新成功",
            "data": config_mgr.get_config()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/{section}", summary="获取指定分区配置")
async def get_section_config(section: str):
    """获取指定分区的配置
    
    Args:
        section: 配置分区，可选值: detection, agriculture, system, notification
    """
    config_mgr = get_config_manager()
    config = config_mgr.get_config()
    
    if section not in config:
        raise HTTPException(status_code=404, detail=f"配置分区不存在: {section}")
    
    return {
        "success": True,
        "data": config[section]
    }
