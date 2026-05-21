import os
import cv2
import numpy as np
from typing import List, Dict, Tuple
import sys

try:
    from ultralytics import YOLO
except ImportError:
    print("[WARN] ultralytics not found, will try to use system one")
    pass

# 导入配置管理器
from .config_manager import get_config_manager


class AppleRipenessDetector:
    """
    苹果成熟度检测服务类
    基于 YOLOv10 模型进行苹果成熟度检测
    """

    # 成熟度类别配置
    RIPENESS_CLASSES = {
        0: {"name": "20%_ripe", "maturity": 20, "label": "仍在生长"},
        1: {"name": "40%_ripe", "maturity": 40, "label": "早期发育"},
        2: {"name": "60%_ripe", "maturity": 60, "label": "中期成熟"},
        3: {"name": "80%_ripe", "maturity": 80, "label": "即将成熟"},
        4: {"name": "100%_ripe", "maturity": 100, "label": "完全成熟"}
    }

    # 颜色配置 (BGR格式)
    COLOR_MAP = {
        "20%_ripe": (0, 128, 0),      # 深绿色 - 仍在生长
        "40%_ripe": (0, 200, 0),      # 浅绿色 - 早期发育
        "60%_ripe": (0, 255, 255),    # 黄色 - 中期成熟
        "80%_ripe": (0, 165, 255),    # 橙色 - 即将成熟
        "100%_ripe": (0, 0, 255),     # 红色 - 完全成熟
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
                "apple.pt"
            )

        self.model_path = model_path
        self.model = None

        # 从配置管理器获取参数
        config_mgr = get_config_manager()
        self.confidence = config_mgr.get("agriculture.appleConfidence", 0.25)
        self.iou_threshold = config_mgr.get("agriculture.appleIouThreshold", 0.45)

        self._load_model()

    def update_from_config(self):
        """从配置管理器更新参数"""
        config_mgr = get_config_manager()
        self.confidence = config_mgr.get("agriculture.appleConfidence", 0.25)
        self.iou_threshold = config_mgr.get("agriculture.appleIouThreshold", 0.45)

    def _load_model(self):
        """加载模型"""
        try:
            if os.path.exists(self.model_path):
                print(f"[LOAD] 加载苹果成熟度检测模型: {self.model_path}")
                self.model = YOLO(self.model_path)
                print(f"[OK] 模型加载成功，支持 {len(self.model.names)} 个类别")
                print(f"[INFO] 类别: {list(self.model.names.values())}")
            else:
                print(f"[WARN] 模型文件不存在: {self.model_path}")
                print("[HINT] 请运行 quick_copy.py 或手动复制模型文件")
        except Exception as e:
            print(f"[ERROR] 加载模型失败: {e}")

    def calculate_maturity(self, class_id, class_name, conf):
        """计算成熟度"""
        # 尝试通过类别ID获取成熟度信息
        if class_id in self.RIPENESS_CLASSES:
            ripeness_info = self.RIPENESS_CLASSES[class_id]
            maturity = ripeness_info["maturity"]
            label = ripeness_info["label"]
            # 根据成熟度计算预计收获天数
            if maturity >= 100:
                days_to_ripe = 0
            elif maturity >= 80:
                days_to_ripe = 3
            elif maturity >= 60:
                days_to_ripe = 7
            elif maturity >= 40:
                days_to_ripe = 14
            else:
                days_to_ripe = 21
            return maturity, label, days_to_ripe

        # 尝试通过类别名称匹配
        class_name_lower = class_name.lower().replace('%', '').replace('_', '-')
        for cls_id, info in self.RIPENESS_CLASSES.items():
            name_normalized = info["name"].lower().replace('%', '').replace('_', '-')
            if name_normalized in class_name_lower or class_name_lower in name_normalized:
                maturity = info["maturity"]
                label = info["label"]
                if maturity >= 100:
                    days_to_ripe = 0
                elif maturity >= 80:
                    days_to_ripe = 3
                elif maturity >= 60:
                    days_to_ripe = 7
                elif maturity >= 40:
                    days_to_ripe = 14
                else:
                    days_to_ripe = 21
                return maturity, label, days_to_ripe

        # 打印警告信息，帮助调试class名称不匹配问题
        print(f"[WARN] 未知苹果类别: {class_name} (ID: {class_id})，使用默认成熟度 50%")
        maturity = 50.0
        label = "未知"
        days_to_ripe = 10
        return maturity, label, days_to_ripe

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
            print(f"[ERROR] 检测失败: {e}")
            return []

    def _parse_results(self, results) -> List[Dict]:
        """解析模型输出"""
        predictions = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls)
                class_name = result.names[class_id]
                confidence = float(box.conf)

                # 计算成熟度信息
                maturity, maturity_label, days_to_ripe = self.calculate_maturity(class_id, class_name, confidence)

                # 调试日志
                print(f"[DEBUG] Apple detection: class={class_name}, conf={confidence}, maturity={maturity}%")

                predictions.append({
                    "class": class_name,
                    "class_id": class_id,
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

                # 构建标签 - 显示成熟度和标签
                if pred.get("maturity") is not None:
                    label = f"{pred['maturity']}% {pred['maturity_label']} {pred['confidence']:.2f}"
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
            print(f"[ERROR] 标注图像失败: {e}")
            return ""

    def detect_and_annotate(self, image_bytes: bytes) -> Tuple[List[Dict], str]:
        """检测并返回标注图像"""
        predictions = self.detect(image_bytes)
        annotated_image = self.annotate_image(image_bytes, predictions)
        return predictions, annotated_image


# 全局单例实例
_apple_detector_instance = None


def get_apple_detector() -> AppleRipenessDetector:
    """获取检测器单例"""
    global _apple_detector_instance
    if _apple_detector_instance is None:
        _apple_detector_instance = AppleRipenessDetector()
    return _apple_detector_instance
