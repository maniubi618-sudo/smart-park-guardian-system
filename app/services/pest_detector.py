
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
        self.cv1 = Conv(c1, c_, k, s, None, g, d, act)
        self.cv2 = Conv(c_, c_, 5, 1, None, c_, d, act)

    def forward(self, x):
        x1 = self.cv1(x)
        x2 = self.cv2(x1)
        return torch.cat((x1, x2), dim=1)


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


import os
import cv2
import numpy as np
from typing import List, Dict, Tuple

try:
    from ultralytics import YOLO
except ImportError as e:
    print(f"Warning [PestDetector] Import YOLO failed: {e}")
    pass

try:
    from app.services.config_manager import get_config_manager
except ImportError as e:
    print(f"Warning [PestDetector] Import config manager failed: {e}")
    pass


class PestDetector:
    """
    Pest Detection Service
    Optimized YOLO-based pest detection with image preprocessing,
    IoU-aware NMS, and TTA for improved recognition rate.
    """

    def __init__(self, model_path: str = None, confidence: float = None):
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'models',
                'pest_detector.pt'
            )

        self.model_path = model_path
        self.confidence = confidence if confidence is not None else self._get_default_confidence()
        self.iou = self._get_iou_threshold()
        self.enable_tta = self._get_tta_enabled()
        self.enable_preprocess = self._get_preprocess_enabled()
        self.model = None
        self._load_model()

    def _get_default_confidence(self):
        try:
            config_manager = get_config_manager()
            return config_manager.get("agriculture.pestConfidence", 0.5)
        except Exception:
            return 0.5

    def _get_iou_threshold(self):
        """获取 IoU 阈值，农业场景默认更低以减少重叠漏检"""
        try:
            config_manager = get_config_manager()
            return config_manager.get("agriculture.pestIouThreshold", 0.25)
        except Exception:
            return 0.25

    def _get_tta_enabled(self):
        """是否启用 TTA (Test Time Augmentation)"""
        try:
            config_manager = get_config_manager()
            return config_manager.get("agriculture.pestEnableTTA", True)
        except Exception:
            return True

    def _get_preprocess_enabled(self):
        """是否启用图像预处理增强"""
        try:
            config_manager = get_config_manager()
            return config_manager.get("agriculture.pestEnablePreprocess", True)
        except Exception:
            return True

    def update_from_config(self):
        self.confidence = self._get_default_confidence()
        self.iou = self._get_iou_threshold()
        self.enable_tta = self._get_tta_enabled()
        self.enable_preprocess = self._get_preprocess_enabled()

    def _load_model(self):
        try:
            if os.path.exists(self.model_path):
                print(f"[PestDetector] Loading model: {self.model_path}")
                self.model = YOLO(self.model_path)
                print(f"OK [PestDetector] Model loaded, supports {len(self.model.names)} classes, "
                      f"conf={self.confidence}, iou={self.iou}, tta={self.enable_tta}")
            else:
                print(f"Warning [PestDetector] Model file not found: {self.model_path}")
        except Exception as e:
            print(f"Error [PestDetector] Load model failed: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def enhance_image(img: np.ndarray) -> np.ndarray:
        """
        Image enhancement for agricultural pest detection:
        1. Convert to LAB, apply CLAHE on L channel for contrast
        2. Denoise with fastNlMeansDenoising
        3. Auto white balance
        """
        try:
            # CLAHE on L channel of LAB
            lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b])
            img = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

            # Gentle denoise
            img = cv2.fastNlMeansDenoisingColored(img, None, 3, 3, 7, 21)
            return img
        except Exception:
            return img

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        if self.enable_preprocess:
            img = self.enhance_image(img)

        return img

    def detect(self, image_bytes: bytes) -> List[Dict]:
        if self.model is None:
            return []

        try:
            img = self.preprocess(image_bytes)

            # Core inference: pass both conf AND iou for NMS
            inference_kwargs = {
                "conf": self.confidence,
                "iou": self.iou,
                "verbose": False
            }

            results = self.model(img, **inference_kwargs)
            predictions = self._parse_results(results)

            # TTA: run again with horizontal flip and merge
            if self.enable_tta and len(predictions) == 0:
                img_flipped = cv2.flip(img, 1)
                results_flip = self.model(img_flipped, **inference_kwargs)
                flip_preds = self._parse_results(results_flip)
                # Flip back bbox coordinates
                w = img.shape[1]
                for p in flip_preds:
                    x1, x2 = p['bbox']['x1'], p['bbox']['x2']
                    p['bbox']['x1'] = w - x2
                    p['bbox']['x2'] = w - x1
                predictions = self._merge_predictions(predictions, flip_preds)

            return predictions
        except Exception as e:
            print(f"Error [PestDetector] Detection failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_results(self, results) -> List[Dict]:
        predictions = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls)
                conf = float(box.conf)
                class_name = result.names.get(class_id, f"class_{class_id}")

                predictions.append({
                    'class': class_name,
                    'class_id': class_id,
                    'confidence': round(conf, 4),
                    'bbox': {
                        'x1': int(box.xyxy[0][0]),
                        'y1': int(box.xyxy[0][1]),
                        'x2': int(box.xyxy[0][2]),
                        'y2': int(box.xyxy[0][3])
                    }
                })

        # Sort by confidence descending
        predictions.sort(key=lambda p: p['confidence'], reverse=True)
        return predictions

    def _merge_predictions(
        self,
        preds_a: List[Dict],
        preds_b: List[Dict],
        iou_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Merge predictions from two augmented views (e.g. original + flipped).
        Keeps the higher-confidence box when two boxes of the same class overlap.
        """
        if not preds_a:
            return preds_b
        if not preds_b:
            return preds_a

        def _iou(b1, b2):
            xa = max(b1['x1'], b2['x1'])
            ya = max(b1['y1'], b2['y1'])
            xb = min(b1['x2'], b2['x2'])
            yb = min(b1['y2'], b2['y2'])
            inter = max(0, xb - xa) * max(0, yb - ya)
            area1 = (b1['x2'] - b1['x1']) * (b1['y2'] - b1['y1'])
            area2 = (b2['x2'] - b2['x1']) * (b2['y2'] - b2['y1'])
            return inter / float(area1 + area2 - inter + 1e-6)

        merged = list(preds_a)
        for pb in preds_b:
            duplicate = False
            for i, pa in enumerate(merged):
                if pa['class_id'] == pb['class_id'] and _iou(pa['bbox'], pb['bbox']) > iou_threshold:
                    # Keep higher confidence
                    if pb['confidence'] > pa['confidence']:
                        merged[i] = pb
                    duplicate = True
                    break
            if not duplicate:
                merged.append(pb)

        merged.sort(key=lambda p: p['confidence'], reverse=True)
        return merged
    
    def annotate_image(self, image_bytes: bytes, predictions: List[Dict]) -> str:
        try:
            img = self.preprocess(image_bytes)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # Color map per class (cycle through distinct colors)
            colors = [
                (0, 255, 0),    # green
                (255, 0, 0),    # blue
                (0, 0, 255),    # red
                (255, 255, 0),  # cyan
                (255, 0, 255),  # magenta
                (0, 255, 255),  # yellow
                (128, 0, 128),  # purple
                (128, 128, 0),  # teal
            ]

            for pred in predictions:
                box = pred['bbox']
                x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
                color = colors[pred['class_id'] % len(colors)]

                # Thicker box for better visibility
                cv2.rectangle(img_bgr, (x1, y1), (x2, y2), color, 3)

                # Background rectangle for text
                label = f"{pred['class']} {pred['confidence']:.2f}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(img_bgr, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
                cv2.putText(img_bgr, label, (x1 + 2, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            _, buffer = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            import base64
            base64_image = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"
        except Exception as e:
            print(f"Error [PestDetector] Annotation failed: {e}")
            return ""

    def detect_and_annotate(self, image_bytes: bytes) -> Tuple[List[Dict], str]:
        predictions = self.detect(image_bytes)
        annotated_image = self.annotate_image(image_bytes, predictions)
        return predictions, annotated_image


# 全局单例实例
_detector_instances = {}

def get_pest_detector():
    """获取或创建 PestDetector 单例"""
    if 'default' not in _detector_instances:
        _detector_instances['default'] = PestDetector()
    return _detector_instances['default']

