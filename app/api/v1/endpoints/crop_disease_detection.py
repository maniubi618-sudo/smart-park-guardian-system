
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import base64

from app.services.crop_disease_detector import get_crop_disease_detector, CropDiseaseDetector
from app.services.config_manager import get_config_manager

router = APIRouter(prefix="/crop-disease-detection", tags=["农作物病害检测"])


class DetectionResult(BaseModel):
    class_name: str
    class_id: int
    confidence: float
    original_confidence: float
    bbox: Dict[str, int]


class DetectionResponse(BaseModel):
    success: bool
    crop_type: str
    predictions: List[DetectionResult]
    annotated_image: Optional[str] = None
    message: str = ""


class CropListResponse(BaseModel):
    success: bool
    crops: List[str]
    message: str = ""


@router.get("/crops", response_model=CropListResponse)
async def get_available_crops():
    """
    获取支持的作物列表
    """
    try:
        crops = CropDiseaseDetector.get_available_crops()
        return CropListResponse(
            success=True,
            crops=crops,
            message=f"共支持 {len(crops)} 种作物"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.post("/detect", response_model=DetectionResponse)
async def detect_disease(
    file: UploadFile = File(...),
    crop_type: str = Query("rice", description="作物类型: apple, corn, cotton, grape, potato, rice, strawberry, tomato, wheat")
):
    """
    上传图片进行病害检测
    """
    try:
        # 验证作物类型
        available_crops = CropDiseaseDetector.get_available_crops()
        if crop_type not in available_crops:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的作物类型: {crop_type}。可选: {', '.join(available_crops)}"
            )

        # 获取检测器
        detector = get_crop_disease_detector(crop_type=crop_type)

        # 从配置读取最新的置信度阈值
        try:
            config_manager = get_config_manager()
            detector.confidence = config_manager.get("agriculture.cropDiseaseConfidence", 0.25)
        except Exception as e:
            print(f"Warning: Failed to get config, using default: {e}")

        if detector.model is None:
            return DetectionResponse(
                success=False,
                crop_type=crop_type,
                predictions=[],
                message="模型未加载，请检查模型文件"
            )

        # 读取图片
        image_bytes = await file.read()

        # 执行检测
        predictions, annotated_image = detector.detect_and_annotate(image_bytes)

        # 格式化结果
        results = [
            DetectionResult(
                class_name=pred["class"],
                class_id=pred["class_id"],
                confidence=pred["confidence"],
                original_confidence=pred["original_confidence"],
                bbox=pred["bbox"]
            )
            for pred in predictions
        ]

        # 判断是否有病害
        has_disease = any(pred["class"] != "健康" for pred in predictions)
        
        if has_disease:
            # 统计病害数量
            disease_count = sum(1 for pred in predictions if pred["class"] != "健康")
            message = f"检测到 {disease_count} 个病害目标"
        else:
            message = "正常"
        
        return DetectionResponse(
            success=True,
            crop_type=crop_type,
            predictions=results,
            annotated_image=annotated_image,
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.get("/status")
async def get_status(crop_type: str = Query("rice", description="作物类型")):
    """
    获取检测器状态
    """
    try:
        detector = get_crop_disease_detector(crop_type=crop_type)
        return {
            "crop_type": detector.crop_type,
            "model_loaded": detector.model is not None,
            "model_path": detector.model_path,
            "confidence_threshold": detector.confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

