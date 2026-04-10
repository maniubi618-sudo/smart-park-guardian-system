from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from app.DB_models.park_area_db import ParkAreaDB
from app.JSON_schemas.park_area_pydantic import ParkAreaCreate, ParkAreaUpdate


def get_park_area(db: Session, park_area_id: int) -> Optional[ParkAreaDB]:
    """
    根据ID获取园区区域信息

    Args:
        db (Session): 数据库会话
        park_area_id (int): 园区区域ID

    Returns:
        Optional[ParkAreaDB]: 园区区域信息或None
    """
    return db.query(ParkAreaDB).filter(ParkAreaDB.park_area_id == park_area_id).first()


def get_park_area_by_name(db: Session, park_area: str) -> Optional[ParkAreaDB]:
    """
    根据名称获取园区区域信息

    Args:
        db (Session): 数据库会话
        park_area (str): 园区区域名称

    Returns:
        Optional[ParkAreaDB]: 园区区域信息或None
    """
    return db.query(ParkAreaDB).filter(ParkAreaDB.park_area == park_area).first()


def get_park_areas_with_condition(
        db: Session,
        park_area: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
):
    """
    根据条件获取园区区域信息列表（支持分页）

    Args:
        db (Session): 数据库会话
        park_area (Optional[str]): 园区区域名称（模糊查询）
        skip (int): 跳过的记录数，默认为0
        limit (int): 限制返回的记录数，默认为10

    Returns:
        tuple: (总数, 园区区域信息列表)
    """
    query = db.query(ParkAreaDB)

    # 添加园区区域名称条件（模糊查询）
    if park_area:
        query = query.filter(ParkAreaDB.park_area.like(f"%{park_area}%"))

    return query.count(), query.offset(skip).limit(limit).all()


def create_park_area(db: Session, park_area: ParkAreaCreate) -> ParkAreaDB:
    """
    创建新的园区区域信息

    Args:
        db (Session): 数据库会话
        park_area (ParkAreaCreate): 园区区域创建数据

    Returns:
        ParkAreaDB: 新创建的园区区域信息
    """
    # 查询所有现有的园区区域ID
    existing_ids = db.query(ParkAreaDB.park_area_id).order_by(ParkAreaDB.park_area_id).all()
    existing_ids = [id[0] for id in existing_ids]
    
    # 查找最小的未使用ID
    new_id = 1
    if existing_ids:
        # 从1开始检查，找到第一个缺失的ID
        for i, id in enumerate(existing_ids, 1):
            if id != i:
                new_id = i
                break
        else:
            # 如果所有ID都是连续的，则使用最大ID+1
            new_id = existing_ids[-1] + 1
    
    # 将 Pydantic 模型转成 SQLAlchemy 模型，并设置新的ID
    db_park_area = ParkAreaDB(**park_area.model_dump(), park_area_id=new_id)
    # 提交到数据库
    db.add(db_park_area)
    db.commit()
    db.refresh(db_park_area)  # 刷新实例，获取数据库自动生成的 id 等字段
    return db_park_area


def update_park_area(
        db: Session,
        park_area_id: int,
        park_area_update: ParkAreaUpdate
) -> Optional[ParkAreaDB]:
    """
    根据 ID 修改园区区域信息

    Args:
        db (Session): 数据库会话
        park_area_id (int): 园区区域ID
        park_area_update (ParkAreaUpdate): 园区区域更新数据

    Returns:
        Optional[ParkAreaDB]: 更新后的园区区域信息或None（如果未找到）
    """
    # 先查询园区区域信息是否存在
    db_park_area = get_park_area(db, park_area_id)
    if not db_park_area:
        return None  # 园区区域信息不存在，返回 None

    # 将更新的字段赋值给数据库实例（只更新非 None 的字段）
    update_data = park_area_update.model_dump(exclude_unset=True)  # 排除未传的字段
    for key, value in update_data.items():
        setattr(db_park_area, key, value)

    # 更新时间自动更新
    db_park_area.update_time = datetime.now()

    # 提交修改
    db.commit()
    db.refresh(db_park_area)
    return db_park_area


def delete_park_areas(db: Session, park_area_ids: List[int]) -> int:
    """
    批量删除园区区域信息

    Args:
        db (Session): 数据库会话
        park_area_ids (List[int]): 园区区域ID列表

    Returns:
        int: 成功删除的记录数
    """
    # 查询存在的园区区域信息
    db_park_areas = db.query(ParkAreaDB).filter(
        ParkAreaDB.park_area_id.in_(park_area_ids)
    ).all()

    # 获取实际存在的记录数量
    deleted_count = len(db_park_areas)

    # 批量删除
    for db_park_area in db_park_areas:
        db.delete(db_park_area)

    # 提交事务
    db.commit()

    return deleted_count