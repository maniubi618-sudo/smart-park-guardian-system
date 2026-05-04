from datetime import datetime
import pytz


class AlarmCase:
    # 告警类型描述
    descs=[
        "安全规范问题(未戴安全帽、未穿反光衣)", 
        "区域入侵(人/车辆)", 
        "火警(火焰、烟雾)",
        "害虫检测",
        "作物长势异常",
        "果实成熟度"
    ]
    # 告警类型描述+编码，对应AlarmDB中alarm_type字段
    desc_and_code={
        "安全规范":0, 
        "区域入侵":1, 
        "火警":2,
        "害虫检测":3,
        "作物长势异常":4,
        "果实成熟度":5
    }
    def __init__(self, code):
        self.code = code
        self.description = AlarmCase.desc_and_code.get(code, "未知的告警类型")
        self.time = datetime.now(pytz.timezone('Asia/Shanghai'))
