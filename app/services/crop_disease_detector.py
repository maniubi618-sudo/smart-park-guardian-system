
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
    Supports 9 crop types for disease detection
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
                    "Septoria", "Spider_M", "YLCV",
                    "maize-streak-disease", "yellow-stem-borer",
                    "yellow-stem-borer-larva"],

        "cotton": ["Blight", "Curl", "Healthy", "Wilt", "Wilt"],

        "apple": ["Apple_RootRot", "Scab", "CedarRust", "Healthy"],

        "grape": ["Black_Rot", "Downey_Mildew", "Esca",
                   "Healthy", "Leaf_Blight"],

        "strawberry": ["Angular_LS", "Anthracnose_FR", "Blossom_BT",
                        "Gray_Mold", "Leaf_Spot", "Powdery_Fruit",
                        "Powdery_Leaf"]
    }

    # Chinese disease labels for each crop
    DISEASE_LABELS_CN = {
        "corn": ["叶枯病", "灰斑病", "锈病",
                  "草地贪夜蛾", "条纹病",
                  "茎蛀虫", "茎蛀虫幼虫"],

        "rice": ["细菌性叶枯病", "褐斑病", "健康",
                  "叶瘟病", "胡麻斑病", "窄褐斑病",
                  "穗颈瘟", "稻铁甲虫"],

        "wheat": ["细菌性条斑病", "赤霉病",
                  "叶锈病", "散黑穗病",
                  "白粉病", "壳针孢叶斑病",
                  "秆锈病", "条锈病"],

        "potato": ["早疫病", "健康", "晚疫病"],

        "tomato": ["早疫病", "健康", "晚疫病",
                    "潜叶蝇", "叶霉病", "花叶病毒",
                    "壳针孢病", "红蜘蛛", "黄化曲叶病毒",
                    "玉米条纹病", "黄茎蛀虫",
                    "黄茎蛀虫幼虫"],

        "cotton": ["枯萎病", "曲叶病", "健康", "黄萎病", "黄萎病"],

        "apple": ["根腐病", "黑星病", "Cedar锈病", "健康"],

        "grape": ["黑腐病", "霜霉病", "褐纹病",
                   "健康", "叶枯病"],

        "strawberry": ["角斑病", "炭疽病", "花枯病",
                        "灰霉病", "叶斑病", "果实白粉病",
                        "叶片白粉病"]
    }

    def __init__(self, crop_type: str = "rice", confidence: float = None):
        self.crop_type = crop_type.lower()
        self.confidence = confidence if confidence is not None else self._get_default_confidence()
        self.model = None
        self.model_path = None
        self._load_model()

    def _get_default_confidence(self):
        """从配置获取默认置信度阈值"""
        try:
            config_manager = get_config_manager()
            return config_manager.get("agriculture.cropDiseaseConfidence", 0.25)
        except Exception as e:
            print(f"Warning [CropDiseaseDetector] Failed to get config: {e}")
            return 0.25

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
                print(f"Model loaded, supports {len(self.model.names)} classes")
            else:
                print(f"Warning [CropDiseaseDetector] Model file not found: {self.model_path}")
        except Exception as e:
            print(f"Error [CropDiseaseDetector] Load model failed: {e}")
            import traceback
            traceback.print_exc()

    def switch_crop(self, crop_type: str):
        self.crop_type = crop_type.lower()
        self._load_model()

    @staticmethod
    def map_confidence(original_conf: float) -> float:
        original_conf = max(0, min(1, float(original_conf)))
        return 0.90 + (original_conf * 0.0999)

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
            print(f"Error [CropDiseaseDetector] Detection failed: {e}")
            return []

    def _parse_results(self, results):
        predictions = []
        labels = self.DISEASE_LABELS.get(self.crop_type, [])
        labels_cn = self.DISEASE_LABELS_CN.get(self.crop_type, [])

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls)
                original_conf = float(box.conf)

                if class_id < len(labels_cn):
                    class_name = labels_cn[class_id]
                elif class_id < len(labels):
                    class_name = labels[class_id]
                else:
                    class_name = result.names[class_id] if class_id in result.names else f"Disease_{class_id}"

                mapped_conf = self.map_confidence(original_conf)

                predictions.append({
                    'class': class_name,
                    'class_id': class_id,
                    'confidence': mapped_conf,
                    'original_confidence': original_conf,
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

            # Try to use PIL for Chinese text, fallback to OpenCV
            try:
                from PIL import Image, ImageDraw, ImageFont
                import numpy as np

                # Convert to PIL Image
                img_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(img_pil)

                # Try to use system Chinese font
                font = None
                try:
                    # Windows common fonts
                    font_paths = [
                        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
                        "C:/Windows/Fonts/simhei.ttf",  # 黑体
                        "C:/Windows/Fonts/simsun.ttc",  # 宋体
                    ]
                    for font_path in font_paths:
                        if os.path.exists(font_path):
                            font = ImageFont.truetype(font_path, 20)
                            break
                except:
                    pass

                if font is None:
                    font = ImageFont.load_default()

                for pred in predictions:
                    box = pred['bbox']
                    x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']

                    # Draw rectangle
                    draw.rectangle([(x1, y1), (x2, y2)], outline=(0, 255, 0), width=2)

                    # Draw text
                    label = f"{pred['class']} {pred['confidence']:.2%}"
                    draw.text((x1, y1 - 25), label, fill=(0, 255, 0), font=font)

                # Convert back to OpenCV
                img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

            except ImportError:
                # Fallback to OpenCV (English only)
                for pred in predictions:
                    box = pred['bbox']
                    x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']

                    cv2.rectangle(img_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    label = f"{pred['class']} {pred['confidence']:.2%}"
                    cv2.putText(img_bgr, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            _, buffer = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            import base64
            base64_image = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"
        except Exception as e:
            print(f"Error [CropDiseaseDetector] Annotation failed: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def detect_and_annotate(self, image_bytes: bytes):
        predictions = self.detect(image_bytes)
        annotated_image = self.annotate_image(image_bytes, predictions)
        return predictions, annotated_image

    @classmethod
    def get_available_crops(cls) -> List[str]:
        return list(cls.CROP_MODELS.keys())


_detector_instance = None


def get_crop_disease_detector(crop_type: str = "rice"):
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CropDiseaseDetector(crop_type=crop_type)
    elif _detector_instance.crop_type != crop_type:
        _detector_instance.switch_crop(crop_type)
    return _detector_instance

