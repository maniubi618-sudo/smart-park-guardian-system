#!/usr/bin/env python3
"""
配置管理服务
提供全局配置的加载、保存和动态更新
"""

import os
import json
import threading
from typing import Dict, Any, Optional

# 默认配置
DEFAULT_CONFIG = {
    "detection": {
        "fireThreshold": 0.7,
        "helmetThreshold": 0.7,
        "vestThreshold": 0.7,
        "alarmDelay": 0,
        "debounceTime": 1,
        "enableHelmet": True,
        "enableVest": True,
        "enableVehicleIntrusion": True,
        "enableFire": True,
        "enablePest": True,
        "enableCropGrowth": True,
        "enableCitrus": True
    },
    "agriculture": {
        "citrusConfidence": 0.25,
        "citrusIouThreshold": 0.45,
        "cropDiseaseConfidence": 0.25,
        "cropDiseaseIouThreshold": 0.45
    },
    "system": {
        "dbHost": "localhost",
        "dbPort": 3306,
        "dbUser": "root",
        "dbPassword": "123456",
        "dbName": "yolo_safety",
        "snapshotPath": "./snapshots/"
    },
    "notification": {
        "enableWebSocket": True,
        "enableEmail": False,
        "emailServer": "",
        "emailPort": 587,
        "emailSender": "",
        "emailPassword": "",
        "emailRecipients": ""
    }
}


class ConfigManager:
    """配置管理器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._config = DEFAULT_CONFIG.copy()
            self._config_file = self._get_config_file_path()
            self._load_from_file()

    def _get_config_file_path(self) -> str:
        """获取配置文件路径"""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_dir = os.path.join(base_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "system_config.json")

    def _load_from_file(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # 合并配置，保留默认值
                self._merge_config(self._config, loaded_config)
                print(f"✅ 配置已从 {self._config_file} 加载")
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")

    def _merge_config(self, target: Dict, source: Dict):
        """递归合并配置"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value

    def _save_to_file(self):
        """保存配置到文件"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")

    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config.copy()

    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key_path: 配置路径，例如 "detection.fireThreshold"
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any):
        """设置配置项
        
        Args:
            key_path: 配置路径，例如 "detection.fireThreshold"
            value: 配置值
        """
        keys = key_path.split('.')
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self._save_to_file()

    def update_config(self, new_config: Dict[str, Any]):
        """批量更新配置
        
        Args:
            new_config: 新的配置字典
        """
        self._merge_config(self._config, new_config)
        self._save_to_file()
        print("[OK] 配置已更新")


# 全局单例
_config_manager_instance = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance
