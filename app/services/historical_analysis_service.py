"""历史数据智能分析服务"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.utils.logger import get_logger
from app.objects.alarm_case import AlarmCase

logger = get_logger()


class HistoricalAnalysisService:
    """历史数据智能分析服务"""

    @classmethod
    def get_alarm_statistics(cls, db: Session, days: int = 30) -> Dict:
        """
        获取告警统计分析
        :param db: 数据库会话
        :param days: 统计天数
        :return: 统计分析结果
        """
        try:
            from app.DB_models.alarm_db import AlarmDB

            start_date = datetime.now() - timedelta(days=days)

            # 基础统计
            total_alarms = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= start_date
            ).scalar() or 0

            # 按类型统计
            type_stats = db.query(
                AlarmDB.alarm_type,
                func.count(AlarmDB.alarm_id)
            ).filter(
                AlarmDB.alarm_time >= start_date
            ).group_by(AlarmDB.alarm_type).all()

            type_breakdown = []
            for alarm_type, count in type_stats:
                type_breakdown.append({
                    "alarm_type": alarm_type,
                    "alarm_type_desc": AlarmCase.descs.get(alarm_type, f"类型{alarm_type}"),
                    "count": count,
                    "percentage": round((count / total_alarms * 100) if total_alarms > 0 else 0, 2)
                })

            # 按状态统计
            status_stats = db.query(
                AlarmDB.alarm_status,
                func.count(AlarmDB.alarm_id)
            ).filter(
                AlarmDB.alarm_time >= start_date
            ).group_by(AlarmDB.alarm_status).all()

            status_map = {0: "未处理", 1: "处理中", 2: "已解决", 3: "误报"}
            status_breakdown = [{"status": status_map.get(s, "未知"), "count": c} for s, c in status_stats]

            # 日均告警数
            daily_avg = total_alarms / days if days > 0 else 0

            return {
                "success": True,
                "data": {
                    "period_days": days,
                    "total_alarms": total_alarms,
                    "daily_average": round(daily_avg, 2),
                    "by_type": type_breakdown,
                    "by_status": status_breakdown,
                    "analysis": cls._generate_analysis(type_breakdown, total_alarms, days)
                }
            }
        except Exception as e:
            logger.error(f"获取告警统计失败：{str(e)}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_daily_trend(cls, db: Session, days: int = 30) -> Dict:
        """
        获取每日告警趋势
        :param db: 数据库会话
        :param days: 天数
        :return: 趋势数据
        """
        try:
            from app.DB_models.alarm_db import AlarmDB

            today = datetime.now().date()
            trends = []

            for i in range(days - 1, -1, -1):
                date = today - timedelta(days=i)
                day_start = datetime.combine(date, datetime.min.time())
                day_end = day_start + timedelta(days=1)

                count = db.query(func.count(AlarmDB.alarm_id)).filter(
                    AlarmDB.alarm_time >= day_start,
                    AlarmDB.alarm_time < day_end
                ).scalar() or 0

                trends.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "count": count
                })

            return {
                "success": True,
                "data": {
                    "trends": trends,
                    "max_day": max(trends, key=lambda x: x["count"]) if trends else None,
                    "min_day": min(trends, key=lambda x: x["count"]) if trends else None,
                    "total": sum(t["count"] for t in trends)
                }
            }
        except Exception as e:
            logger.error(f"获取每日趋势失败：{str(e)}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_hourly_distribution(cls, db: Session, days: int = 30) -> Dict:
        """
        获取24小时告警分布
        :param db: 数据库会话
        :param days: 统计天数
        :return: 小时分布数据
        """
        try:
            from app.DB_models.alarm_db import AlarmDB

            start_date = datetime.now() - timedelta(days=days)

            hourly_stats = db.query(
                extract('hour', AlarmDB.alarm_time).label('hour'),
                func.count(AlarmDB.alarm_id).label('count')
            ).filter(
                AlarmDB.alarm_time >= start_date
            ).group_by(
                extract('hour', AlarmDB.alarm_time)
            ).all()

            # 填充所有24小时
            hourly_map = {int(h): c for h, c in hourly_stats}
            hourly_distribution = [
                {"hour": h, "count": hourly_map.get(h, 0)}
                for h in range(24)
            ]

            # 找出高峰时段
            peak_hours = sorted(hourly_distribution, key=lambda x: x["count"], reverse=True)[:3]

            return {
                "success": True,
                "data": {
                    "hourly_distribution": hourly_distribution,
                    "peak_hours": peak_hours,
                    "analysis": cls._generate_hourly_analysis(peak_hours)
                }
            }
        except Exception as e:
            logger.error(f"获取小时分布失败：{str(e)}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_area_ranking(cls, db: Session, days: int = 30) -> Dict:
        """
        获取区域告警排名
        :param db: 数据库会话
        :param days: 统计天数
        :return: 区域排名
        """
        try:
            from app.DB_models.alarm_db import AlarmDB
            from app.DB_models.camera_info_db import CameraInfoDB
            from app.DB_models.park_area_db import ParkAreaDB

            start_date = datetime.now() - timedelta(days=days)

            area_stats = db.query(
                ParkAreaDB.area_id,
                ParkAreaDB.area_name,
                func.count(AlarmDB.alarm_id).label('alarm_count'),
                func.avg(AlarmDB.alarm_status == 0).label('unhandled_rate')
            ).join(
                CameraInfoDB, CameraInfoDB.area_id == ParkAreaDB.area_id
            ).join(
                AlarmDB, AlarmDB.camera_id == CameraInfoDB.camera_id
            ).filter(
                AlarmDB.alarm_time >= start_date
            ).group_by(
                ParkAreaDB.area_id,
                ParkAreaDB.area_name
            ).order_by(
                func.count(AlarmDB.alarm_id).desc()
            ).all()

            ranking = []
            for i, (area_id, area_name, alarm_count, unhandled_rate) in enumerate(area_stats, 1):
                if alarm_count > days * 2:
                    risk_level = "高风险"
                elif alarm_count > days:
                    risk_level = "中风险"
                else:
                    risk_level = "低风险"

                ranking.append({
                    "rank": i,
                    "area_id": area_id,
                    "area_name": area_name,
                    "alarm_count": alarm_count,
                    "daily_average": round(alarm_count / days, 2),
                    "unhandled_rate": round(float(unhandled_rate) * 100, 2) if unhandled_rate else 0,
                    "risk_level": risk_level
                })

            return {
                "success": True,
                "data": {
                    "ranking": ranking,
                    "total_areas": len(ranking),
                    "analysis": cls._generate_area_analysis(ranking)
                }
            }
        except Exception as e:
            logger.error(f"获取区域排名失败：{str(e)}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_prediction(cls, db: Session, predict_days: int = 7) -> Dict:
        """
        获取告警预测
        :param db: 数据库会话
        :param predict_days: 预测天数
        :return: 预测结果
        """
        try:
            from app.DB_models.alarm_db import AlarmDB

            # 获取最近30天数据
            days_for_analysis = 30
            start_date = datetime.now() - timedelta(days=days_for_analysis)

            total = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= start_date
            ).scalar() or 0

            daily_avg = total / days_for_analysis

            # 简单移动平均预测（基于均值和标准差）
            import math
            std_dev = math.sqrt(daily_avg) if daily_avg > 0 else 1

            predictions = []
            for i in range(1, predict_days + 1):
                pred_date = (datetime.now() + timedelta(days=i)).date()
                # 预测区间：均值 ± 1个标准差
                lower = max(0, int(daily_avg - std_dev))
                upper = int(daily_avg + std_dev)

                predictions.append({
                    "date": pred_date.strftime("%Y-%m-%d"),
                    "predicted_avg": round(daily_avg, 2),
                    "predicted_range": {"min": lower, "max": upper},
                    "confidence": "68%"
                })

            return {
                "success": True,
                "data": {
                    "predictions": predictions,
                    "daily_average": round(daily_avg, 2),
                    "based_on_days": days_for_analysis
                }
            }
        except Exception as e:
            logger.error(f"生成预测失败：{str(e)}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_comprehensive_report(cls, db: Session) -> Dict:
        """
        获取综合分析报告
        :param db: 数据库会话
        :return: 综合报告
        """
        stats = cls.get_alarm_statistics(db, 30)
        trend = cls.get_daily_trend(db, 30)
        hourly = cls.get_hourly_distribution(db, 30)
        area = cls.get_area_ranking(db, 30)
        prediction = cls.get_prediction(db, 7)

        # 计算安全评分
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            from app.DB_models.alarm_db import AlarmDB
            today_alarms = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= today_start
            ).scalar() or 0

            safety_score = max(0, 100 - today_alarms * 2)

            if safety_score >= 90:
                safety_level = "优秀"
            elif safety_score >= 70:
                safety_level = "良好"
            elif safety_score >= 50:
                safety_level = "一般"
            else:
                safety_level = "较差"
        except Exception:
            safety_score = 0
            safety_level = "未知"

        return {
            "success": True,
            "data": {
                "report_time": datetime.now().isoformat(),
                "safety_score": safety_score,
                "safety_level": safety_level,
                "statistics": stats.get("data", {}),
                "trend": trend.get("data", {}),
                "hourly_distribution": hourly.get("data", {}),
                "area_ranking": area.get("data", {}),
                "prediction": prediction.get("data", {})
            }
        }

    @classmethod
    def _generate_analysis(cls, type_breakdown: List[Dict], total: int, days: int) -> str:
        """生成统计分析文字"""
        if not type_breakdown:
            return "暂无告警数据"

        main_type = type_breakdown[0]
        daily_avg = total / days if days > 0 else 0

        analysis = f"近{days}天共发生{total}次告警，日均{daily_avg:.1f}次。"
        analysis += f"主要告警类型为：{main_type['alarm_type_desc']}（{main_type['count']}次，{main_type['percentage']}%）。"

        if daily_avg > 10:
            analysis += "告警频次较高，建议加强监控力量。"
        elif daily_avg > 5:
            analysis += "告警频次中等，建议关注高风险时段。"
        else:
            analysis += "告警频次较低，安全状况良好。"

        return analysis

    @classmethod
    def _generate_hourly_analysis(cls, peak_hours: List[Dict]) -> str:
        """生成小时分布分析"""
        if not peak_hours:
            return "暂无数据"

        hours_str = "、".join([f"{h['hour']}:00" for h in peak_hours])
        return f"告警高发时段为：{hours_str}，建议在这些时段加强巡查。"

    @classmethod
    def _generate_area_analysis(cls, ranking: List[Dict]) -> str:
        """生成区域分析"""
        if not ranking:
            return "暂无数据"

        high_risk = [r for r in ranking if r["risk_level"] == "高风险"]
        if high_risk:
            areas = "、".join([r["area_name"] for r in high_risk])
            return f"高风险区域：{areas}，建议优先整改。"
        return "当前无高风险区域，整体安全状况良好。"
