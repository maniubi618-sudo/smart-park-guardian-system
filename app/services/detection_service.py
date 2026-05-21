from pathlib import Path
from ultralytics import YOLO
from app.utils.logger import get_logger
from app.services.pest_detector import PestDetector
from app.services.citrus_detector import CitrusDetector
from app.services.tomato_detector import TomatoDetector
from app.services.apple_detector import AppleRipenessDetector
from app.services.config_manager import get_config_manager

logger = get_logger()
# 模型推理服务
class DetectionService:
    # 使用Path获取项目根目录
    project_root = Path(__file__).parent.parent.parent

    descs = [
        "安全规范(未戴安全帽、未穿反光衣)", 
        "区域入侵(人)", 
        "火警(火焰、烟雾)",
        "害虫检测",
        "作物长势异常",
        "果实成熟度"
    ]

    # 告警类型描述+编码，对应AlarmDB中alarm_type字段
    desc_and_code = {
        "安全规范": 0, 
        "区域入侵": 1, 
        "火警": 2,
        "害虫检测": 3,
        "作物长势异常": 4,
        "果实成熟度": 5
    }

    # 加载训练模型（认为该模型能够检测出所有场景中的所有类别的目标）
    model=YOLO(project_root / 'app' / 'models' / 'yolo11s.pt')

    # 人体类别ID
    person_class_id = 0
    # 车辆类别ID
    vehicle_class_id = 1
    # 安全帽类别ID
    helmet_class_id = -1
    # 反光背心
    reflective_vest_class_id = -2
    # 火焰
    fire_class_id = -3
    # 烟雾
    smoke_class_id = -4

    # 置信度阈值
    confidence_threshold = 0.5

    # 构建各个模型文件的路径
    helmet_model_path = project_root / 'app' / 'models' / 'helmet_model.pt'
    vest_model_path = project_root / 'app' / 'models' / 'vest_model.pt'
    person_vehicle_model_path = project_root / 'app' / 'models' / 'yolo11s.pt'
    fire_smoke_model_path = project_root / 'app' / 'models' / 'fire_smoke_seg_model.pt'
    # 害虫检测模型路径
    pest_detector_model_path = project_root / 'app' / 'models' / 'pest_detector.pt'
    crop_growth_model_path = project_root / 'app' / 'models' / 'crop_growth.pt'
    crop_fruit_model_path = project_root / 'app' / 'models' / 'crop_fruit.pt'

    helmet_model = YOLO(helmet_model_path)  # 安全帽检测模型
    vest_model = YOLO(vest_model_path)  # 反光衣检测模型
    person_vehicle_model = YOLO(person_vehicle_model_path)  # 人体车辆检测模型，这里直接使用COCO数据集上预训练的yolo11s模型即可
    fire_smoke_model = YOLO(fire_smoke_model_path)  # 火焰烟雾检测模型
    
    # 害虫检测器（使用专用类）
    pest_detector = None
    citrus_detector = None
    tomato_detector = None
    apple_detector = None

    # 作物检测模型
    crop_growth_model = None
    crop_fruit_model = None

    # 柑橘检测模型路径
    citrus_model_path = project_root / 'app' / 'models' / 'citrus_maturity.pt'
    # 番茄检测模型路径
    tomato_model_path = project_root / 'app' / 'models' / 'tomato_maturity.pt'
    # 苹果检测模型路径
    apple_model_path = project_root / 'app' / 'models' / 'apple.pt'
    
    # 初始化害虫检测器
    try:
        if pest_detector_model_path.exists():
            pest_detector = PestDetector(str(pest_detector_model_path))
            logger.info("[OK] 害虫检测器加载成功")
        else:
            logger.warning("[WARN] 害虫检测模型文件不存在，请运行 copy_model.py")
    except Exception as e:
        logger.warning(f"[ERROR] 加载害虫检测器失败: {e}")

    # 初始化柑橘检测器
    try:
        if citrus_model_path.exists():
            citrus_detector = CitrusDetector(str(citrus_model_path))
            logger.info("[OK] 柑橘成熟度检测器加载成功")
        else:
            logger.warning("[WARN] 柑橘检测模型文件不存在，请运行 quick_copy.py")
    except Exception as e:
        logger.warning(f"[ERROR] 加载柑橘检测器失败: {e}")

    # 初始化番茄检测器
    try:
        if tomato_model_path.exists():
            tomato_detector = TomatoDetector(str(tomato_model_path))
            logger.info("[OK] 番茄成熟度检测器加载成功")
        else:
            logger.warning("[WARN] 番茄检测模型文件不存在，请运行 quick_copy.py")
    except Exception as e:
        logger.warning(f"[ERROR] 加载番茄检测器失败: {e}")

    # 初始化苹果检测器
    try:
        if apple_model_path.exists():
            apple_detector = AppleRipenessDetector(str(apple_model_path))
            logger.info("[OK] 苹果成熟度检测器加载成功")
        else:
            logger.warning("[WARN] 苹果检测模型文件不存在，请运行 quick_copy.py")
    except Exception as e:
        logger.warning(f"[ERROR] 加载苹果检测器失败: {e}")

    if crop_growth_model_path.exists():
        try:
            crop_growth_model = YOLO(crop_growth_model_path)
        except Exception as e:
            logger.warning(f"加载作物长势模型失败: {e}")
    
    if crop_fruit_model_path.exists():
        try:
            crop_fruit_model = YOLO(crop_fruit_model_path)
        except Exception as e:
            logger.warning(f"加载果实成熟度模型失败: {e}")

    @classmethod
    def get_detection_config(cls):
        """获取检测配置，默认启用所有检测以保持向后兼容"""
        config_mgr = get_config_manager()
        config = config_mgr.get_config()
        detection_config = config.get("detection", {})
        
        # 返回配置，缺失的键默认为 True 以保持向后兼容
        return {
            "enableHelmet": detection_config.get("enableHelmet", True),
            "enableVest": detection_config.get("enableVest", True),
            "enableVehicleIntrusion": detection_config.get("enableVehicleIntrusion", True),
            "enableFire": detection_config.get("enableFire", True),
            "enablePest": detection_config.get("enablePest", True),
            "enableCropGrowth": detection_config.get("enableCropGrowth", True),
            "enableCitrus": detection_config.get("enableCitrus", True)
        }

    @classmethod
    def detect_alarm_case(cls, frame, alarm_case_code):
        det_config = cls.get_detection_config()
        
        if alarm_case_code==0:
            # logger.info("本次帧分析的目标告警场景：安全规范（是否佩戴安全帽、是否穿戴反光衣）")
            
            # 检查安全规范检测是否启用
            helmet_enabled = det_config["enableHelmet"]
            vest_enabled = det_config["enableVest"]
            
            if not helmet_enabled and not vest_enabled:
                logger.info("安全规范检测已关闭（安全帽和反光衣检测均禁用）")
                return False, []
            
            head_detected=False
            head_class_id=0 # 未戴安全帽的头部在模型训练集中的类别id
            
            if helmet_enabled:
                # 减小推理尺寸，提高速度
                helmet_result=cls.helmet_model(frame,imgsz=320)[0]
                for box in helmet_result.boxes:
                    class_id = int(box.cls[0])
                    if class_id == head_class_id:
                        head_detected=True

            no_vest_detected=False
            no_vest_class_id=0 # 未穿反光衣在模型训练集中的类别id
            
            if vest_enabled:
                # 减小推理尺寸，提高速度
                vest_result=cls.vest_model(frame,imgsz=320)[0]
                for box in vest_result.boxes:
                    class_id = int(box.cls[0])
                    if class_id == no_vest_class_id:
                        no_vest_detected=True

            if head_detected or no_vest_detected:
                annotated_frames=[]
                if head_detected and helmet_enabled:
                    annotated_frames.append(helmet_result.plot())
                if no_vest_detected and vest_enabled:
                    annotated_frames.append(vest_result.plot())
                return True, annotated_frames
            else:
                return False, []
        elif alarm_case_code==1:
            # logger.info("本次帧分析的目标告警场景：区域入侵（是否存在人体、车辆）")
            
            # 检查区域入侵检测是否启用
            if not det_config["enableVehicleIntrusion"]:
                logger.info("区域入侵检测已关闭")
                return False, []
                
            # 减小推理尺寸，提高速度
            person_vehicle_result=cls.person_vehicle_model(frame, classes=[0,1,2,3,4,5,6,7], imgsz=320)[0]
            person_detected=len(person_vehicle_result.boxes)>0
            annotated_frames=[person_vehicle_result.plot()]
            return person_detected, annotated_frames
        elif alarm_case_code==2:
            # logger.info("本次帧分析的目标告警场景：火警（是否存在火焰、烟雾）")
            
            # 检查火警检测是否启用
            if not det_config["enableFire"]:
                logger.info("火警检测已关闭")
                return False, []
                
            # 减小推理尺寸，提高速度
            fire_smoke_result=cls.fire_smoke_model(frame, imgsz=320)[0]
            fire_or_smoke_detected=len(fire_smoke_result.boxes)>0
            annotated_frames=[fire_smoke_result.plot()]
            return fire_or_smoke_detected, annotated_frames
        elif alarm_case_code==3:
            # 作物病虫害/害虫检测
            
            # 检查害虫检测是否启用
            if not det_config["enablePest"]:
                logger.info("害虫检测已关闭")
                return False, []
                
            if cls.pest_detector and cls.pest_detector.model is not None:
                try:
                    # 使用害虫检测器
                    # 将 frame 是 OpenCV 图像，需要转换为 bytes
                    import cv2
                    import numpy as np
                    
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_bytes = buffer.tobytes()
                    
                    # 使用我们的害虫检测器
                    predictions, annotated_image_base64 = cls.pest_detector.detect_and_annotate(image_bytes)
                    
                    pest_detected = len(predictions) > 0
                    
                    # 准备标注帧
                    annotated_frames = []
                    if pest_detected:
                        # 将 base64 转回图像用于显示
                        try:
                            import base64
                            img_data = base64.b64decode(annotated_image_base64.split(',')[1])
                            nparr = np.frombuffer(img_data, np.uint8)
                            annotated_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            annotated_frames.append(annotated_frame)
                        except Exception as e:
                            logger.warning(f"解析标注图像失败: {e}")
                    
                    return pest_detected, annotated_frames
                except Exception as e:
                    logger.error(f"害虫检测出错: {e}")
                    return False, []
            else:
                logger.warning("害虫检测器未加载，请确保 pest_detector.pt 文件存在")
                return False, []
        elif alarm_case_code==4:
            # 作物长势异常检测
            
            # 检查作物长势检测是否启用
            if not det_config["enableCropGrowth"]:
                logger.info("作物长势检测已关闭")
                return False, []
                
            if cls.crop_growth_model:
                try:
                    growth_result = cls.crop_growth_model(frame, imgsz=320)[0]
                    if hasattr(growth_result, 'boxes'):
                        abnormal_detected = len(growth_result.boxes) > 0
                    else:
                        abnormal_detected = False
                    annotated_frames = [growth_result.plot()]
                    return abnormal_detected, annotated_frames
                except Exception as e:
                    logger.error(f"作物长势检测出错: {e}")
                    return False, []
            else:
                logger.warning("作物长势模型未加载，请确保 crop_growth.pt 文件存在")
                return False, []
        elif alarm_case_code==5:
            # 柑橘成熟度检测
            
            # 检查柑橘检测是否启用
            if not det_config["enableCitrus"]:
                logger.info("柑橘成熟度检测已关闭")
                return False, []
                
            if cls.citrus_detector and cls.citrus_detector.model is not None:
                try:
                    # 使用柑橘检测器
                    # 将 frame 是 OpenCV 图像，需要转换为 bytes
                    import cv2
                    import numpy as np
                    
                    _, buffer = cv2.imencode('.jpg', frame)
                    image_bytes = buffer.tobytes()
                    
                    # 使用我们的柑橘检测器
                    predictions, annotated_image_base64 = cls.citrus_detector.detect_and_annotate(image_bytes)
                    
                    citrus_detected = len(predictions) > 0
                    
                    # 准备标注帧
                    annotated_frames = []
                    if citrus_detected:
                        # 将 base64 转回图像用于显示
                        try:
                            import base64
                            img_data = base64.b64decode(annotated_image_base64.split(',')[1])
                            nparr = np.frombuffer(img_data, np.uint8)
                            annotated_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            annotated_frames.append(annotated_frame)
                        except Exception as e:
                            logger.warning(f"解析标注图像失败: {e}")
                    
                    return citrus_detected, annotated_frames
                except Exception as e:
                    logger.error(f"柑橘成熟度检测出错: {e}")
                    return False, []
            else:
                logger.warning("柑橘检测器未加载，请确保 citrus_maturity.pt 文件存在")
                return False, []
        else:
            logger.info("本次帧分析失败: 目标告警场景未知")
            return None, []


