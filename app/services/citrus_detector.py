
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple
import sys

try:
    from ultralytics import YOLO
except ImportError:
    print("⚠️ ultralytics not found, will try to use system one")
    pass

# 导入配置管理器
from .config_manager import get_config_manager


class CitrusDetector:
    """
    柑橘成熟度检测服务类
    基于 YOLOv10 模型进行柑橘成熟度检测
    """
    
    # 成熟度范围配置
    MATURITY_RANGES = {
        "unripe_orange": (0, 60),
        "ripe_orange": (60, 95),
        "rotten_orange": (95, 100)
    }
    
    # 颜色配置
    COLOR_MAP = {
        "unripe_orange": (0, 128, 0),    # 深绿色 - 未成熟橙子
        "ripe_orange": (0, 165, 255),    # 橙色 - 成熟橙子
        "rotten_orange": (128, 128, 128),# 灰色 - 腐烂橙子
    }
    
    def __init__(self, model_path: str = None):
        """
        初始化检测器
        
        Args:
            model_path: 模型权重路径
        """
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "models",
                "citrus_maturity.pt"
            )
        
        self.model_path = model_path
        self.model = None
        
        # 从配置管理器获取参数
        config_mgr = get_config_manager()
        self.confidence = config_mgr.get("agriculture.citrusConfidence", 0.25)
        self.iou_threshold = config_mgr.get("agriculture.citrusIouThreshold", 0.45)
        
        self._load_model()
    
    def update_from_config(self):
        """从配置管理器更新参数"""
        config_mgr = get_config_manager()
        self.confidence = config_mgr.get("agriculture.citrusConfidence", 0.25)
        self.iou_threshold = config_mgr.get("agriculture.citrusIouThreshold", 0.45)
    
    def _load_model(self):
        """加载模型"""
        try:
            if os.path.exists(self.model_path):
                print(f"📦 加载柑橘成熟度检测模型: {self.model_path}")
                self.model = YOLO(self.model_path)
                print(f"✅ 模型加载成功，支持 {len(self.model.names)} 个类别")
                print(f"📋 类别: {list(self.model.names.values())}")
            else:
                print(f"⚠️ 模型文件不存在: {self.model_path}")
                print("💡 请运行 quick_copy.py 或手动复制模型文件")
        except Exception as e:
            print(f"❌ 加载模型失败: {e}")
    
    def calculate_maturity(self, class_name, conf):
        """计算成熟度"""
        if class_name in self.MATURITY_RANGES:
            low, high = self.MATURITY_RANGES[class_name]
            maturity = round(low + conf * (high - low), 1)
            if maturity >= 80.0:
                label = "橙色成熟"
            elif maturity >= 55.0:
                label = "转色中"
            else:
                label = "偏青"
            days_to_ripe = max(0, round((100 - maturity) / 5))
            return maturity, label, days_to_ripe
        return None, None, None
    
    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        """预处理图像"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img
    
    def detect(self, image_bytes: bytes) -> List[Dict]:
        """
        执行检测
        
        Args:
            image_bytes: 图像字节数据
            
        Returns:
            检测结果列表
        """
        if self.model is None:
            return []
        
        try:
            img = self.preprocess(image_bytes)
            # 降低置信度和IOU阈值以提高召回率
            results = self.model(
                img, 
                conf=self.confidence, 
                iou=self.iou_threshold,
                verbose=False
            )
            return self._parse_results(results)
        except Exception as e:
            print(f"❌ 检测失败: {e}")
            return []
    
    def _parse_results(self, results) -> List[Dict]:
        """解析模型输出"""
        predictions = []
        for result in results:
            for box in result.boxes:
                class_name = result.names[int(box.cls)]
                confidence = float(box.conf)
                
                # 计算成熟度信息
                maturity, maturity_label, days_to_ripe = self.calculate_maturity(class_name, confidence)
                
                predictions.append({
                    "class": class_name,
                    "class_id": int(box.cls),
                    "confidence": confidence,
                    "maturity": maturity,
                    "maturity_label": maturity_label,
                    "days_to_ripe": days_to_ripe,
                    "bbox": {
                        "x1": int(box.xyxy[0][0]),
                        "y1": int(box.xyxy[0][1]),
                        "x2": int(box.xyxy[0][2]),
                        "y2": int(box.xyxy[0][3])
                    }
                })
        return predictions
    
    def annotate_image(self, image_bytes: bytes, predictions: List[Dict]) -> str:
        """绘制标注并返回 base64 编码图像"""
        try:
            img = self.preprocess(image_bytes)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            for pred in predictions:
                box = pred["bbox"]
                x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
                
                # 获取颜色
                color = self.COLOR_MAP.get(pred["class"], (255, 255, 255))
                
                # 绘制框
                cv2.rectangle(img_bgr, (x1, y1), (x2, y2), color, 2)
                
                # 构建标签 - 显示成熟度
                if pred.get("maturity") is not None:
                    label = f"{pred['maturity']}% {pred['confidence']:.2f}"
                    if pred.get("days_to_ripe", 0) > 0:
                        label += f" {pred['days_to_ripe']}天"
                else:
                    label = f"{pred['class']} {pred['confidence']:.2f}"
                
                cv2.putText(img_bgr, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            _, buffer = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            import base64
            base64_image = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"
        except Exception as e:
            print(f"❌ 标注图像失败: {e}")
            return ""
    
    def detect_and_annotate(self, image_bytes: bytes) -> Tuple[List[Dict], str]:
        """检测并返回标注图像"""
        predictions = self.detect(image_bytes)
        annotated_image = self.annotate_image(image_bytes, predictions)
        return predictions, annotated_image


# 全局单例实例
_citrus_detector_instance = None


def get_citrus_detector() -> CitrusDetector:
    """获取检测器单例"""
    global _citrus_detector_instance
    if _citrus_detector_instance is None:
        _citrus_detector_instance = CitrusDetector()
    return _citrus_detector_instance
