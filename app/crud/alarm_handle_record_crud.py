from sqlalchemy.orm import Session
from app.DB_models.alarm_handle_record_db import AlarmHandleRecordDB
from app.DB_models.user_db import UserDB
from typing import Optional, List
from app.JSON_schemas.alarm_handle_record_pydantic import AlarmHandleRecordCreate


def get_alarm_handle_records(db: Session, alarm_id: int) -> List[dict]:
    """
    根据告警ID获取该告警的所有处理记录

    Args:
        db (Session): 数据库会话
        alarm_id (int): 告警ID

    Returns:
        List[dict]: 告警处理记录字典列表
    """
    # 联表查询，获取处理记录和处理人信息
    records = db.query(
        AlarmHandleRecordDB,
        UserDB.name.label('handle_user_name')
    ).outerjoin(
        UserDB, AlarmHandleRecordDB.handler_user_id == UserDB.user_id
    ).filter(
        AlarmHandleRecordDB.alarm_id == alarm_id
    ).all()
    
    # 转换为字典列表，确保字段名与前端一致
    result = []
    for record, handle_user_name in records:
        # 处理状态映射：0-标记误报(1)，1-派单处理(2)，2-标记已解决(3)
        alarm_status_map = {0: 1, 1: 2, 2: 3}
        alarm_status = alarm_status_map.get(record.handle_action, 0)
        
        result.append({
            'handle_record_id': record.handle_id,
            'handle_time': record.handle_time,
            'handle_user_name': handle_user_name or '未知',
            'alarm_status': alarm_status,
            'handle_remark': record.handle_content or ''
        })
    
    return result

def create_alarm_handle_record(db: Session, record_create: AlarmHandleRecordCreate) -> AlarmHandleRecordDB:
    """
    创建新的告警处理记录

    Args:
        db (Session): 数据库会话
        record_create (AlarmHandleRecordCreate): 告警处理记录创建数据

    Returns:
        AlarmHandleRecordDB: 新创建的告警处理记录对象
    """
    # 将Pydantic模型转换为数据库模型
    db_record = AlarmHandleRecordDB(**record_create.model_dump(exclude_unset=True))

    # 添加到数据库
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return db_record