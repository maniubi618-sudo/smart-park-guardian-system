import base64
import os
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

try:
    import tensorflow as tf
    import tensorflow_hub as hub
except ImportError as e:
    print(f"Warning [CropDiseaseDetector] Import TensorFlow/CropNet dependencies failed: {e}")
    tf = None
    hub = None

try:
    from app.services.config_manager import get_config_manager
except ImportError as e:
    print(f"Warning [CropDiseaseDetector] Import config manager failed: {e}")
    get_config_manager = None


class CropDiseaseDetector:
    """
    Google CropNet cassava disease classifier.

    This service intentionally supports only cassava leaf disease recognition.
    Legacy crop disease YOLO models and pest models have no fallback path here.
    """

    CROP_TYPE = "cassava"
    BACKEND = "google_cropnet_cassava"
    MODEL_SOURCE = "https://tfhub.dev/google/cropnet/classifier/cassava_disease_V1/2"
    MODEL_CACHE_DIR = Path(__file__).resolve().parents[1] / "models" / "crop_disease" / "cropnet_cassava"
    MODEL_DIR = MODEL_CACHE_DIR / "saved_model"

    CLASS_NAMES = ["cbb", "cbsd", "cgm", "cmd", "healthy", "unknown"]
    CLASS_LABELS_CN = {
        "cbb": "木薯细菌性枯萎病",
        "cbsd": "木薯褐条病",
        "cgm": "木薯绿螨",
        "cmd": "木薯花叶病",
        "healthy": "健康",
        "unknown": "未知",
    }
    NON_ALARM_CLASSES = {"healthy", "unknown"}

    def __init__(self, crop_type: str = CROP_TYPE, confidence: float = None):
        self.crop_type = self.normalize_crop(crop_type)
        self.backend = self.BACKEND
        self.model_source = self.MODEL_SOURCE
        self.confidence = confidence if confidence is not None else self._get_default_confidence()
        self.model_path = str(self.MODEL_DIR)
        self.model = None
        self.input_size = 224
        self.class_map = {i: self.CLASS_LABELS_CN[name] for i, name in enumerate(self.CLASS_NAMES)}
        self._load_model()

    @classmethod
    def normalize_crop(cls, crop_type: str) -> str:
        crop = (crop_type or cls.CROP_TYPE).strip().lower()
        if crop in {"cassava", "木薯"}:
            return cls.CROP_TYPE
        return crop

    def _get_default_confidence(self) -> float:
        try:
            if get_config_manager is None:
                return 0.50
            config_manager = get_config_manager()
            return float(config_manager.get("agriculture.cropDiseaseConfidence", 0.50))
        except Exception:
            return 0.50

    def _load_model(self):
        if tf is None or hub is None:
            return

        if self.crop_type != self.CROP_TYPE:
            print(f"Warning [CropDiseaseDetector] Unsupported crop type: {self.crop_type}")
            return

        if not self.MODEL_DIR.exists():
            print(
                "Warning [CropDiseaseDetector] CropNet cassava model cache not found. "
                "Run scripts/download_cropnet_cassava.py first."
            )
            return

        try:
            self.model = hub.KerasLayer(str(self.MODEL_DIR))
            print(f"[CropDiseaseDetector] Google CropNet cassava model loaded: {self.MODEL_DIR}")
        except Exception as e:
            print(f"Error [CropDiseaseDetector] Load CropNet model failed: {e}")
            import traceback
            traceback.print_exc()
            self.model = None

    def update_from_config(self):
        self.confidence = self._get_default_confidence()

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("无法读取图片")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (self.input_size, self.input_size), interpolation=cv2.INTER_AREA)
        img = img.astype(np.float32) / 255.0
        return np.expand_dims(img, axis=0)

    def detect(self, image_bytes: bytes) -> List[Dict]:
        if self.model is None:
            return []

        try:
            input_tensor = self.preprocess(image_bytes)
            probabilities = self.model(input_tensor).numpy()[0]
            class_id = int(np.argmax(probabilities))
            confidence = float(probabilities[class_id])
            class_key = self.CLASS_NAMES[class_id]

            if class_key in self.NON_ALARM_CLASSES or confidence < self.confidence:
                return []

            h, w = self._image_size(image_bytes)
            return [{
                "class": self.CLASS_LABELS_CN[class_key],
                "class_id": class_id,
                "confidence": round(confidence, 4),
                "original_confidence": round(confidence, 4),
                "bbox": {
                    "x1": 0,
                    "y1": 0,
                    "x2": int(w),
                    "y2": int(h),
                }
            }]
        except Exception as e:
            print(f"Error [CropDiseaseDetector] Detection failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def _image_size(image_bytes: bytes) -> Tuple[int, int]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return 0, 0
        return img.shape[:2]

    def annotate_image(self, image_bytes: bytes, predictions: List[Dict]) -> str:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                return ""

            for pred in predictions:
                box = pred["bbox"]
                x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
                color = (0, 0, 255)
                cv2.rectangle(img_bgr, (x1, y1), (x2, y2), color, 3)
                label = f"{pred['class']} {pred['confidence']:.2%}"
                cv2.rectangle(img_bgr, (x1, max(0, y1 - 32)), (min(x2, x1 + 260), y1), color, -1)
                cv2.putText(
                    img_bgr,
                    label,
                    (x1 + 6, max(18, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

            _, buffer = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        except Exception as e:
            print(f"Error [CropDiseaseDetector] Annotation failed: {e}")
            return ""

    def detect_and_annotate(self, image_bytes: bytes) -> Tuple[List[Dict], str]:
        predictions = self.detect(image_bytes)
        annotated_image = self.annotate_image(image_bytes, predictions)
        return predictions, annotated_image

    @classmethod
    def get_available_crops(cls) -> List[str]:
        return [cls.CROP_TYPE]


_detector_instances = {}


def get_crop_disease_detector(crop_type: str = CropDiseaseDetector.CROP_TYPE):
    crop_type = CropDiseaseDetector.normalize_crop(crop_type)
    if crop_type not in _detector_instances:
        _detector_instances[crop_type] = CropDiseaseDetector(crop_type=crop_type)
    return _detector_instances[crop_type]


def update_crop_disease_detectors_from_config():
    for detector in _detector_instances.values():
        detector.update_from_config()
