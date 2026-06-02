
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import base64

from app.services.crop_disease_detector import get_crop_disease_detector, CropDiseaseDetector

router = APIRouter(prefix="/crop-disease-detection", tags=["农作物病害检测"])

HEALTHY_LABELS = {"健康", "Healthy", "healthy"}


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
    crop_type: str = Query("rice", description="作物类型: apple, corn, cotton, grape, potato, rice, strawberry, tomato, wheat"),
    record_alarm: bool = Query(False, description="是否将本次病害检测结果写入大屏告警")
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

        # 从配置读取最新阈值。这里使用检测器的作物级配置，避免前端把阈值调低后
        # 仍被固定 0.25 二次过滤导致漏检。
        try:
            detector.update_from_config()
        except Exception as e:
            print(f"Warning: Failed to refresh crop disease config, using current values: {e}")

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

        # 只保留高置信度病害结果。低置信度和“健康”类别都不返回给前端，避免手机画面误报。
        disease_preds = [
            p for p in predictions
            if p["class"] not in HEALTHY_LABELS and p["original_confidence"] >= detector.confidence
        ]
        annotated_image = detector.annotate_image(image_bytes, disease_preds)

        # 格式化结果
        results = [
            DetectionResult(
                class_name=pred["class"],
                class_id=pred["class_id"],
                confidence=pred["confidence"],
                original_confidence=pred["original_confidence"],
                bbox=pred["bbox"]
            )
            for pred in disease_preds
        ]

        has_disease = len(disease_preds) > 0

        if has_disease:
            # 统计病害数量
            disease_count = len(disease_preds)
            message = f"检测到 {disease_count} 个病害目标"

            if record_alarm:
                # ★ 创建告警记录，使智慧大棚前端能展示
                try:
                    from app.crud.alarm_crud import create_alarm
                    from app.utils.oss_utils import get_now
                    from app.config.database import SessionLocal
                    from app.services.alarm_broadcast_service import sync_broadcast_alarm
                    from app.utils.logger import get_logger
                    _log = get_logger()

                    db = SessionLocal()
                    try:
                        # 保存标注图作为截图
                        snapshot_url = ""
                        if annotated_image:
                            import base64, os
                            snapshot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'snapshots')
                            os.makedirs(snapshot_dir, exist_ok=True)
                            # 从检测结果收集病害名称和置信度，写入文件名以便前端解析
                            # 格式: 0_20260530_175958_apple_叶斑病_0.97_灰霉病_0.85_crop.jpg
                            disease_parts = []
                            for p in disease_preds:
                                disease_parts.append(p["class"])
                                disease_parts.append(f'{p["confidence"]:.2f}')
                            disease_tag = "_".join(disease_parts[:6])  # 最多3个病害（名+置信度=6段）
                            snapshot_path = os.path.join(snapshot_dir, f'0_{get_now().strftime("%Y%m%d_%H%M%S")}_{disease_tag}_crop.jpg')
                            img_data = base64.b64decode(annotated_image.split(',')[1] if ',' in annotated_image else annotated_image)
                            with open(snapshot_path, 'wb') as f:
                                f.write(img_data)
                            snapshot_url = snapshot_path
                            _log.info(f"[CropDisease] 标注图已保存: {snapshot_path}")

                        _log.info(f"[CropDisease] 创建告警: camera_id=0, type=3...")
                        alarm = create_alarm(db, 0, 3, 0, get_now(), snapshot_url)
                        _log.info(f"[CropDisease] 告警创建成功: ID={alarm.alarm_id}")
                        sync_broadcast_alarm(alarm)
                        _log.info(f"[CropDisease] 告警已广播")
                    finally:
                        db.close()
                except Exception as e:
                    import traceback
                    print(f"创建病虫告警失败: {e}\n{traceback.format_exc()}")
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
        try:
            detector.update_from_config()
        except Exception as e:
            print(f"Warning: Failed to get config, using current detector confidence: {e}")
        return {
            "crop_type": detector.crop_type,
            "model_loaded": detector.model is not None,
            "model_path": detector.model_path,
            "confidence_threshold": detector.confidence,
            "iou_threshold": detector.iou,
            "tta_enabled": detector.enable_tta,
            "preprocess_enabled": detector.enable_preprocess,
            "classes": detector.model.names if detector.model is not None else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
