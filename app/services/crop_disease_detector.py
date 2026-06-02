
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional

try:
    from ultralytics import YOLO
except ImportError as e:
    print(f"Warning [CropDiseaseDetector] Import YOLO failed: {e}")
    pass

try:
    from app.services.config_manager import get_config_manager
except ImportError as e:
    print(f"Warning [CropDiseaseDetector] Import config manager failed: {e}")
    pass


class CropDiseaseDetector:
    """
    Crop Disease Detection Service
    Optimized YOLO-based crop disease detection with:
    - Per-crop IoU NMS thresholds
    - CLAHE image preprocessing for agricultural images
    - TTA (Test Time Augmentation) for hard cases
    - Per-crop confidence calibration
    Supports 9 crop types for disease detection.
    """

    # Crop type to model file mapping
    CROP_MODELS = {
        "apple": "apple_best.pt",
        "corn": "corn_best.pt",
        "cotton": "cotton_best.pt",
        "grape": "grape_best.pt",
        "potato": "potato_best.pt",
        "rice": "rice_best.pt",
        "strawberry": "strawberry_best.pt",
        "tomato": "tomato_best.pt",
        "wheat": "wheat_best.pt"
    }

    # Lower defaults for the crops used most in this project. The upload/API
    # path still allows config overrides, but these avoid missing weak early
    # symptoms when no crop-specific config has been set.
    DEFAULT_CONFIDENCE_BY_CROP = {
        "tomato": 0.45,
        "apple": 0.20,
        "rice": 0.05,
    }

    DEFAULT_IOU_BY_CROP = {
        "tomato": 0.55,
        "apple": 0.50,
        "rice": 0.55,
    }

    DEFAULT_MIN_CROP_CONTENT_RATIO_BY_CROP = {
        "tomato": 0.30,
        "rice": 0.12,
    }

    HEALTHY_LABELS = {"健康", "Healthy", "healthy"}

    # Disease labels for each crop (English)
    DISEASE_LABELS = {
        "corn": ["Blight", "Gray_Spot", "Rust",
                  "FAW_Lv", "Streak",
                  "Stem_Borer", "StemBorer_Lv"],

        "rice": ["Bact_L_Blight", "Brn_Spot", "Healthy",
                  "Leaf_Blast", "Scald", "Narrow_Br_Spot",
                  "Neck_Blast", "Hispa"],

        "wheat": ["Bacterial_Streak", "Head_Scab",
                  "Leaf_Rust", "Loose_Smut",
                  "Powdery_Mildew", "Septoria_Blotch",
                  "Stem_Rust", "Stripe_Rust"],

        "potato": ["Early_Blight", "Healthy", "Late_Blight"],

        "tomato": ["Early_Blight", "Healthy", "Late_Blight",
                    "Leaf_Miner", "Leaf_Mold", "Mosaic_V",
                    "Septoria", "Spider_M", "YLCV"],

        "cotton": ["Blight", "Curl", "Healthy", "Wilt", "Wilt"],

        "apple": ["RootRot", "Scab", "CedarRust", "Healthy"],

        "grape": ["Black_Rot", "Downey_Mildew", "Esca",
                   "Healthy", "Leaf_Blight"],

        "strawberry": ["Angular_LS", "Anthracnose_FR", "Blossom_BT",
                        "Gray_Mold", "Leaf_Spot", "Powdery_Fruit",
                        "Powdery_Leaf"]
    }

    # Chinese disease labels for each crop（严格对齐模型 class_id 顺序）
    DISEASE_LABELS_CN = {
        "corn": ["枯萎病", "灰斑病", "锈病",
                  "草地贪夜蛾", "条纹病",
                  "茎蛀虫", "茎蛀虫幼虫"],

        "rice": ["细菌性叶枯病", "褐斑病", "健康",
                  "叶瘟病", "纹枯病", "窄褐斑病",
                  "穗颈瘟", "稻铁甲虫"],

        "wheat": ["细菌性条斑病", "赤霉病",
                  "叶锈病", "散黑穗病",
                  "白粉病", "壳针孢叶斑病",
                  "秆锈病", "条锈病"],

        "potato": ["早疫病", "健康", "晚疫病"],

        "tomato": ["早疫病", "健康", "晚疫病",
                    "潜叶蝇", "叶霉病", "花叶病毒",
                    "壳针孢病", "红蜘蛛", "黄化曲叶病毒"],

        "cotton": ["枯萎病", "卷叶病", "健康", "萎蔫病", "萎蔫病"],

        "apple": ["根腐病", "黑星病", "苹果锈病", "健康"],

        "grape": ["黑腐病", "霜霉病", "木材腐烂病",
                   "健康", "叶枯病"],

        "strawberry": ["角斑病", "炭疽病", "花枯病",
                        "灰霉病", "叶斑病", "果实白粉病",
                        "叶片白粉病"]
    }

    def __init__(self, crop_type: str = "rice", confidence: float = None):
        self.crop_type = crop_type.lower()
        self.confidence = confidence if confidence is not None else self._get_default_confidence()
        self.iou = self._get_iou_threshold()
        self.enable_tta = self._get_tta_enabled()
        self.enable_preprocess = self._get_preprocess_enabled()
        self.require_crop_content = self._get_require_crop_content()
        self.min_crop_content_ratio = self._get_min_crop_content_ratio()
        self.min_green_ratio = self._get_min_green_ratio()
        self.min_box_area_ratio = self._get_min_box_area_ratio()
        self.healthy_suppression_margin = self._get_healthy_suppression_margin()
        self.model = None
        self.model_path = None
        self._load_model()

    def _get_default_confidence(self):
        """从配置获取默认置信度阈值"""
        try:
            config_manager = get_config_manager()
            per_crop = config_manager.get("agriculture.cropDiseaseConfidenceByCrop", {})
            if isinstance(per_crop, dict) and self.crop_type in per_crop:
                return float(per_crop[self.crop_type])
            default_value = self.DEFAULT_CONFIDENCE_BY_CROP.get(self.crop_type, 0.25)
            return float(config_manager.get("agriculture.cropDiseaseConfidence", default_value))
        except Exception:
            return self.DEFAULT_CONFIDENCE_BY_CROP.get(self.crop_type, 0.25)

    def _get_iou_threshold(self):
        """IoU NMS 阈值 - 农业场景建议 0.3-0.5"""
        try:
            config_manager = get_config_manager()
            per_crop = config_manager.get("agriculture.cropDiseaseIouByCrop", {})
            if isinstance(per_crop, dict) and self.crop_type in per_crop:
                return float(per_crop[self.crop_type])
            default_value = self.DEFAULT_IOU_BY_CROP.get(self.crop_type, 0.5)
            return float(config_manager.get("agriculture.cropDiseaseIouThreshold", default_value))
        except Exception:
            return self.DEFAULT_IOU_BY_CROP.get(self.crop_type, 0.5)

    def _get_tta_enabled(self):
        try:
            config_manager = get_config_manager()
            return config_manager.get("agriculture.cropDiseaseEnableTTA", True)
        except Exception:
            return True

    def _get_preprocess_enabled(self):
        try:
            config_manager = get_config_manager()
            return config_manager.get("agriculture.cropDiseaseEnablePreprocess", False)
        except Exception:
            return False

    def _get_require_crop_content(self):
        try:
            config_manager = get_config_manager()
            return bool(config_manager.get("agriculture.cropDiseaseRequireCropContent", True))
        except Exception:
            return True

    def _get_min_crop_content_ratio(self):
        try:
            config_manager = get_config_manager()
            per_crop = config_manager.get("agriculture.cropDiseaseMinCropContentRatioByCrop", {})
            if isinstance(per_crop, dict) and self.crop_type in per_crop:
                return float(per_crop[self.crop_type])
            return float(config_manager.get("agriculture.cropDiseaseMinCropContentRatio", 0.015))
        except Exception:
            return self.DEFAULT_MIN_CROP_CONTENT_RATIO_BY_CROP.get(self.crop_type, 0.015)

    def _get_min_green_ratio(self):
        try:
            config_manager = get_config_manager()
            per_crop = config_manager.get("agriculture.cropDiseaseMinGreenRatioByCrop", {})
            if isinstance(per_crop, dict) and self.crop_type in per_crop:
                return float(per_crop[self.crop_type])
            return 0.0
        except Exception:
            return 0.0

    def _get_min_box_area_ratio(self):
        try:
            config_manager = get_config_manager()
            return float(config_manager.get("agriculture.cropDiseaseMinBoxAreaRatio", 0.003))
        except Exception:
            return 0.003

    def _get_healthy_suppression_margin(self):
        try:
            config_manager = get_config_manager()
            return float(config_manager.get("agriculture.cropDiseaseHealthySuppressionMargin", 0.0))
        except Exception:
            return 0.0

    def _load_model(self):
        try:
            models_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'models'
            )

            if self.crop_type not in self.CROP_MODELS:
                print(f"Warning: Unsupported crop type: {self.crop_type}, using rice instead")
                self.crop_type = "rice"

            model_file = self.CROP_MODELS[self.crop_type]
            self.model_path = os.path.join(models_dir, model_file)

            if os.path.exists(self.model_path):
                print(f"[CropDiseaseDetector] Loading model: {model_file} (crop: {self.crop_type})")
                self.model = YOLO(self.model_path)
                print(f"Model loaded, supports {len(self.model.names)} classes, "
                      f"conf={self.confidence}, iou={self.iou}, tta={self.enable_tta}")
            else:
                print(f"Warning [CropDiseaseDetector] Model file not found: {self.model_path}")
        except Exception as e:
            print(f"Error [CropDiseaseDetector] Load model failed: {e}")
            import traceback
            traceback.print_exc()

    def switch_crop(self, crop_type: str):
        self.crop_type = crop_type.lower()
        self.update_from_config()
        self._load_model()

    def update_from_config(self):
        self.confidence = self._get_default_confidence()
        self.iou = self._get_iou_threshold()
        self.enable_tta = self._get_tta_enabled()
        self.enable_preprocess = self._get_preprocess_enabled()
        self.require_crop_content = self._get_require_crop_content()
        self.min_crop_content_ratio = self._get_min_crop_content_ratio()
        self.min_green_ratio = self._get_min_green_ratio()
        self.min_box_area_ratio = self._get_min_box_area_ratio()
        self.healthy_suppression_margin = self._get_healthy_suppression_margin()

    @staticmethod
    def map_confidence(original_conf: float) -> float:
        """Return the real YOLO confidence instead of inflating low scores."""
        original_conf = max(0.0, min(1.0, float(original_conf)))
        return original_conf

    @staticmethod
    def enhance_image(img: np.ndarray) -> np.ndarray:
        """
        Agricultural image enhancement:
        1. CLAHE on LAB L channel for leaf texture & disease spots contrast
        2. Gentle denoising that preserves disease spot edges
        """
        try:
            lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)

            # CLAHE - brings out subtle disease patterns on leaves
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)

            # Enhance green-magenta channel to highlight diseased areas
            clahe2 = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            a = clahe2.apply(a)

            lab = cv2.merge([l, a, b])
            img = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

            # Bilateral filter: denoise while preserving edges (disease spots)
            img = cv2.bilateralFilter(img, 5, 50, 50)
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

    def _has_enough_crop_content(self, img: np.ndarray) -> bool:
        """Reject black/blank/non-crop frames before YOLO can hallucinate labels."""
        if img is None or img.size == 0:
            return False

        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        mean_light = float(np.mean(gray))
        contrast = float(np.std(gray))
        if mean_light < 12 or mean_light > 245 or contrast < 6:
            return False

        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)

        green_mask = (h >= 25) & (h <= 95) & (s >= 35) & (v >= 35)
        yellow_brown_mask = (h >= 8) & (h < 25) & (s >= 35) & (v >= 45)
        red_mask = ((h <= 8) | (h >= 165)) & (s >= 35) & (v >= 45)
        green_ratio = float(np.count_nonzero(green_mask)) / float(img.shape[0] * img.shape[1])
        if green_ratio < self.min_green_ratio:
            return False

        crop_like_ratio = float(np.count_nonzero(green_mask | yellow_brown_mask | red_mask)) / float(img.shape[0] * img.shape[1])
        if crop_like_ratio < self.min_crop_content_ratio:
            return False

        return True

    def _filter_predictions(self, img: np.ndarray, predictions: List[Dict]) -> List[Dict]:
        if not predictions:
            return []

        image_area = max(1, img.shape[0] * img.shape[1])
        filtered = []
        for pred in predictions:
            box = pred.get("bbox", {})
            area = max(0, box.get("x2", 0) - box.get("x1", 0)) * max(0, box.get("y2", 0) - box.get("y1", 0))
            if area / image_area < self.min_box_area_ratio:
                continue
            filtered.append(pred)

        healthy_conf = max(
            (p["original_confidence"] for p in filtered if p["class"] in self.HEALTHY_LABELS),
            default=0.0
        )
        if healthy_conf > 0:
            filtered = [
                p for p in filtered
                if p["class"] in self.HEALTHY_LABELS
                or p["original_confidence"] > healthy_conf + self.healthy_suppression_margin
            ]

        filtered.sort(key=lambda p: p["confidence"], reverse=True)
        return filtered

    def detect(self, image_bytes: bytes) -> List[Dict]:
        if self.model is None:
            return []

        try:
            img = self.preprocess(image_bytes)
            if self.require_crop_content and not self._has_enough_crop_content(img):
                return []

            inference_kwargs = {
                "conf": self.confidence,
                "iou": self.iou,
                "imgsz": 640,
                "verbose": False
            }

            model_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            results = self.model(model_img, **inference_kwargs)
            predictions = self._parse_results(results)

            # TTA: horizontal flip for hard cases (no detection or low conf)
            if self.enable_tta and (len(predictions) == 0 or
                                     all(p['original_confidence'] < 0.45 for p in predictions)):
                img_flipped = cv2.flip(img, 1)
                model_img_flipped = cv2.cvtColor(img_flipped, cv2.COLOR_RGB2BGR)
                results_flip = self.model(model_img_flipped, **inference_kwargs)
                flip_preds = self._parse_results(results_flip)

                w = img.shape[1]
                for p in flip_preds:
                    x1, x2 = p['bbox']['x1'], p['bbox']['x2']
                    p['bbox']['x1'] = w - x2
                    p['bbox']['x2'] = w - x1

                predictions = self._merge_predictions(predictions, flip_preds)

            return self._filter_predictions(img, predictions)
        except Exception as e:
            print(f"Error [CropDiseaseDetector] Detection failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_results(self, results) -> List[Dict]:
        predictions = []
        labels = self.DISEASE_LABELS.get(self.crop_type, [])
        labels_cn = self.DISEASE_LABELS_CN.get(self.crop_type, [])

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls)
                original_conf = float(box.conf)

                if class_id in result.names:
                    raw_name = str(result.names[class_id])
                    if '(' in raw_name and raw_name.endswith(')'):
                        class_name = raw_name[raw_name.index('(') + 1:-1]
                    else:
                        class_name = raw_name
                elif class_id < len(labels_cn):
                    class_name = labels_cn[class_id]
                elif class_id < len(labels):
                    class_name = labels[class_id]
                else:
                    class_name = f"Disease_{class_id}"

                mapped_conf = self.map_confidence(original_conf)

                predictions.append({
                    'class': class_name,
                    'class_id': class_id,
                    'confidence': round(mapped_conf, 4),
                    'original_confidence': round(original_conf, 4),
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
        """Merge TTA results, keeping higher-confidence boxes on overlap."""
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

            # Distinct colors per class for disease differentiation
            colors = [
                (0, 255, 0),    # green
                (255, 0, 0),    # blue
                (0, 0, 255),    # red
                (255, 255, 0),  # cyan
                (255, 0, 255),  # magenta
                (0, 255, 255),  # yellow
                (128, 0, 128),  # purple
                (128, 128, 0),  # teal
                (0, 128, 128),  # olive
                (128, 0, 0),    # maroon
            ]

            # Try PIL for Chinese text, fallback to OpenCV
            try:
                from PIL import Image, ImageDraw, ImageFont

                img_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(img_pil)

                font = None
                font_size = 18
                try:
                    font_paths = [
                        "C:/Windows/Fonts/msyh.ttc",
                        "C:/Windows/Fonts/simhei.ttf",
                        "C:/Windows/Fonts/simsun.ttc",
                        "/System/Library/Fonts/PingFang.ttc",
                        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                    ]
                    for font_path in font_paths:
                        if os.path.exists(font_path):
                            font = ImageFont.truetype(font_path, font_size)
                            break
                except Exception:
                    pass

                if font is None:
                    font = ImageFont.load_default()

                for pred in predictions:
                    box = pred['bbox']
                    x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
                    class_id = pred.get('class_id', 0)
                    color = colors[class_id % len(colors)]

                    draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=3)

                    label = f"{pred['class']} {pred['confidence']:.2%}"
                    text_bbox = draw.textbbox((x1, y1 - 28), label, font=font)
                    draw.rectangle(text_bbox, fill=color)
                    draw.text((x1, y1 - 28), label, fill=(255, 255, 255), font=font)

                img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

            except ImportError:
                for pred in predictions:
                    box = pred['bbox']
                    x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
                    class_id = pred.get('class_id', 0)
                    color = colors[class_id % len(colors)]

                    cv2.rectangle(img_bgr, (x1, y1), (x2, y2), color, 3)

                    label = f"{pred['class']} {pred['confidence']:.2%}"
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(img_bgr, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
                    cv2.putText(img_bgr, label, (x1 + 2, y1 - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            _, buffer = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            import base64
            base64_image = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"
        except Exception as e:
            print(f"Error [CropDiseaseDetector] Annotation failed: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def detect_and_annotate(self, image_bytes: bytes) -> Tuple[List[Dict], str]:
        predictions = self.detect(image_bytes)
        annotated_image = self.annotate_image(image_bytes, predictions)
        return predictions, annotated_image

    @classmethod
    def get_available_crops(cls) -> List[str]:
        return list(cls.CROP_MODELS.keys())


_detector_instances = {}

def get_crop_disease_detector(crop_type: str = "rice"):
    """获取或创建对应作物的检测器实例"""
    if crop_type not in _detector_instances:
        _detector_instances[crop_type] = CropDiseaseDetector(crop_type=crop_type)
    elif _detector_instances[crop_type].crop_type != crop_type:
        _detector_instances[crop_type].switch_crop(crop_type)
    return _detector_instances[crop_type]


def update_crop_disease_detectors_from_config():
    """Refresh cached crop disease detector thresholds after config changes."""
    for detector in _detector_instances.values():
        detector.update_from_config()
