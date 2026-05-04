
# ===================== 强制注入 GSConv 解决报错 =====================
import torch
import torch.nn as nn

# 先尝试导入原版 Conv
try:
    from ultralytics.nn.modules.conv import Conv
except Exception as e:
    print(f"Warning [PestDetector] Import Conv failed: {e}")
    pass

# 定义训练时使用的 GSConv
class GSConv(nn.Module):
    def __init__(self, c1, c2, k=1, s=1, p=0, g=1, d=1, act=True):
        super().__init__()
        c_ = c2 // 2
        # 兼容参数，使用 autopad
        self.cv1 = Conv(c1, c_, k, s, None, g, d, act)
        self.cv2 = Conv(c_, c_, 5, 1, None, c_, d, act)

    def forward(self, x):
        x1 = self.cv1(x)
        x2 = self.cv2(x1)
        return torch.cat((x1, x2), dim=1)


# 定义其他可能缺失的类
class GSConvns(GSConv):
    def __init__(self, c1, c2, k=1, s=1, g=1, act=True):
        super().__init__(c1, c2, k=1, s=1, g=1, act=True)
        c_ = c2 // 2
        self.shuf = Conv(c_ * 2, c2, 1, 1, 0, bias=False)

    def forward(self, x):
        x1 = self.cv1(x)
        x2 = torch.cat((x1, self.cv2(x1)), dim=1)
        return torch.nn.functional.relu(self.shuf(x2))


class GSBottleneck(nn.Module):
    def __init__(self, c1, c2, k=3, s=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.conv_lighting = nn.Sequential(
            GSConv(c1, c_, 1, 1),
            GSConv(c_, c2, 3, 1, act=False)
        )
        self.shortcut = Conv(c1, c2, 1, 1, act=False)

    def forward(self, x):
        return self.conv_lighting(x) + self.shortcut(x)


class VoVGSCSP(nn.Module):
    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c1, c_, 1, 1)
        self.gsb = nn.Sequential(*(GSBottleneck(c_, c_, e=1.0) for _ in range(n)))
        self.res = Conv(c_, c_, 3, 1, act=False)
        self.cv3 = Conv(2 * c_, c2, 1)

    def forward(self, x):
        x1 = self.gsb(self.cv1(x))
        y = self.cv2(x)
        return self.cv3(torch.cat((y, x1), dim=1))


class VoVGSCSPC(VoVGSCSP):
    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__(c1, c2)
        c_ = int(c2 * 0.5)
        self.gsb = GSBottleneck(c_, c_, 1, 1)


# 把所有需要的类注册到 ultralytics 模块
import sys
try:
    import ultralytics.nn.modules.conv as conv_module
    
    classes_to_register = {
        'GSConv': GSConv,
        'GSConvns': GSConvns,
        'GSBottleneck': GSBottleneck,
        'VoVGSCSP': VoVGSCSP,
        'VoVGSCSPC': VoVGSCSPC
    }
    
    for name, cls in classes_to_register.items():
        if not hasattr(conv_module, name):
            setattr(conv_module, name, cls)
            print(f"[PestDetector] Registered custom class: {name}")
    print("[PestDetector] All custom classes registered OK!")

except Exception as e:
    print(f"Warning [PestDetector] Register classes failed: {e}")
    pass
# ==================================================================


# 以下是原代码
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple

try:
    from ultralytics import YOLO
except ImportError as e:
    print(f"Warning [PestDetector] Import YOLO failed: {e}")
    pass


class PestDetector:
    """
    害虫检测服务类
    基于 YOLOv12 模型进行害虫检测
    """
    
    def __init__(self, model_path: str = None, confidence: float = 0.5):
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'models',
                'pest_detector.pt'
            )
        
        self.model_path = model_path
        self.confidence = confidence
        self.model = None
        self._load_model()
    
    def _load_model(self):
        try:
            if os.path.exists(self.model_path):
                print(f"[PestDetector] Loading model: {self.model_path}")
                self.model = YOLO(self.model_path)
                print(f"OK [PestDetector] Model loaded, supports {len(self.model.names)} classes")
            else:
                print(f"Warning [PestDetector] Model file not found: {self.model_path}")
        except Exception as e:
            print(f"Error [PestDetector] Load model failed: {e}")
            import traceback
            traceback.print_exc()
    
    def preprocess(self, image_bytes: bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img
    
    def detect(self, image_bytes: bytes):
        if self.model is None:
            return []
        
        try:
            img = self.preprocess(image_bytes)
            results = self.model(img, conf=self.confidence, verbose=False)
            return self._parse_results(results)
        except Exception as e:
            print(f"Error [PestDetector] Detection failed: {e}")
            return []
    
    def _parse_results(self, results):
        predictions = []
        for result in results:
            for box in result.boxes:
                predictions.append({
                    'class': result.names[int(box.cls)],
                    'class_id': int(box.cls),
                    'confidence': float(box.conf),
                    'bbox': {
                        'x1': int(box.xyxy[0][0]),
                        'y1': int(box.xyxy[0][1]),
                        'x2': int(box.xyxy[0][2]),
                        'y2': int(box.xyxy[0][3])
                    }
                })
        return predictions
    
    def annotate_image(self, image_bytes: bytes, predictions):
        try:
            img = self.preprocess(image_bytes)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            for pred in predictions:
                box = pred['bbox']
                x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
                
                cv2.rectangle(img_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                label = f"{pred['class']} {pred['confidence']:.2f}"
                cv2.putText(img_bgr, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            _, buffer = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            import base64
            base64_image = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"
        except Exception as e:
            print(f"Error [PestDetector] Annotation failed: {e}")
            return ""
    
    def detect_and_annotate(self, image_bytes: bytes):
        predictions = self.detect(image_bytes)
        annotated_image = self.annotate_image(image_bytes, predictions)
        return predictions, annotated_image


# 全局单例实例
_detector_instance = None


def get_pest_detector():
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = PestDetector()
    return _detector_instance


