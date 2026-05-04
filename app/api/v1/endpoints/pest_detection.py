
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import base64

from app.services.pest_detector import get_pest_detector

router = APIRouter(prefix="/pest-detection", tags=["害虫检测"])


class DetectionResult(BaseModel):
    class_name: str
    confidence: float
    bbox: Dict[str, int]


class DetectionResponse(BaseModel):
    success: bool
    predictions: List[DetectionResult]
    annotated_image: Optional[str] = None
    message: str = ""


@router.post("/detect", response_model=DetectionResponse)
async def detect_pests(file: UploadFile = File(...)):
    """
    上传图片进行害虫检测
    """
    try:
        detector = get_pest_detector()
        
        if detector.model is None:
            return DetectionResponse(
                success=False,
                predictions=[],
                message="模型未加载，请确保 pest_detector.pt 文件存在"
            )
        
        image_bytes = await file.read()
        predictions, annotated_image = detector.detect_and_annotate(image_bytes)
        
        results = [
            DetectionResult(
                class_name=pred["class"],
                confidence=pred["confidence"],
                bbox=pred["bbox"]
            )
            for pred in predictions
        ]
        
        return DetectionResponse(
            success=True,
            predictions=results,
            annotated_image=annotated_image,
            message=f"检测到 {len(predictions)} 个目标"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.get("/status")
async def get_status():
    """
    获取检测器状态
    """
    detector = get_pest_detector()
    return {
        "model_loaded": detector.model is not None,
        "model_path": detector.model_path
    }

