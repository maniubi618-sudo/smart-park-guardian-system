import asyncio
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime
import pytz
from io import BytesIO
import base64
from PIL import Image

import cv2
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect

from app.JSON_schemas.Result_pydantic import Result
from app.JSON_schemas.camera_info_pydantic import CameraInfoResponse, CameraInfoCreate, CameraInfoUpdate, \
    CameraInfoPageResponse, CameraStatusReport
from app.crud.camera_crud import (
    get_camera_info,
    get_camera_infos_with_condition as crud_get_camera_infos_with_condition,
    create_camera_info as crud_create_camera_info,
    update_camera_info as crud_update_camera_info,
    delete_camera_infos as crud_delete_camera_infos,
    get_camera_status_stats as crud_get_camera_status_stats
)
from app.crud.park_area_crud import get_park_area as crud_get_park_area
from app.DB_models.camera_info_db import CameraInfoDB
from app.services.thread_pool_manager import executor as db_executor
from app.services.detection_service import DetectionService
from app.services.safety_analysis_service import SafetyAnalysisService
from app.services.storage_service import StorageService
from app.services.config_manager import get_config_manager
from app.utils.oss_utils import get_now
from app.DB_models.alarm_db import AlarmDB
from app.crud.alarm_crud import create_alarm
from app.services.alarm_broadcast_service import sync_broadcast_alarm
from app.utils.logger import get_logger

logger = get_logger()


class AppleTracker:
    """
    苹果跟踪器，用于在视频帧间去重跟踪苹果
    基于 IOU (Intersection over Union) 匹配
    """
    def __init__(self, iou_threshold=0.3, max_frames_missing=5):
        self.tracked_apples = {}  # {track_id: {"bbox": (x1,y1,x2,y2), "maturity": float, "class": str, "frames_missing": int}}
        self.next_track_id = 0
        self.iou_threshold = iou_threshold
        self.max_frames_missing = max_frames_missing
        self.current_frame_apples = []  # 当前帧检测到的苹果
        self.historical_max_maturity = 0  # 历史最高成熟度，即使苹果丢失也保留
        self.historical_total = 0  # 历史总苹果数量（累计追踪）
        self.historical_stage_20 = 0  # 历史20%成熟总数
        self.historical_stage_40 = 0  # 历史40%成熟总数
        self.historical_stage_60 = 0  # 历史60%成熟总数
        self.historical_stage_80 = 0  # 历史80%成熟总数
        self.historical_stage_100 = 0  # 历史100%成熟总数
    
    def calculate_iou(self, box1, box2):
        """计算两个边框的 IOU"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # 计算交集
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)
        
        if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
            return 0.0
        
        inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
        
        # 计算各自的面积
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        
        # 计算并集
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def update(self, detections):
        """
        更新跟踪器，传入当前帧的检测结果
        返回: dict with tracking summary
        """
        self.current_frame_apples = []
        matched_track_ids = set()
        
        for det in detections:
            bbox = det.get('bbox', {})
            x1, y1, x2, y2 = bbox.get('x1', 0), bbox.get('y1', 0), bbox.get('x2', 0), bbox.get('y2', 0)
            box = (x1, y1, x2, y2)
            maturity = det.get('maturity', 0) or 0
            class_name = det.get('class', '')
            
            best_match_id = None
            best_iou = 0
            
            # 查找最佳匹配
            for track_id, tracked in self.tracked_apples.items():
                if tracked['frames_missing'] <= self.max_frames_missing:
                    iou = self.calculate_iou(box, tracked['bbox'])
                    if iou > best_iou and iou >= self.iou_threshold:
                        best_iou = iou
                        best_match_id = track_id
            
            if best_match_id is not None:
                # 更新已跟踪的苹果
                self.tracked_apples[best_match_id] = {
                    'bbox': box,
                    'maturity': maturity,
                    'class': class_name,
                    'frames_missing': 0
                }
                matched_track_ids.add(best_match_id)
            else:
                # 新苹果
                new_id = self.next_track_id
                self.next_track_id += 1
                self.tracked_apples[new_id] = {
                    'bbox': box,
                    'maturity': maturity,
                    'class': class_name,
                    'frames_missing': 0
                }
                matched_track_ids.add(new_id)
                self.historical_total += 1  # 增加历史总数

                # 根据成熟度阶段增加历史分类计数
                if maturity >= 100:
                    self.historical_stage_100 += 1
                elif maturity >= 80:
                    self.historical_stage_80 += 1
                elif maturity >= 60:
                    self.historical_stage_60 += 1
                elif maturity >= 40:
                    self.historical_stage_40 += 1
                else:
                    self.historical_stage_20 += 1
        
        # 增加未匹配苹果的丢失帧数
        for track_id in self.tracked_apples:
            if track_id not in matched_track_ids:
                self.tracked_apples[track_id]['frames_missing'] += 1
        
        # 更新历史最高成熟度（即使苹果丢失也保留）
        for det in detections:
            maturity = det.get('maturity', 0) or 0
            if maturity > self.historical_max_maturity:
                self.historical_max_maturity = maturity
        
        return self.get_summary()
    
    def get_summary(self):
        """获取跟踪摘要"""
        active = [t for t in self.tracked_apples.values() if t['frames_missing'] <= self.max_frames_missing]

        # 统计各成熟阶段
        stage_20 = 0
        stage_40 = 0
        stage_60 = 0
        stage_80 = 0
        stage_100 = 0
        
        for t in active:
            maturity = t.get('maturity', 0) or 0
            if maturity >= 100:
                stage_100 += 1
            elif maturity >= 80:
                stage_80 += 1
            elif maturity >= 60:
                stage_60 += 1
            elif maturity >= 40:
                stage_40 += 1
            else:
                stage_20 += 1

        # 使用历史最高成熟度（即使苹果丢失也保留之前的最大值）
        active_maturities = [t.get('maturity', 0) or 0 for t in active]
        current_max = max(active_maturities, default=0)
        max_maturity = max(self.historical_max_maturity, current_max)

        # 如果当前没有活跃苹果，使用历史分类计数
        final_stage_20 = stage_20 if stage_20 > 0 else self.historical_stage_20
        final_stage_40 = stage_40 if stage_40 > 0 else self.historical_stage_40
        final_stage_60 = stage_60 if stage_60 > 0 else self.historical_stage_60
        final_stage_80 = stage_80 if stage_80 > 0 else self.historical_stage_80
        final_stage_100 = stage_100 if stage_100 > 0 else self.historical_stage_100
        final_total = len(active) if len(active) > 0 else self.historical_total

        return {
            'total': final_total,
            'active_total': len(active),
            'historical_total': self.historical_total,
            'stage_20': final_stage_20,
            'stage_40': final_stage_40,
            'stage_60': final_stage_60,
            'stage_80': final_stage_80,
            'stage_100': final_stage_100,
            'active_stage_20': stage_20,
            'active_stage_40': stage_40,
            'active_stage_60': stage_60,
            'active_stage_80': stage_80,
            'active_stage_100': stage_100,
            'max_maturity': max_maturity
        }

    def reset(self):
        """重置跟踪器"""
        self.tracked_apples = {}
        self.next_track_id = 0
        self.historical_max_maturity = 0
        self.historical_total = 0
        self.historical_stage_20 = 0
        self.historical_stage_40 = 0
        self.historical_stage_60 = 0
        self.historical_stage_80 = 0
        self.historical_stage_100 = 0


class TomatoTracker:
    """
    番茄跟踪器，用于在视频帧间去重跟踪番茄
    基于 IOU (Intersection over Union) 匹配
    """
    def __init__(self, iou_threshold=0.3, max_frames_missing=5):
        self.tracked_tomatoes = {}  # {track_id: {"bbox": (x1,y1,x2,y2), "maturity": float, "class": str, "frames_missing": int}}
        self.next_track_id = 0
        self.iou_threshold = iou_threshold
        self.max_frames_missing = max_frames_missing
        self.current_frame_tomatoes = []  # 当前帧检测到的番茄
        self.historical_max_maturity = 0  # 历史最高成熟度，即使番茄丢失也保留
        self.historical_total = 0  # 历史总番茄数量（累计追踪）
        self.historical_unripe = 0  # 历史未成熟总数
        self.historical_ripe = 0  # 历史成熟总数
        self.historical_overripe = 0  # 历史过熟总数
    
    def calculate_iou(self, box1, box2):
        """计算两个边框的 IOU"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # 计算交集
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)
        
        if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
            return 0.0
        
        inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
        
        # 计算各自的面积
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        
        # 计算并集
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def update(self, detections):
        """
        更新跟踪器，传入当前帧的检测结果
        返回: (new_tomatoes, all_tracked) - 新检测到的番茄列表，所有活跃跟踪的番茄列表
        """
        self.current_frame_tomatoes = []
        matched_track_ids = set()
        
        for det in detections:
            bbox = det.get('bbox', {})
            x1, y1, x2, y2 = bbox.get('x1', 0), bbox.get('y1', 0), bbox.get('x2', 0), bbox.get('y2', 0)
            box = (x1, y1, x2, y2)
            maturity = det.get('maturity', 0) or 0
            class_name = det.get('class', '')
            
            best_match_id = None
            best_iou = 0
            
            # 查找最佳匹配
            for track_id, tracked in self.tracked_tomatoes.items():
                if tracked['frames_missing'] <= self.max_frames_missing:
                    iou = self.calculate_iou(box, tracked['bbox'])
                    if iou > best_iou and iou >= self.iou_threshold:
                        best_iou = iou
                        best_match_id = track_id
            
            if best_match_id is not None:
                # 更新已跟踪的番茄
                self.tracked_tomatoes[best_match_id] = {
                    'bbox': box,
                    'maturity': maturity,
                    'class': class_name,
                    'frames_missing': 0
                }
                matched_track_ids.add(best_match_id)
            else:
                # 新番茄
                new_id = self.next_track_id
                self.next_track_id += 1
                self.tracked_tomatoes[new_id] = {
                    'bbox': box,
                    'maturity': maturity,
                    'class': class_name,
                    'frames_missing': 0
                }
                matched_track_ids.add(new_id)
                self.historical_total += 1  # 增加历史总数

                # 根据类别增加历史分类计数
                class_normalized = class_name.lower().replace('_', '-').replace(' ', '-')
                if 'unripe' in class_normalized or 'green' in class_normalized:
                    self.historical_unripe += 1
                elif 'ripe' in class_normalized or 'red' in class_normalized:
                    self.historical_ripe += 1
                elif 'overripe' in class_normalized or 'over' in class_normalized:
                    self.historical_overripe += 1
                else:
                    # 基于 maturity 判断类别
                    if maturity < 60:
                        self.historical_unripe += 1
                    elif maturity < 95:
                        self.historical_ripe += 1
                    else:
                        self.historical_overripe += 1
        
        # 增加未匹配番茄的丢失帧数
        for track_id in self.tracked_tomatoes:
            if track_id not in matched_track_ids:
                self.tracked_tomatoes[track_id]['frames_missing'] += 1
        
        # 构建当前帧活跃的番茄列表
        active_tomatoes = []
        new_tomatoes_list = []
        for track_id, tracked in self.tracked_tomatoes.items():
            if tracked['frames_missing'] <= self.max_frames_missing:
                active_tomatoes.append({
                    'track_id': track_id,
                    'bbox': tracked['bbox'],
                    'maturity': tracked['maturity'],
                    'class': tracked['class'],
                    'is_new': track_id in matched_track_ids and len([
                        t for t in detections if self.calculate_iou(tracked['bbox'], (t.get('bbox',{}).get('x1',0), t.get('bbox',{}).get('y1',0), t.get('bbox',{}).get('x2',0), t.get('bbox',{}).get('y2',0))) >= self.iou_threshold
                    ]) > 0 and tracked['frames_missing'] == 0
                })
        
        # 标记新番茄（当前帧首次出现）
        for i, det in enumerate(detections):
            bbox = det.get('bbox', {})
            x1, y1, x2, y2 = bbox.get('x1', 0), bbox.get('y1', 0), bbox.get('x2', 0), bbox.get('y2', 0)
            is_new = True
            for track_id, tracked in self.tracked_tomatoes.items():
                if tracked['frames_missing'] == 0 and self.calculate_iou((x1,y1,x2,y2), tracked['bbox']) >= self.iou_threshold:
                    # 这个检测匹配到了一个活跃跟踪的番茄，不是新的
                    is_new = False
                    break
            if is_new:
                new_tomatoes_list.append(det)

        # 更新历史最高成熟度（即使番茄丢失也保留）
        for det in detections:
            maturity = det.get('maturity', 0) or 0
            if maturity > self.historical_max_maturity:
                self.historical_max_maturity = maturity
        
        return new_tomatoes_list, active_tomatoes
    
    def _normalize_class_name(self, class_name):
        """规范化类名以便匹配"""
        if not class_name:
            return ''
        name = class_name.lower().replace('_', '-').replace(' ', '-').replace('tomato', '').replace('tomates', '')
        return name

    def get_summary(self):
        """获取跟踪摘要"""
        active = [t for t in self.tracked_tomatoes.values() if t['frames_missing'] <= self.max_frames_missing]

        # 使用规范化类名进行匹配
        unripe = 0
        ripe = 0
        overripe = 0
        for t in active:
            normalized = self._normalize_class_name(t['class'])
            # 匹配未成熟 (unripe/green)
            if 'unripe' in normalized or 'green' in normalized or '青' in t['class']:
                unripe += 1
            # 匹配成熟 (ripe/red)
            elif 'ripe' in normalized or 'red' in normalized or '成熟' in t['class']:
                ripe += 1
            # 匹配过熟 (overripe/over)
            elif 'overripe' in normalized or 'over' in normalized or '过熟' in t['class']:
                overripe += 1
            # 如果仍然不匹配，使用 maturity 值来判断
            else:
                maturity = t.get('maturity', 0) or 0
                if maturity < 60:
                    unripe += 1
                elif maturity < 95:
                    ripe += 1
                else:
                    overripe += 1

        # 使用历史最高成熟度（即使番茄丢失也保留之前的最大值）
        # 同时也要考虑当前活跃番茄的 maturity
        active_maturities = [t.get('maturity', 0) or 0 for t in active]
        current_max = max(active_maturities, default=0)
        max_maturity = max(self.historical_max_maturity, current_max)

        # 如果当前没有活跃番茄，使用历史分类计数
        final_unripe = unripe if unripe > 0 else self.historical_unripe
        final_ripe = ripe if ripe > 0 else self.historical_ripe
        final_overripe = overripe if overripe > 0 else self.historical_overripe
        final_total = len(active) if len(active) > 0 else self.historical_total

        return {
            'total': final_total,
            'active_total': len(active),
            'historical_total': self.historical_total,
            'unripe': final_unripe,
            'ripe': final_ripe,
            'overripe': final_overripe,
            'active_unripe': unripe,
            'active_ripe': ripe,
            'active_overripe': overripe,
            'max_maturity': max_maturity
        }

    def reset(self):
        """重置跟踪器"""
        self.tracked_tomatoes = {}
        self.next_track_id = 0
        self.historical_max_maturity = 0
        self.historical_total = 0
        self.historical_unripe = 0
        self.historical_ripe = 0
        self.historical_overripe = 0


