"""直通桥接：5175 检测 → 内存队列（实时）+ 数据库（持久化）→ 5174 拉取"""

import time, json, os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/bridge", tags=["bridge"])

_queue: List[dict] = []
_MAX_AGE_SEC = 600  # 内存保留 10 分钟
_MAX_ITEMS = 30
_PERSIST_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "bridge_persist.json")


class DetectionItem(BaseModel):
    disease_type: str
    crop: str
    confidence: float
    severity: str
    advice: str = ""
    source: str = "5175"
    snapshotDataUrl: Optional[str] = None
    snapshotUrl: Optional[str] = None


class DetectionPushRequest(BaseModel):
    detections: List[DetectionItem]


class DetectionPullResponse(BaseModel):
    items: List[dict]
    count: int


def _load_persist():
    """启动时从文件恢复"""
    global _queue
    try:
        if os.path.exists(_PERSIST_FILE):
            with open(_PERSIST_FILE) as f:
                saved = json.load(f)
            now = time.time()
            _queue = [item for item in saved if now - item.get("_ts", 0) < _MAX_AGE_SEC]
    except Exception:
        pass


def _save_persist():
    """保存到文件"""
    try:
        with open(_PERSIST_FILE, "w") as f:
            json.dump(_queue, f, ensure_ascii=False)
    except Exception:
        pass


def _cleanup():
    global _queue
    now = time.time()
    old_len = len(_queue)
    _queue = [item for item in _queue if now - item.get("_ts", 0) < _MAX_AGE_SEC]
    if len(_queue) > _MAX_ITEMS:
        _queue = _queue[-_MAX_ITEMS:]
    if len(_queue) != old_len:
        _save_persist()


# 启动时加载
_load_persist()


@router.post("/detection")
async def push_detection(payload: DetectionPushRequest):
    """5175 推入检测结果 → 内存 + 文件持久化"""
    now = time.time()
    added = 0
    for d in payload.detections:
        dup = False
        for existing in _queue:
            if (existing.get("diseaseType") == d.disease_type and
                existing.get("crop") == d.crop and
                now - existing.get("_ts", 0) < 30):
                if d.confidence > existing.get("confidence", 0):
                    existing["confidence"] = d.confidence
                    existing["severity"] = d.severity
                    existing["advice"] = d.advice
                    existing["_ts"] = now
                if d.snapshotDataUrl:
                    existing["snapshotDataUrl"] = d.snapshotDataUrl
                if d.snapshotUrl:
                    existing["snapshotUrl"] = d.snapshotUrl
                dup = True
                break
        if dup:
            continue
        item = {
            "id": f"bridge-{int(now * 1000)}-{d.disease_type}",
            "diseaseType": d.disease_type,
            "crop": d.crop,
            "confidence": d.confidence,
            "severity": d.severity,
            "advice": d.advice,
            "zoneId": "手机摄像头",
            "detectedAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
            "source": d.source,
            "_ts": now
        }
        if d.snapshotDataUrl:
            item["snapshotDataUrl"] = d.snapshotDataUrl
        if d.snapshotUrl:
            item["snapshotUrl"] = d.snapshotUrl
        _queue.append(item)
        added += 1

    if added > 0:
        _cleanup()
    return {"success": True, "queued": added}


@router.get("/detection/latest", response_model=DetectionPullResponse)
async def pull_latest():
    """5174 拉取内存中全部有效条目"""
    _cleanup()
    clean = [{k: v for k, v in item.items() if not k.startswith("_")} for item in _queue]
    return DetectionPullResponse(items=clean, count=len(clean))