class CitrusTracker:
    """
    柑橘跟踪器，用于在视频帧间去重跟踪柑橘
    基于 IOU (Intersection over Union) 匹配
    """
    def __init__(self, iou_threshold=0.3, max_frames_missing=5):
        self.tracked_citrus = {}
        self.next_track_id = 0
        self.iou_threshold = iou_threshold
        self.max_frames_missing = max_frames_missing
        self.historical_max_maturity = 0  # 历史最高成熟度，即使柑橘丢失也保留
        self.historical_total = 0  # 历史总柑橘数量（累计追踪）
        self.historical_unripe = 0  # 历史未成熟总数
        self.historical_ripe = 0  # 历史成熟总数
        self.historical_rotten = 0  # 历史腐烂总数
    
    def calculate_iou(self, box1, box2):
        """计算两个边框的 IOU"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)
        
        if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
            return 0.0
        
        inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def update(self, detections):
        """更新跟踪器"""
        matched_track_ids = set()
        
        for det in detections:
            bbox = det.get('bbox', {})
            x1, y1, x2, y2 = bbox.get('x1', 0), bbox.get('y1', 0), bbox.get('x2', 0), bbox.get('y2', 0)
            box = (x1, y1, x2, y2)
            maturity = det.get('maturity', 0) or 0
            class_name = det.get('class', '')
            
            best_match_id = None
            best_iou = 0
            
            for track_id, tracked in self.tracked_citrus.items():
                if tracked['frames_missing'] <= self.max_frames_missing:
                    iou = self.calculate_iou(box, tracked['bbox'])
                    if iou > best_iou and iou >= self.iou_threshold:
                        best_iou = iou
                        best_match_id = track_id
            
            if best_match_id is not None:
                self.tracked_citrus[best_match_id] = {
                    'bbox': box,
                    'maturity': maturity,
                    'class': class_name,
                    'frames_missing': 0
                }
                matched_track_ids.add(best_match_id)
            else:
                new_id = self.next_track_id
                self.next_track_id += 1
                self.tracked_citrus[new_id] = {
                    'bbox': box,
                    'maturity': maturity,
                    'class': class_name,
                    'frames_missing': 0
                }
                matched_track_ids.add(new_id)
                self.historical_total += 1  # 增加历史总数

                # 根据类别增加历史分类计数
                class_normalized = class_name.lower()
                if 'unripe' in class_normalized or 'green' in class_normalized:
                    self.historical_unripe += 1
                elif 'ripe' in class_normalized or 'orange' in class_normalized:
                    self.historical_ripe += 1
                elif 'rotten' in class_normalized or 'rot' in class_normalized:
                    self.historical_rotten += 1
                else:
                    # 基于 maturity 判断类别
                    if maturity < 60:
                        self.historical_unripe += 1
                    elif maturity < 95:
                        self.historical_ripe += 1
                    else:
                        self.historical_rotten += 1
        
        for track_id in self.tracked_citrus:
            if track_id not in matched_track_ids:
                self.tracked_citrus[track_id]['frames_missing'] += 1

        # 更新历史最高成熟度（即使柑橘丢失也保留）
        for det in detections:
            maturity = det.get('maturity', 0) or 0
            if maturity > self.historical_max_maturity:
                self.historical_max_maturity = maturity

        return self.get_summary()
    
    def get_summary(self):
        """获取跟踪摘要"""
        active = [t for t in self.tracked_citrus.values() if t['frames_missing'] <= self.max_frames_missing]

        # 使用规范化类名进行匹配
        unripe = 0
        ripe = 0
        rotten = 0
        for t in active:
            class_name = t.get('class', '').lower()
            # 匹配未成熟 (unripe/green)
            if 'unripe' in class_name or 'green' in class_name or '青' in t.get('class', ''):
                unripe += 1
            # 匹配成熟 (ripe/orange)
            elif 'ripe' in class_name or 'orange' in class_name or '成熟' in t.get('class', ''):
                ripe += 1
            # 匹配腐烂 (rotten/rot)
            elif 'rotten' in class_name or 'rot' in class_name or '腐烂' in t.get('class', ''):
                rotten += 1
            # 如果仍然不匹配，使用 maturity 值来判断
            else:
                maturity = t.get('maturity', 0) or 0
                if maturity < 60:
                    unripe += 1
                elif maturity < 95:
                    ripe += 1
                else:
                    rotten += 1

        # 使用历史最高成熟度（即使柑橘丢失也保留之前的最大值）
        # 同时也要考虑当前活跃柑橘的 maturity
        active_maturities = [t.get('maturity', 0) or 0 for t in active]
        current_max = max(active_maturities, default=0)
        max_maturity = max(self.historical_max_maturity, current_max)

        # 如果当前没有活跃柑橘，使用历史分类计数
        final_unripe = unripe if unripe > 0 else self.historical_unripe
        final_ripe = ripe if ripe > 0 else self.historical_ripe
        final_rotten = rotten if rotten > 0 else self.historical_rotten
        final_total = len(active) if len(active) > 0 else self.historical_total

        return {
            'total': final_total,
            'active_total': len(active),
            'historical_total': self.historical_total,
            'unripe': final_unripe,
            'ripe': final_ripe,
            'rotten': final_rotten,
            'active_unripe': unripe,
            'active_ripe': ripe,
            'active_rotten': rotten,
            'max_maturity': max_maturity
        }

    def reset(self):
        """重置跟踪器"""
        self.tracked_citrus = {}
        self.next_track_id = 0
        self.historical_max_maturity = 0
        self.historical_total = 0
        self.historical_unripe = 0
        self.historical_ripe = 0
        self.historical_rotten = 0


class CameraInfoService:
    # 类级别的跟踪器字典，支持多视频同时分析
    _tomato_trackers = {}
    _citrus_trackers = {}
    _apple_trackers = {}
    
    @staticmethod
    def _get_tomato_tracker(session_id: str = "default") -> TomatoTracker:
        """获取或创建番茄跟踪器"""
        if session_id not in CameraInfoService._tomato_trackers:
            CameraInfoService._tomato_trackers[session_id] = TomatoTracker()
        return CameraInfoService._tomato_trackers[session_id]
    
    @staticmethod
    def _get_citrus_tracker(session_id: str = "default") -> CitrusTracker:
        """获取或创建柑橘跟踪器"""
        if session_id not in CameraInfoService._citrus_trackers:
            CameraInfoService._citrus_trackers[session_id] = CitrusTracker()
        return CameraInfoService._citrus_trackers[session_id]
    
    @staticmethod
    def _get_apple_tracker(session_id: str = "default") -> AppleTracker:
        """获取或创建苹果跟踪器"""
        if session_id not in CameraInfoService._apple_trackers:
            CameraInfoService._apple_trackers[session_id] = AppleTracker()
        return CameraInfoService._apple_trackers[session_id]
    
    @staticmethod
    def _reset_tomato_tracker(session_id: str = "default"):
        """重置番茄跟踪器"""
        if session_id in CameraInfoService._tomato_trackers:
            CameraInfoService._tomato_trackers[session_id].reset()
    
    @staticmethod
    def _reset_citrus_tracker(session_id: str = "default"):
        """重置柑橘跟踪器"""
        if session_id in CameraInfoService._citrus_trackers:
            CameraInfoService._citrus_trackers[session_id].reset()
    
    @staticmethod
    def _reset_apple_tracker(session_id: str = "default"):
        """重置苹果跟踪器"""
        if session_id in CameraInfoService._apple_trackers:
            CameraInfoService._apple_trackers[session_id].reset()
    
    @staticmethod
    async def get_camera_info(db: Session, camera_info_id: int) -> Result[CameraInfoResponse]:
        """
        获取单个摄像头信息

        Args:
            db: 数据库会话
            camera_info_id: 摄像头信息ID

        Returns:
            Result[CameraInfoResponse]: 包含摄像头信息的响应对象
        """
        # 使用线程池执行数据库操作
        camera_info_with_park_area = await asyncio.get_event_loop().run_in_executor(
            db_executor,
            get_camera_info,
            db, camera_info_id
        )

        # 检查摄像头信息是否存在
        if not camera_info_with_park_area:
            return Result.ERROR("未找到指定的摄像头信息")

        # 从联表查询结果中提取信息
        camera_info = camera_info_with_park_area[0]  # CameraInfoDB instance
        park_area_name = camera_info_with_park_area[1]  # Park area name

        # 转换为响应模型
        camera_response = CameraInfoResponse(
            camera_id=camera_info.camera_id,
            camera_name=camera_info.camera_name,
            park_area_id=camera_info.park_area_id,
            park_area=park_area_name,
            install_position=camera_info.install_position,
            rtsp_url=camera_info.rtsp_url,
            analysis_mode=camera_info.analysis_mode,
            camera_status=camera_info.camera_status,
            create_time=camera_info.create_time,
            update_time=camera_info.update_time
        )

        return Result.SUCCESS(camera_response)

    @staticmethod
    async def get_camera_status_report(db: Session) -> Result[CameraStatusReport]:
        """
        获取摄像头状态统计报告

        Args:
            db: 数据库会话

        Returns:
            Result[CameraStatusReport]: 包含摄像头状态统计数据的响应对象
        """
        try:
            # 使用线程池执行数据库操作
            online_count, total_count = await asyncio.get_event_loop().run_in_executor(
                db_executor,
                crud_get_camera_status_stats,
                db
            )

            # 计算离线摄像头数
            offline_count = total_count - online_count

            return Result.SUCCESS(CameraStatusReport(
                online_count=online_count,
                total_count=total_count,
                offline_count=offline_count
            ))
        except Exception as e:
            return Result.ERROR(f"查询摄像头状态统计失败: {str(e)}")

    @staticmethod
    async def get_camera_infos_with_condition(
            db: Session,
            park_area_id: Optional[int] = None,
            analysis_mode: Optional[int] = None,
            camera_status: Optional[int] = None,
            skip: int = 0,
            limit: int = 10
    ) -> Result[CameraInfoPageResponse]:
        """
        根据条件获取摄像头信息（支持分页）

        Args:
            db: 数据库会话
            park_area_id: 园区位置ID
            analysis_mode: 分析模式
            camera_status: 摄像头状态
            skip: 跳过的记录数
            limit: 限制返回的记录数

        Returns:
            Result[CameraInfoPageResponse]: 包含摄像头信息列表和分页信息的响应对象
        """
        try:
            # 使用线程池执行数据库操作，分别获取符合条件的总记录数和当前页数据
            total, camera_infos_with_details = await asyncio.get_event_loop().run_in_executor(
                    db_executor,
                    crud_get_camera_infos_with_condition,
                    db, park_area_id, analysis_mode, camera_status, skip, limit
                )
            
            # 转换查询结果为CameraInfoResponse对象
            camera_responses = []
            for camera_info_row in camera_infos_with_details:
                # 从联表查询结果中提取信息
                camera_info = camera_info_row[0]  # CameraInfoDB instance
                park_area_name = camera_info_row[1]  # Park area name
                
                camera_response = CameraInfoResponse(
                    camera_id=camera_info.camera_id,
                    camera_name=camera_info.camera_name,
                    park_area_id=camera_info.park_area_id,
                    park_area=park_area_name,
                    install_position=camera_info.install_position,
                    rtsp_url=camera_info.rtsp_url,
                    analysis_mode=camera_info.analysis_mode,
                    camera_status=camera_info.camera_status,
                    create_time=camera_info.create_time,
                    update_time=camera_info.update_time
                )
                camera_responses.append(camera_response)

            return Result.SUCCESS(CameraInfoPageResponse(total=total, rows=camera_responses))
        except Exception as e:
            return Result.ERROR(f"查询摄像头信息失败: {str(e)}")

    @staticmethod
    async def create_camera_info(db: Session, camera_info: CameraInfoCreate) -> Result[CameraInfoResponse]:
        """
        创建新摄像头信息

        Args:
            db: 数据库会话
            camera_info: 摄像头信息创建请求数据

        Returns:
            Result[CameraInfoResponse]: 包含创建的摄像头信息的响应对象
        """
        try:
            # 检查园区区域是否存在
            park_area = await asyncio.get_event_loop().run_in_executor(
                db_executor,
                crud_get_park_area,
                db, camera_info.park_area_id
            )
            if not park_area:
                return Result.ERROR("指定的园区区域不存在")

            # 使用线程池执行数据库操作
            db_camera_info, park_area_name = await asyncio.get_event_loop().run_in_executor(
                db_executor,
                crud_create_camera_info,
                db, camera_info
            )

            # 转换为响应模型
            camera_response = CameraInfoResponse(
                camera_id=db_camera_info.camera_id,
                camera_name=db_camera_info.camera_name,
                park_area_id=db_camera_info.park_area_id,
                park_area=park_area_name,
                install_position=db_camera_info.install_position,
                rtsp_url=db_camera_info.rtsp_url,
                analysis_mode=db_camera_info.analysis_mode,
                camera_status=db_camera_info.camera_status,
                create_time=db_camera_info.create_time,
                update_time=db_camera_info.update_time
            )

            return Result.SUCCESS(camera_response, "摄像头信息创建成功")
        except Exception as e:
            return Result.ERROR(f"创建摄像头信息失败: {str(e)}")

    @staticmethod
    async def update_camera_info(
            db: Session,
            camera_info_id: int,
            camera_info_update: CameraInfoUpdate
    ) -> Result[CameraInfoResponse]:
        """
        修改摄像头信息

        Args:
            db: 数据库会话
            camera_info_id: 摄像头信息ID
            camera_info_update: 摄像头信息更新数据

        Returns:
            Result[CameraInfoResponse]: 包含更新后的摄像头信息的响应对象
        """
        try:
            # 检查园区区域是否存在（如果提供了park_area_id）
            if camera_info_update.park_area_id is not None:
                park_area = await asyncio.get_event_loop().run_in_executor(
                    db_executor,
                    crud_get_park_area,
                    db, camera_info_update.park_area_id
                )
                if not park_area:
                    return Result.ERROR("指定的园区区域不存在")

            # 使用线程池执行数据库操作
            updated_camera_info_with_park_area = await asyncio.get_event_loop().run_in_executor(
                db_executor,
                crud_update_camera_info,
                db, camera_info_id, camera_info_update
            )

            # 检查摄像头信息是否存在
            if not updated_camera_info_with_park_area:
                return Result.ERROR("未找到指定的摄像头信息")

            # 从联表查询结果中提取信息
            updated_camera_info = updated_camera_info_with_park_area[0]  # CameraInfoDB instance
            park_area_name = updated_camera_info_with_park_area[1]  # Park area name

            # 转换为响应模型
            camera_response = CameraInfoResponse(
                camera_id=updated_camera_info.camera_id,
                camera_name=updated_camera_info.camera_name,
                park_area_id=updated_camera_info.park_area_id,
                park_area=park_area_name,
                install_position=updated_camera_info.install_position,
                rtsp_url=updated_camera_info.rtsp_url,
                analysis_mode=updated_camera_info.analysis_mode,
                camera_status=updated_camera_info.camera_status,
                create_time=updated_camera_info.create_time,
                update_time=updated_camera_info.update_time
            )

            return Result.SUCCESS(camera_response, "摄像头信息更新成功")
        except Exception as e:
            return Result.ERROR(f"更新摄像头信息失败: {str(e)}")

    @staticmethod
    async def delete_camera_infos(db: Session, camera_info_ids_str: str) -> Result:
        """
        服务层处理摄像头信息删除业务逻辑并构造响应结果

        Args:
            db: 数据库会话
            camera_info_ids_str: 摄像头信息ID字符串（逗号分隔）

        Returns:
            Result: 包含删除结果的响应对象
        """
        # 解析ID列表，支持单个ID或多个ID（用逗号分隔）
        try:
            ids = [int(camera_id.strip()) for camera_id in camera_info_ids_str.split(',') if camera_id.strip()]
            if not ids:
                return Result.ERROR("无效的ID参数")
        except ValueError:
            return Result.ERROR("ID参数格式错误，请提供有效的数字ID")

        # 使用线程池执行数据库操作
        deleted_count = await asyncio.get_event_loop().run_in_executor(
            db_executor, crud_delete_camera_infos, db, ids
        )

        # 构造并返回响应结果
        if deleted_count == 0:
            return Result.ERROR("删除失败: 没有找到指定的任意一个摄像头信息")
        elif deleted_count < len(ids):
            return Result.SUCCESS(
                {"deleted_count": deleted_count},
                f"部分删除成功: 成功删除{deleted_count}条记录"
            )
        else:
            return Result.SUCCESS(
                {"deleted_count": deleted_count},
                f"批量删除成功: 共删除{deleted_count}条记录"
            )

    # rtsp流连通性检测方法

    @classmethod
    async def test_camera_connection(cls, camera_id, db):
        def _test_connection():
            result_container = {}

            def connection_task():
                try:
                    camera_info_result0 = get_camera_info(db, camera_id)
                    if not camera_info_result0:
                        result_container['result'] = Result.ERROR(f"未找到ID为 {camera_id} 的摄像头信息")
                        return

                    # 从元组中提取CameraInfoDB对象
                    camera_info0 = camera_info_result0[0]  # CameraInfoDB instance
                    rtsp_url = camera_info0.rtsp_url

                    is_local_camera = False
                    if rtsp_url == "0":  # RTSP地址为0时，使用本地摄像头（USB摄像头）
                        rtsp_url = 0  # OpenCV使用0表示默认摄像头设备
                        is_local_camera = True
                    elif rtsp_url.startswith("local:"):# 测试时，服务器本地视频充当实时视频流
                        file_name = rtsp_url[6:]
                        project_root = Path(__file__).parent.parent.parent
                        rtsp_url = project_root / 'app' / 'test_videos' / file_name
                        # 检查该文件是否存在
                        if not rtsp_url.exists():
                            result_container['result'] = Result.ERROR(f"本地测试视频文件 {rtsp_url} 不存在，无法进行连接测试")
                            return

                    # 本地摄像头使用 DirectShow 后端（Windows）
                    if is_local_camera:
                        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_DSHOW)
                    else:
                        cap = cv2.VideoCapture(rtsp_url)
                    # 本地摄像头不支持设置超时属性
                    if not is_local_camera:
                        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
                        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 3000)

                    result_container['is_opened'] = cap.isOpened()
                    if cap.isOpened():
                        cap.release()
                        if is_local_camera:
                            result_container['result'] = Result.SUCCESS(True, "本地摄像头连接成功")
                        else:
                            result_container['result'] = Result.SUCCESS(True, "RTSP流连接成功")
                    else:
                        if is_local_camera:
                            result_container['result'] = Result.ERROR("本地摄像头连接失败，请检查摄像头是否被占用或是否存在")
                        else:
                            result_container['result'] = Result.ERROR("RTSP流连接失败")

                except Exception as e:
                    result_container['result'] = Result.ERROR(f"测试连接时发生错误: {str(e)}")

            # 在单独线程中执行连接测试
            thread = threading.Thread(target=connection_task)
            thread.daemon = True
            thread.start()

            # 等待最多5秒
            thread.join(timeout=5.0)

            # 检查线程是否完成
            if thread.is_alive():
                return Result.ERROR("RTSP流连接超时（超过5秒）")

            return result_container['result']

        # 使用线程池执行阻塞的视频连接测试
        test_result = await asyncio.get_event_loop().run_in_executor(db_executor, _test_connection)
        
        # 根据测试结果更新摄像头状态
        # 首先获取摄像头当前状态
        camera_info_result = await asyncio.get_event_loop().run_in_executor(
            db_executor, get_camera_info, db, camera_id
        )
        
        if camera_info_result:
            # 从元组中提取CameraInfoDB对象
            camera_info = camera_info_result[0]  # CameraInfoDB instance
            current_status = camera_info.camera_status
            
            if test_result.code == 1:  # 成功
                # 如果摄像头当前状态是2（在线且安防检测中），保持状态为2
                # 否则更新为1（在线但未开启安防检测）
                new_status = 2 if current_status == 2 else 1
                camera_update = CameraInfoUpdate(camera_status=new_status)
                await asyncio.get_event_loop().run_in_executor(
                    db_executor,
                    crud_update_camera_info,
                    db, camera_id, camera_update
                )
            elif test_result.code == 0:  # 失败
                # 更新摄像头状态为离线（值为0）
                camera_update = CameraInfoUpdate(camera_status=0)
                await asyncio.get_event_loop().run_in_executor(
                    db_executor,
                    crud_update_camera_info,
                    db, camera_id, camera_update
                )
        
        return test_result

    @staticmethod
    async def get_camera_preview(db: Session, camera_id: int) -> Result:
        """
        获取摄像头预览图像

        Args:
            db: 数据库会话
            camera_id: 摄像头ID

        Returns:
            Result: 包含预览图像Base64数据的响应对象
        """
        import base64
        from io import BytesIO
        from PIL import Image

        def _capture_preview():
            try:
                # 获取摄像头信息
                camera_info_result = get_camera_info(db, camera_id)
                if not camera_info_result:
                    return Result.ERROR(f"未找到ID为 {camera_id} 的摄像头信息")

                camera_info = camera_info_result[0]
                rtsp_url = camera_info.rtsp_url

                # 处理不同类型的视频源
                is_local_camera = False
                if rtsp_url == "0":  # 本地摄像头
                    rtsp_url = 0
                    is_local_camera = True
                elif rtsp_url.startswith("local:"):
                    file_name = rtsp_url[6:]
                    project_root = Path(__file__).parent.parent.parent
                    rtsp_url = project_root / 'app' / 'test_videos' / file_name
                    if not rtsp_url.exists():
                        return Result.ERROR(f"本地测试视频文件 {rtsp_url} 不存在")

                # 打开视频流
                if is_local_camera:
                    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_DSHOW)
                else:
                    cap = cv2.VideoCapture(rtsp_url)
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)

                if not cap.isOpened():
                    return Result.ERROR("无法打开摄像头视频流")

                # 读取一帧图像
                ret, frame = cap.read()
                cap.release()

                if not ret or frame is None:
                    return Result.ERROR("无法读取视频帧")

                # 将OpenCV图像(BGR)转换为RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 转换为PIL Image
                pil_image = Image.fromarray(frame_rgb)

                # 调整图像大小以减小传输数据量
                max_size = (640, 480)
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)

                # 转换为Base64
                buffer = BytesIO()
                pil_image.save(buffer, format='JPEG', quality=85)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                return Result.SUCCESS({
                    "image": f"data:image/jpeg;base64,{img_base64}",
                    "camera_name": camera_info.camera_name,
                    "timestamp": datetime.now(pytz.timezone('Asia/Shanghai')).isoformat()
                }, "预览图像获取成功")

            except Exception as e:
                return Result.ERROR(f"获取预览图像失败: {str(e)}")

        # 使用线程池执行
        return await asyncio.get_event_loop().run_in_executor(db_executor, _capture_preview)

    @staticmethod
    async def stream_camera_preview(websocket, camera_id: int, db: Session):
        """
        通过WebSocket流式传输摄像头预览

        Args:
            websocket: WebSocket连接对象
            camera_id: 摄像头ID
            db: 数据库会话
        """
        import base64
        from io import BytesIO
        from PIL import Image
        import asyncio

        cap = None
        try:
            # 获取摄像头信息
            camera_info_result = get_camera_info(db, camera_id)
            if not camera_info_result:
                await websocket.send_json({"error": "未找到摄像头信息"})
                return

            camera_info = camera_info_result[0]
            rtsp_url = camera_info.rtsp_url

            # 处理不同类型的视频源
            is_local_camera = False
            if rtsp_url == "0":  # 本地摄像头
                rtsp_url = 0
                is_local_camera = True
            elif rtsp_url.startswith("local:"):
                file_name = rtsp_url[6:]
                project_root = Path(__file__).parent.parent.parent
                rtsp_url = project_root / 'app' / 'test_videos' / file_name
                if not rtsp_url.exists():
                    await websocket.send_json({"error": "本地测试视频文件不存在"})
                    return

            # 打开视频流
            if is_local_camera:
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(rtsp_url)
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)

            if not cap.isOpened():
                await websocket.send_json({"error": "无法打开摄像头"})
                return

            # 持续发送视频帧
            while True:
                # 读取一帧
                ret, frame = cap.read()
                if not ret or frame is None:
                    await asyncio.sleep(0.1)
                    continue

                # 转换为RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 转换为PIL Image并调整大小
                pil_image = Image.fromarray(frame_rgb)
                max_size = (640, 480)
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)

                # 转换为Base64
                buffer = BytesIO()
                pil_image.save(buffer, format='JPEG', quality=85)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                # 发送到WebSocket
                await websocket.send_json({
                    "image": f"data:image/jpeg;base64,{img_base64}",
                    "timestamp": datetime.now(pytz.timezone('Asia/Shanghai')).isoformat()
                })

                # 控制帧率（约10fps）
                await asyncio.sleep(0.1)

        except WebSocketDisconnect:
            # 客户端断开连接
            logger.info(f"摄像头 {camera_id} 分析测试WebSocket连接已断开")
        except Exception as e:
            logger.error(f"摄像头 {camera_id} 分析测试发生错误: {str(e)}")
            try:
                await websocket.send_json({"error": f"错误: {str(e)}"})
            except:
                pass
        finally:
            if cap:
                cap.release()
                logger.info(f"摄像头 {camera_id} 视频流已释放")

    @staticmethod
    async def stream_camera_analysis(websocket, camera_id: int, db: Session, write_to_database: bool = False, analysis_mode_param: int = None):
        """
        摄像头分析测试的WebSocket流
        启动该功能调取对应摄像头，并对摄像头获取到图像进行分析
        同时显示对应摄像头获取的图像以便调整摄像头

        Args:
            websocket: WebSocket连接对象
            camera_id: 摄像头ID
            db: 数据库会话
            write_to_database: 是否将警告信息写入数据库
            analysis_mode_param: 可选的分析模式参数，如果提供则优先使用
        """
        cap = None
        try:
            # 获取摄像头信息
            camera_info = db.query(CameraInfoDB).filter(CameraInfoDB.camera_id == camera_id).first()
            if not camera_info:
                await websocket.send_json({"error": "摄像头不存在"})
                return

            # 打开摄像头
            rtsp_url = camera_info.rtsp_url
            if rtsp_url == "0":
                # 本地摄像头
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            else:
                # 网络摄像头
                cap = cv2.VideoCapture(rtsp_url)

            if not cap.isOpened():
                await websocket.send_json({"error": "无法打开摄像头"})
                return

            # 帧采样参数，每N帧分析一次
            frame_count = 0
            frame_sample_rate = 15  # 每15帧分析一次，减少分析频率以提高FPS
            last_analysis_results = []
            
            # 获取分析模式（优先使用传入的参数，否则使用数据库中的配置）
            mode = analysis_mode_param if analysis_mode_param is not None else (camera_info.analysis_mode or 1)
            
            # 持续发送视频帧和分析结果
            while True:
                # 检查是否有WebSocket消息需要处理
                try:
                    # 非阻塞地检查WebSocket消息
                    message = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                    if message.get('action') == 'update_write_to_database':
                        write_to_database = message.get('write_to_database', False)
                        logger.info(f"更新write_to_database值为: {write_to_database}")
                except asyncio.TimeoutError:
                    # 没有消息，继续
                    pass
                except Exception as e:
                    # 发生错误，可能是连接已关闭
                    logger.error(f"接收WebSocket消息失败: {str(e)}")
                    break
                
                # 读取一帧
                ret, frame = cap.read()
                if not ret or frame is None:
                    await asyncio.sleep(0.1)
                    continue

                # 直接使用OpenCV调整图像大小，减少转换步骤
                max_size = (320, 240)  # 进一步减小图像尺寸以提高传输速度
                frame_resized = cv2.resize(frame, max_size)

                # 直接使用OpenCV编码为JPEG，降低质量以减小数据量
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]  # 进一步降低图像质量以提高传输速度
                _, buffer = cv2.imencode('.jpg', frame_resized, encode_param)
                img_base64 = base64.b64encode(buffer).decode('utf-8')

                # 帧采样，每N帧分析一次
                analysis_results = last_analysis_results
                if frame_count % frame_sample_rate == 0:
                    # 使用真实的检测服务进行分析
                    helmet_detected = False
                    vest_detected = False
                    fire_detected = False
                    smoke_detected = False
                    person_count = 0
                    vehicle_count = 0
                    intrusion_detected = False
                    pest_detected = False
                    growth_abnormal_detected = False
                    citrus_detected = False
                    citrus_predictions = []
                    tomato_detected = False
                    tomato_predictions = []
                    apple_detected = False
                    apple_predictions = []

                    # 直接使用原始帧，不需要转换
                    frame_cv = frame
                    
                    # 准备并行检测任务
                    tasks = []
                    task_names = []
                    
                    # 根据分析模式添加对应的检测任务
                    if mode in [1, 2]:
                        tasks.append(asyncio.to_thread(lambda: DetectionService.helmet_model(frame_cv, imgsz=320)[0]))
                        task_names.append('helmet')
                        tasks.append(asyncio.to_thread(lambda: DetectionService.vest_model(frame_cv, imgsz=320)[0]))
                        task_names.append('vest')
                    
                    if mode in [1, 4]:
                        tasks.append(asyncio.to_thread(lambda: DetectionService.fire_smoke_model(frame_cv, imgsz=960, conf=0.2)[0]))
                        task_names.append('fire_smoke')
                    
                    if mode in [1, 3]:
                        tasks.append(asyncio.to_thread(lambda: DetectionService.person_vehicle_model(frame_cv, classes=[0,1,2,3,4,5,6,7], imgsz=960)[0]))
                        task_names.append('person_vehicle')
                    
                    if mode in [1, 5]:
                        if DetectionService.pest_detector and DetectionService.pest_detector.model is not None:
                            def detect_pest_task():
                                _, buffer = cv2.imencode('.jpg', frame_cv)
                                image_bytes = buffer.tobytes()
                                return DetectionService.pest_detector.detect_and_annotate(image_bytes)
                            tasks.append(asyncio.to_thread(detect_pest_task))
                            task_names.append('pest')
                    
                    if mode in [1, 6]:
                        if DetectionService.crop_growth_model:
                            tasks.append(asyncio.to_thread(lambda: DetectionService.crop_growth_model(frame_cv, imgsz=640)[0]))
                            task_names.append('growth')
                    
                    if mode in [1, 7]:
                        if DetectionService.citrus_detector and DetectionService.citrus_detector.model is not None:
                            def detect_citrus_task():
                                _, buffer = cv2.imencode('.jpg', frame_cv)
                                image_bytes = buffer.tobytes()
                                return DetectionService.citrus_detector.detect_and_annotate(image_bytes)
                            tasks.append(asyncio.to_thread(detect_citrus_task))
                            task_names.append('citrus')

                    if mode in [1, 9]:
                        if DetectionService.tomato_detector and DetectionService.tomato_detector.model is not None:
                            def detect_tomato_task():
                                _, buffer = cv2.imencode('.jpg', frame_cv)
                                image_bytes = buffer.tobytes()
                                return DetectionService.tomato_detector.detect_and_annotate(image_bytes)
                            tasks.append(asyncio.to_thread(detect_tomato_task))
                            task_names.append('tomato')

                    if mode in [1, 10]:
                        if DetectionService.apple_detector and DetectionService.apple_detector.model is not None:
                            def detect_apple_task():
                                _, buffer = cv2.imencode('.jpg', frame_cv)
                                image_bytes = buffer.tobytes()
                                return DetectionService.apple_detector.detect_and_annotate(image_bytes)
                            tasks.append(asyncio.to_thread(detect_apple_task))
                            task_names.append('apple')

                    # 并行执行所有检测任务
                    try:
                        if tasks:
                            results = await asyncio.gather(*tasks, return_exceptions=True)
                            
                            # 处理检测结果
                            for i, (name, result) in enumerate(zip(task_names, results)):
                                if isinstance(result, Exception):
                                    logger.error(f"{name}检测失败: {str(result)}")
                                    continue
                                
                                if name == 'helmet':
                                    head_class_id = 0
                                    for box in result.boxes:
                                        class_id = int(box.cls[0])
                                        if class_id == head_class_id:
                                            helmet_detected = True
                                            break
                                elif name == 'vest':
                                    no_vest_class_id = 0
                                    for box in result.boxes:
                                        class_id = int(box.cls[0])
                                        if class_id == no_vest_class_id:
                                            vest_detected = True
                                            break
                                elif name == 'fire_smoke':
                                    confidence_threshold = 0.2
                                    for box in result.boxes:
                                        class_id = int(box.cls[0])
                                        confidence = float(box.conf[0])
                                        if confidence >= confidence_threshold:
                                            if class_id == 0:
                                                fire_detected = True
                                            elif class_id == 1:
                                                smoke_detected = True
                                elif name == 'person_vehicle':
                                    confidence_threshold = 0.3
                                    for box in result.boxes:
                                        class_id = int(box.cls[0])
                                        confidence = float(box.conf[0])
                                        if confidence >= confidence_threshold:
                                            if class_id == 0:
                                                person_count += 1
                                            elif class_id in [1, 2, 3, 4, 5, 6, 7]:
                                                vehicle_count += 1
                                elif name == 'pest':
                                    predictions, _ = result
                                    pest_detected = len(predictions) > 0
                                elif name == 'growth':
                                    if hasattr(result, 'boxes'):
                                        growth_abnormal_detected = len(result.boxes) > 0
                                elif name == 'citrus':
                                    predictions, _ = result
                                    citrus_detected = len(predictions) > 0
                                    # 存储柑橘检测结果用于更丰富的展示
                                    citrus_predictions = predictions
                                elif name == 'tomato':
                                    predictions, _ = result
                                    tomato_detected = len(predictions) > 0
                                    # 存储番茄检测结果用于更丰富的展示
                                    tomato_predictions = predictions
                                elif name == 'apple':
                                    predictions, _ = result
                                    apple_detected = len(predictions) > 0
                                    # 存储苹果检测结果用于更丰富的展示
                                    apple_predictions = predictions
                    except Exception as e:
                        logger.error(f"检测任务执行失败: {str(e)}")
                    
                    # 检测区域入侵（人员或车辆）
                    intrusion_detected = person_count > 0 or vehicle_count > 0
                    
                    # 生成分析结果
                    analysis_results = []
                    
                    # 获取检测配置
                    detection_config = DetectionService.get_detection_config()
                    
                    # 根据分析模式添加对应的检测结果
                    if mode in [1, 2]:
                        if detection_config.get('enableHelmet', True) or detection_config.get('enableVest', True):
                            if detection_config.get('enableHelmet', True):
                                analysis_results.append({"label": "未戴安全帽", "value": "检测到" if helmet_detected else "未检测到"})
                            if detection_config.get('enableVest', True):
                                analysis_results.append({"label": "未穿反光衣", "value": "检测到" if vest_detected else "未检测到"})
                    
                    if mode in [1, 4]:
                        analysis_results.extend([
                            {"label": "火焰检测", "value": "检测到" if fire_detected else "未检测到"},
                            {"label": "烟雾检测", "value": "检测到" if smoke_detected else "未检测到"}
                        ])
                    
                    if mode in [1, 3]:
                        if detection_config.get('enableVehicleIntrusion', True):
                            analysis_results.extend([
                                {"label": "人员检测", "value": f"{person_count}人"},
                                {"label": "车辆检测", "value": f"{vehicle_count}辆"},
                                {"label": "区域入侵", "value": "检测到" if intrusion_detected else "未检测到"}
                            ])
                    
                    if mode in [1, 5]:
                        analysis_results.append({
                            "label": "害虫检测", "value": "检测到" if pest_detected else "未检测到"
                        })
                    
                    if mode in [1, 6]:
                        analysis_results.append({
                            "label": "作物长势异常", "value": "检测到" if growth_abnormal_detected else "未检测到"
                        })
                    
                    if mode in [1, 7]:
                        # 首先显示检测状态：有没有检测到橘子
                        if citrus_detected and len(citrus_predictions) > 0:
                            analysis_results.append({
                                "label": "🍊 检测状态",
                                "value": f"✅ 检测到橘子！共{len(citrus_predictions)}个"
                            })
                            
                            # 计算综合成熟度信息
                            citrus_info = []
                            max_maturity = 0
                            unripe_count = 0
                            ripe_count = 0
                            rotten_count = 0
                            
                            for pred in citrus_predictions:
                                maturity = pred.get('maturity', 0) or 0
                                if maturity > max_maturity:
                                    max_maturity = maturity
                                class_name = pred.get('class', '')
                                
                                if class_name == 'unripe_orange':
                                    unripe_count += 1
                                elif class_name == 'ripe_orange':
                                    ripe_count += 1
                                elif class_name == 'rotten_orange':
                                    rotten_count += 1
                            
                            # 显示更丰富的成熟度信息
                            if max_maturity >= 80:
                                ripeness_status = "已成熟"
                            elif max_maturity >= 55:
                                ripeness_status = "转色中"
                            else:
                                ripeness_status = "未成熟"
                            
                            # 详细统计
                            status_detail = []
                            if unripe_count > 0:
                                status_detail.append(f"未成熟:{unripe_count}")
                            if ripe_count > 0:
                                status_detail.append(f"成熟:{ripe_count}")
                            if rotten_count > 0:
                                status_detail.append(f"腐烂:{rotten_count}")
                            
                            analysis_results.append({
                                "label": "柑橘成熟度分析",
                                "value": f"{ripeness_status} (最高成熟度:{max_maturity}%) - {', '.join(status_detail)}"
                            })
                        else:
                            analysis_results.append({
                                "label": "🍊 检测状态",
                                "value": "❌未检测到橘子"
                            })

                    if mode in [1, 9]:
                        # 首先显示检测状态：有没有检测到番茄
                        if tomato_detected and len(tomato_predictions) > 0:
                            analysis_results.append({
                                "label": "🍅 检测状态",
                                "value": f"✅ 检测到番茄！共{len(tomato_predictions)}个"
                            })

                            # 计算综合成熟度信息
                            tomato_info = []
                            max_maturity = 0
                            unripe_count = 0
                            ripe_count = 0
                            overripe_count = 0

                            for pred in tomato_predictions:
                                maturity = pred.get('maturity', 0) or 0
                                if maturity > max_maturity:
                                    max_maturity = maturity
                                class_name = pred.get('class', '')

                                if 'unripe' in class_name.lower() or 'green' in class_name.lower():
                                    unripe_count += 1
                                elif 'ripe' in class_name.lower() or 'red' in class_name.lower():
                                    ripe_count += 1
                                elif 'overripe' in class_name.lower() or 'over' in class_name.lower():
                                    overripe_count += 1

                            # 显示更丰富的成熟度信息
                            if max_maturity >= 80:
                                ripeness_status = "已成熟"
                            elif max_maturity >= 55:
                                ripeness_status = "转色中"
                            else:
                                ripeness_status = "未成熟"

                            # 详细统计
                            status_detail = []
                            if unripe_count > 0:
                                status_detail.append(f"未成熟:{unripe_count}")
                            if ripe_count > 0:
                                status_detail.append(f"成熟:{ripe_count}")
                            if overripe_count > 0:
                                status_detail.append(f"过熟:{overripe_count}")

                            analysis_results.append({
                                "label": "番茄成熟度分析",
                                "value": f"{ripeness_status} (最高成熟度:{max_maturity}%) - {', '.join(status_detail)}"
                            })
                        else:
                            analysis_results.append({
                                "label": "🍅 检测状态",
                                "value": "❌ 未检测到番茄"
                            })

                    if mode in [1, 10]:
                        # 首先显示检测状态：有没有检测到苹果
                        if apple_detected and len(apple_predictions) > 0:
                            analysis_results.append({
                                "label": "🍎 检测状态",
                                "value": f"✅ 检测到苹果！共{len(apple_predictions)}个"
                            })

                            # 计算综合成熟度信息
                            apple_info = []
                            max_maturity = 0
                            stage_20_count = 0
                            stage_40_count = 0
                            stage_60_count = 0
                            stage_80_count = 0
                            stage_100_count = 0

                            for pred in apple_predictions:
                                maturity = pred.get('maturity', 0) or 0
                                if maturity > max_maturity:
                                    max_maturity = maturity
                                maturity_label = pred.get('maturity_label', '')

                                if '20' in maturity_label or '仍在生长' in maturity_label:
                                    stage_20_count += 1
                                elif '40' in maturity_label or '早期发育' in maturity_label:
                                    stage_40_count += 1
                                elif '60' in maturity_label or '中期成熟' in maturity_label:
                                    stage_60_count += 1
                                elif '80' in maturity_label or '即将成熟' in maturity_label:
                                    stage_80_count += 1
                                elif '100' in maturity_label or '完全成熟' in maturity_label:
                                    stage_100_count += 1

                            # 显示更丰富的成熟度信息
                            if max_maturity >= 100:
                                ripeness_status = "完全成熟"
                            elif max_maturity >= 80:
                                ripeness_status = "即将成熟"
                            elif max_maturity >= 60:
                                ripeness_status = "中期成熟"
                            elif max_maturity >= 40:
                                ripeness_status = "早期发育"
                            else:
                                ripeness_status = "仍在生长"

                            # 详细统计
                            status_detail = []
                            if stage_20_count > 0:
                                status_detail.append(f"20%:{stage_20_count}")
                            if stage_40_count > 0:
                                status_detail.append(f"40%:{stage_40_count}")
                            if stage_60_count > 0:
                                status_detail.append(f"60%:{stage_60_count}")
                            if stage_80_count > 0:
                                status_detail.append(f"80%:{stage_80_count}")
                            if stage_100_count > 0:
                                status_detail.append(f"100%:{stage_100_count}")

                            analysis_results.append({
                                "label": "🍎 苹果成熟度分析",
                                "value": f"{ripeness_status} (最高成熟度:{max_maturity}%) - {', '.join(status_detail)}"
                            })
                        else:
                            analysis_results.append({
                                "label": "🍎 检测状态",
                                "value": "❌ 未检测到苹果"
                            })

                    # 保存分析结果，用于未分析的帧
                    last_analysis_results = analysis_results
                    
                    # 检测告警情况并创建告警记录
                    # 获取检测配置
                    detection_config = DetectionService.get_detection_config()
                    
                    # 检查是否有已启用的检测结果
                    has_enabled_detection = (
                        (detection_config.get('enableFire', True) and (fire_detected or smoke_detected)) or 
                        (detection_config.get('enableHelmet', True) and helmet_detected) or 
                        (detection_config.get('enableVest', True) and vest_detected) or 
                        (detection_config.get('enableVehicleIntrusion', True) and (intrusion_detected or person_count > 0 or vehicle_count > 0))
                    )
                    
                    if write_to_database and has_enabled_detection:
                        # 将告警处理放到后台执行，避免阻塞视频流
                        async def process_alarm():
                            # 创建新的数据库会话，避免使用可能已关闭的会话
                            from app.config.database import SessionLocal
                            alarm_db = SessionLocal()
                            try:
                                # 保存告警截图
                                snapshot_url = ""
                                try:
                                    snapshot_url = StorageService.upload_alarm_snapshot(frame_cv, camera_id)
                                    logger.info(f"告警截图上传成功: {snapshot_url}")
                                except Exception as e:
                                    logger.error(f"上传告警截图失败: {str(e)}")
                                    snapshot_url = ""

                                # 确定告警类型（优先检测已启用的）
                                alarm_type = 0  # 默认为安全规范
                                if detection_config.get('enableFire', True) and (fire_detected or smoke_detected):
                                    alarm_type = 2  # 火警
                                elif detection_config.get('enableVehicleIntrusion', True) and (person_count > 0 or vehicle_count > 0):
                                    alarm_type = 1  # 区域入侵
                                elif (detection_config.get('enableHelmet', True) and helmet_detected) or (detection_config.get('enableVest', True) and vest_detected):
                                    alarm_type = 0  # 安全规范

                                # 创建告警记录（无论是否有截图都创建）
                                try:
                                    alarm = create_alarm(alarm_db, camera_id, alarm_type, 0, datetime.now(pytz.timezone('Asia/Shanghai')), snapshot_url if snapshot_url else "")
                                    logger.info(f"告警记录创建成功: alarm_id={alarm.alarm_id}, camera_id={camera_id}, alarm_type={alarm_type}, snapshot={snapshot_url}")
                                    # 广播告警
                                    sync_broadcast_alarm(alarm)
                                except Exception as e:
                                    logger.error(f"创建告警记录失败: {str(e)}")
                                    import traceback
                                    logger.error(traceback.format_exc())
                            finally:
                                alarm_db.close()

                        # 创建后台任务处理告警
                        asyncio.create_task(process_alarm())
                
                # 确保 analysis_results 有值
                if not analysis_results:
                    analysis_results = []
                    if mode in [1, 2]:
                        analysis_results.extend([
                            {"label": "未戴安全帽", "value": "未检测到"},
                            {"label": "未穿反光衣", "value": "未检测到"}
                        ])
                    if mode in [1, 4]:
                        analysis_results.extend([
                            {"label": "火焰检测", "value": "未检测到"},
                            {"label": "烟雾检测", "value": "未检测到"}
                        ])
                    if mode in [1, 3]:
                        analysis_results.extend([
                            {"label": "人员检测", "value": "0人"},
                            {"label": "车辆检测", "value": "0辆"},
                            {"label": "区域入侵", "value": "未检测到"}
                        ])
                    if mode in [1, 5]:
                        analysis_results.append({
                            "label": "害虫检测", "value": "未检测到"
                        })
                    if mode in [1, 6]:
                        analysis_results.append({
                            "label": "作物长势异常", "value": "未检测到"
                        })
                    if mode in [1, 7]:
                        analysis_results.append({
                            "label": "柑橘检测状态",
                            "value": "[ERROR] 未检测到橘子"
                        })
                
                frame_count += 1

                # 发送到WebSocket
                try:
                    await websocket.send_json({
                        "image": f"data:image/jpeg;base64,{img_base64}",
                        "timestamp": datetime.now(pytz.timezone('Asia/Shanghai')).isoformat(),
                        "results": analysis_results
                    })
                    logger.debug(f"分析结果已发送: {len(analysis_results)}项检测结果")
                except Exception as e:
                    logger.error(f"发送WebSocket消息失败: {str(e)}")
                    # 发送失败，说明客户端已断开连接，跳出循环
                    break

                # 控制帧率（约20fps）
                await asyncio.sleep(0.05)

        except WebSocketDisconnect:
            # 客户端断开连接
            pass
        except Exception as e:
            try:
                await websocket.send_json({"error": f"错误: {str(e)}"})
            except:
                pass
        finally:
            if cap:
                cap.release()

    @staticmethod
    async def analyze_single_frame(image_base64: str, analysis_mode: str, db: Session):
        """
        分析单个视频帧，用于本地视频分析功能
        
        Args:
            image_base64 (str): Base64编码的图像
            analysis_mode (str): 分析模式
            db (Session): 数据库会话
        
        Returns:
            dict: 分析结果
        """
        logger = get_logger()
        try:
            # 解码Base64图像
            import base64
            from io import BytesIO
            import numpy as np
            
            # 移除data:image/jpeg;base64,前缀
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',')[1]
            
            # 解码Base64
            image_data = base64.b64decode(image_base64)
            image_np = np.frombuffer(image_data, dtype=np.uint8)
            frame_cv = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
            
            if frame_cv is None:
                return {"error": "无法解码图像"}

            # 初始化检测结果
            helmet_detected = False
            vest_detected = False
            fire_detected = False
            smoke_detected = False
            person_count = 0
            vehicle_count = 0
            intrusion_detected = False
            pest_detected = False
            growth_abnormal_detected = False
            citrus_detected = False
            citrus_predictions = []
            tomato_detected = False
            tomato_predictions = []
            apple_detected = False
            apple_predictions = []
            
            # 转换分析模式为整数
            mode = int(analysis_mode) if analysis_mode else 1
            
            # 模式1 = 全部，模式2=安全规范，模式3=区域入侵，模式4=火警，模式5=害虫检测，模式6=作物长势异常，模式7=果实成熟度
            
            # 检测安全帽（未戴安全帽）- 在线程中运行避免阻塞
            if mode in [1, 2]:
                try:
                    def detect_helmet():
                        result = DetectionService.helmet_model(frame_cv, imgsz=640)[0]
                        head_class_id = 0
                        confidence_threshold = 0.5
                        for box in result.boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            if class_id == head_class_id and confidence >= confidence_threshold:
                                return True
                        return False
                    helmet_detected = await asyncio.to_thread(detect_helmet)
                except Exception as e:
                    logger.error(f"安全帽检测失败: {str(e)}")
            
            # 检测反光衣（未穿反光衣）- 在线程中运行避免阻塞
            if mode in [1, 2]:
                try:
                    def detect_vest():
                        result = DetectionService.vest_model(frame_cv, imgsz=640)[0]
                        no_vest_class_id = 0
                        confidence_threshold = 0.5
                        for box in result.boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            if class_id == no_vest_class_id and confidence >= confidence_threshold:
                                return True
                        return False
                    vest_detected = await asyncio.to_thread(detect_vest)
                except Exception as e:
                    logger.error(f"反光衣检测失败: {str(e)}")
            
            # 检测火焰和烟雾 - 在线程中运行避免阻塞
            if mode in [1, 4]:
                try:
                    def detect_fire_smoke():
                        # 增加推理尺寸并设置较低的置信度阈值，提高火灾检测灵敏度
                        result = DetectionService.fire_smoke_model(frame_cv, imgsz=960, conf=0.2)[0]  # 增加推理尺寸，降低置信度阈值
                        fire_detected = False
                        smoke_detected = False
                        confidence_threshold = 0.2  # 降低置信度阈值以提高灵敏度
                        for box in result.boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            if confidence >= confidence_threshold:
                                if class_id == 0:
                                    fire_detected = True
                                elif class_id == 1:
                                    smoke_detected = True
                        return fire_detected, smoke_detected
                    fire_detected, smoke_detected = await asyncio.to_thread(detect_fire_smoke)
                except Exception as e:
                    logger.error(f"火焰烟雾检测失败: {str(e)}")
            
            # 检测人员和车辆 - 在线程中运行避免阻塞
            if mode in [1, 3]:
                try:
                    def detect_person_vehicle():
                        # 增加推理尺寸并降低置信度阈值，提高人员检测的准确性
                        result = DetectionService.person_vehicle_model(frame_cv, classes=[0,1,2,3,4,5,6,7], imgsz=960)[0]  # 增加推理尺寸
                        person_count = 0
                        vehicle_count = 0
                        confidence_threshold = 0.3  # 降低置信度阈值以提高检测灵敏度
                        for box in result.boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            if confidence >= confidence_threshold:
                                if class_id == 0:  # person
                                    person_count += 1
                                elif class_id in [1, 2, 3, 4, 5, 6, 7]:  # car, truck, bus, etc.
                                    vehicle_count += 1
                        return person_count, vehicle_count
                    person_count, vehicle_count = await asyncio.to_thread(detect_person_vehicle)
                except Exception as e:
                    logger.error(f"人员车辆检测失败: {str(e)}")
            
            # 检测害虫
            if mode in [1, 5]:
                try:
                    def detect_pest():
                        if DetectionService.pest_detector and DetectionService.pest_detector.model is not None:
                            # 使用害虫检测器
                            _, buffer = cv2.imencode('.jpg', frame_cv)
                            image_bytes = buffer.tobytes()
                            predictions, _ = DetectionService.pest_detector.detect_and_annotate(image_bytes)
                            return len(predictions) > 0
                        return False
                    pest_detected = await asyncio.to_thread(detect_pest)
                except Exception as e:
                    logger.error(f"害虫检测失败: {str(e)}")
            
            # 检测作物长势异常
            if mode in [1, 6]:
                try:
                    def detect_growth():
                        if DetectionService.crop_growth_model:
                            result = DetectionService.crop_growth_model(frame_cv, imgsz=640)[0]
                            if hasattr(result, 'boxes'):
                                return len(result.boxes) > 0
                        return False
                    growth_abnormal_detected = await asyncio.to_thread(detect_growth)
                except Exception as e:
                    logger.error(f"作物长势检测失败: {str(e)}")
            
            # 检测柑橘成熟度
            if mode in [1, 7]:
                try:
                    def detect_citrus():
                        if DetectionService.citrus_detector and DetectionService.citrus_detector.model is not None:
                            _, buffer = cv2.imencode('.jpg', frame_cv)
                            image_bytes = buffer.tobytes()
                            predictions, _ = DetectionService.citrus_detector.detect_and_annotate(image_bytes)
                            return len(predictions) > 0, predictions
                        return False, []
                    citrus_detected, citrus_predictions = await asyncio.to_thread(detect_citrus)
                except Exception as e:
                    logger.error(f"柑橘成熟度检测失败: {str(e)}")

            # 检测番茄成熟度
            if mode in [1, 9]:
                try:
                    def detect_tomato():
                        if DetectionService.tomato_detector and DetectionService.tomato_detector.model is not None:
                            _, buffer = cv2.imencode('.jpg', frame_cv)
                            image_bytes = buffer.tobytes()
                            predictions, _ = DetectionService.tomato_detector.detect_and_annotate(image_bytes)
                            return len(predictions) > 0, predictions
                        return False, []
                    tomato_detected, tomato_predictions = await asyncio.to_thread(detect_tomato)
                except Exception as e:
                    logger.error(f"番茄成熟度检测失败: {str(e)}")

            # 检测苹果成熟度
            if mode in [1, 10]:
                try:
                    def detect_apple():
                        if DetectionService.apple_detector and DetectionService.apple_detector.model is not None:
                            _, buffer = cv2.imencode('.jpg', frame_cv)
                            image_bytes = buffer.tobytes()
                            predictions, _ = DetectionService.apple_detector.detect_and_annotate(image_bytes)
                            return len(predictions) > 0, predictions
                        logger.warning(f"[WARN] 苹果检测器未加载或模型为None")
                        return False, []
                    apple_detected, apple_predictions = await asyncio.to_thread(detect_apple)
                except Exception as e:
                    logger.error(f"苹果成熟度检测失败: {str(e)}")

            # 简单的区域入侵检测（如果检测到人员或车辆，就认为有入侵）
            intrusion_detected = person_count > 0 or vehicle_count > 0
            
            # 生成分析结果
            analysis_results = []
            
            # 获取检测配置
            detection_config = DetectionService.get_detection_config()
            
            # 根据分析模式添加对应的检测结果
            if mode in [1, 2]:
                if detection_config.get('enableHelmet', True) or detection_config.get('enableVest', True):
                    if detection_config.get('enableHelmet', True):
                        analysis_results.append({"label": "未戴安全帽", "value": "未检测到" if not helmet_detected else "检测到"})
                    if detection_config.get('enableVest', True):
                        analysis_results.append({"label": "未穿反光衣", "value": "未检测到" if not vest_detected else "检测到"})
            
            if mode in [1, 4]:
                analysis_results.extend([
                    {"label": "火焰检测", "value": "未检测到" if not fire_detected else "检测到"},
                    {"label": "烟雾检测", "value": "未检测到" if not smoke_detected else "检测到"}
                ])
            
            if mode in [1, 3]:
                if detection_config.get('enableVehicleIntrusion', True):
                    analysis_results.extend([
                        {"label": "人员检测", "value": f"{person_count}人"},
                        {"label": "车辆检测", "value": f"{vehicle_count}辆"},
                        {"label": "区域入侵", "value": "未检测到" if not intrusion_detected else "检测到"}
                    ])
            
            if mode in [1, 5]:
                analysis_results.append({
                    "label": "害虫检测", "value": "未检测到" if not pest_detected else "检测到"
                })
            
            if mode in [1, 6]:
                analysis_results.append({
                    "label": "作物长势异常", "value": "未检测到" if not growth_abnormal_detected else "检测到"
                })
            
            if mode in [1, 7]:
                # 使用柑橘跟踪器进行去重
                citrus_tracker = CameraInfoService._get_citrus_tracker()
                citrus_tracker_summary = citrus_tracker.update(citrus_predictions)
                
                # 获取跟踪器统计（去重后的准确数据）
                tracked_total = citrus_tracker_summary['total']
                tracked_unripe = citrus_tracker_summary['unripe']
                tracked_ripe = citrus_tracker_summary['ripe']
                tracked_rotten = citrus_tracker_summary['rotten']
                tracked_max_maturity = citrus_tracker_summary['max_maturity']
                
                # 显示当前帧检测到的柑橘数量
                current_frame_count = len(citrus_predictions)
                
                # 首先显示检测状态：有没有检测到橘子
                if citrus_detected and current_frame_count > 0:
                    analysis_results.append({
                        "label": "柑橘检测状态",
                        "value": f"[OK] 本帧检测{current_frame_count}个 | 累计追踪{tracked_total}个"
                    })
                    
                    # 使用跟踪器的去重统计
                    max_maturity = tracked_max_maturity
                    unripe_count = tracked_unripe
                    ripe_count = tracked_ripe
                    rotten_count = tracked_rotten
                    
                    # 显示更丰富的成熟度信息
                    if max_maturity >= 80:
                        ripeness_status = "已成熟"
                    elif max_maturity >= 55:
                        ripeness_status = "转色中"
                    else:
                        ripeness_status = "未成熟"
                    
                    # 详细统计
                    status_detail = []
                    if unripe_count > 0:
                        status_detail.append(f"未成熟:{unripe_count}")
                    if ripe_count > 0:
                        status_detail.append(f"成熟:{ripe_count}")
                    if rotten_count > 0:
                        status_detail.append(f"腐烂:{rotten_count}")
                    
                    analysis_results.append({
                        "label": "柑橘成熟度分析",
                        "value": f"{ripeness_status} (最高成熟度:{max_maturity}%) - {', '.join(status_detail)}"
                    })
                else:
                    analysis_results.append({
                        "label": "柑橘检测状态",
                        "value": "[ERROR] 未检测到橘子"
                    })

            if mode in [1, 9]:
                # 使用番茄跟踪器进行去重
                tracker = CameraInfoService._get_tomato_tracker()
                new_tomatoes, all_tracked = tracker.update(tomato_predictions)
                
                # 获取跟踪器统计（去重后的准确数据）
                tracker_summary = tracker.get_summary()
                tracked_total = tracker_summary['total']
                tracked_unripe = tracker_summary['unripe']
                tracked_ripe = tracker_summary['ripe']
                tracked_overripe = tracker_summary['overripe']
                tracked_max_maturity = tracker_summary['max_maturity']
                
                # 显示当前帧检测到的番茄数量（去重前）
                current_frame_count = len(tomato_predictions)
                tracked_historical_total = tracker_summary.get('historical_total', tracked_total)

                # 调试：打印原始预测数据
                logger.info(f"[DEBUG] 番茄跟踪器结果: total={tracked_total}, historical_total={tracked_historical_total}, unripe={tracked_unripe}, ripe={tracked_ripe}, overripe={tracked_overripe}, max_maturity={tracked_max_maturity}")
                if tomato_predictions:
                    for i, pred in enumerate(tomato_predictions[:3]):  # 只打印前3个
                        logger.info(f"[DEBUG] 番茄预测{i}: class={pred.get('class')}, maturity={pred.get('maturity')}, conf={pred.get('confidence')}")

                # 使用跟踪器的去重统计
                max_maturity = tracked_max_maturity
                unripe_count = tracked_unripe
                ripe_count = tracked_ripe
                overripe_count = tracked_overripe

                # 显示更丰富的成熟度信息
                if max_maturity >= 80:
                    ripeness_status = "已成熟"
                elif max_maturity >= 55:
                    ripeness_status = "转色中"
                else:
                    ripeness_status = "未成熟"

                # 详细统计
                status_detail = []
                if unripe_count > 0:
                    status_detail.append(f"未成熟:{unripe_count}")
                if ripe_count > 0:
                    status_detail.append(f"成熟:{ripe_count}")
                if overripe_count > 0:
                    status_detail.append(f"过熟:{overripe_count}")

                # 判断有没有检测到番茄（包括当前帧和历史）
                has_tomatoes = (tomato_detected and current_frame_count > 0) or tracked_historical_total > 0 or max_maturity > 0

                if has_tomatoes:
                    # 有番茄（当前帧检测到或历史有记录）
                    if tomato_detected and current_frame_count > 0:
                        analysis_results.append({
                            "label": "番茄检测状态",
                            "value": f"[OK] 本帧检测{current_frame_count}个 | 累计追踪{tracked_historical_total}个"
                        })
                    else:
                        # 当前帧没检测到，但历史有
                        analysis_results.append({
                            "label": "番茄检测状态",
                            "value": f"[OK] 累计追踪{tracked_historical_total}个 (当前帧无番茄)"
                        })

                    analysis_results.append({
                        "label": "番茄成熟度分析",
                        "value": f"{ripeness_status} (最高成熟度:{max_maturity}%) - {', '.join(status_detail) if status_detail else '无详细分类'}"
                    })
                else:
                    # 真的没有检测到任何番茄
                    analysis_results.append({
                        "label": "番茄检测状态",
                        "value": "[ERROR] 未检测到番茄"
                    })

            # 苹果成熟度检测结果生成
            if mode in [1, 10]:
                # 使用苹果跟踪器进行去重
                apple_tracker = CameraInfoService._get_apple_tracker()
                apple_tracker_summary = apple_tracker.update(apple_predictions)

                # 获取跟踪器统计（去重后的准确数据）
                tracked_total = apple_tracker_summary['total']
                tracked_stage_20 = apple_tracker_summary.get('stage_20', 0)
                tracked_stage_40 = apple_tracker_summary.get('stage_40', 0)
                tracked_stage_60 = apple_tracker_summary.get('stage_60', 0)
                tracked_stage_80 = apple_tracker_summary.get('stage_80', 0)
                tracked_stage_100 = apple_tracker_summary.get('stage_100', 0)
                tracked_max_maturity = apple_tracker_summary['max_maturity']

                # 显示当前帧检测到的苹果数量（去重前）
                current_frame_count = len(apple_predictions)
                tracked_historical_total = apple_tracker_summary.get('historical_total', tracked_total)

                # 调试：打印苹果检测数据
                logger.info(f"[DEBUG] 苹果跟踪器结果: total={tracked_total}, historical_total={tracked_historical_total}, stage_20={tracked_stage_20}, stage_40={tracked_stage_40}, stage_60={tracked_stage_60}, stage_80={tracked_stage_80}, stage_100={tracked_stage_100}, max_maturity={tracked_max_maturity}")
                logger.info(f"[DEBUG] 苹果检测状态: apple_detected={apple_detected}, current_frame_count={current_frame_count}")
                if apple_predictions:
                    for i, pred in enumerate(apple_predictions[:3]):  # 只打印前3个
                        logger.info(f"[DEBUG] 苹果预测{i}: class={pred.get('class')}, maturity={pred.get('maturity')}, conf={pred.get('confidence')}")

                # 使用跟踪器的去重统计
                max_maturity = tracked_max_maturity

                # 显示更丰富的成熟度信息
                if max_maturity >= 100:
                    ripeness_status = "完全成熟"
                elif max_maturity >= 80:
                    ripeness_status = "即将成熟"
                elif max_maturity >= 60:
                    ripeness_status = "中期成熟"
                elif max_maturity >= 40:
                    ripeness_status = "早期发育"
                else:
                    ripeness_status = "仍在生长"

                # 详细统计
                status_detail = []
                if tracked_stage_20 > 0:
                    status_detail.append(f"20%:{tracked_stage_20}")
                if tracked_stage_40 > 0:
                    status_detail.append(f"40%:{tracked_stage_40}")
                if tracked_stage_60 > 0:
                    status_detail.append(f"60%:{tracked_stage_60}")
                if tracked_stage_80 > 0:
                    status_detail.append(f"80%:{tracked_stage_80}")
                if tracked_stage_100 > 0:
                    status_detail.append(f"100%:{tracked_stage_100}")

                # 判断有没有检测到苹果（包括当前帧和历史）
                has_apples = (apple_detected and current_frame_count > 0) or tracked_historical_total > 0 or max_maturity > 0

                if has_apples:
                    # 有苹果（当前帧检测到或历史有记录）
                    if apple_detected and current_frame_count > 0:
                        analysis_results.append({
                            "label": "苹果检测状态",
                            "value": f"[OK] 本帧检测{current_frame_count}个 | 累计追踪{tracked_historical_total}个"
                        })
                    else:
                        # 当前帧没检测到，但历史有
                        analysis_results.append({
                            "label": "苹果检测状态",
                            "value": f"[OK] 累计追踪{tracked_historical_total}个 (当前帧无苹果)"
                        })

                    analysis_results.append({
                        "label": "苹果成熟度分析",
                        "value": f"{ripeness_status} (最高成熟度:{max_maturity}%) - {', '.join(status_detail) if status_detail else '无详细分类'}"
                    })
                else:
                    # 真的没有检测到任何苹果
                    analysis_results.append({
                        "label": "苹果检测状态",
                        "value": "[ERROR] 未检测到苹果"
                    })

            # 直接返回原始结果
            return {"results": analysis_results}
        except Exception as e:
            logger.error(f"分析单个视频帧失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"分析失败: {str(e)}"}