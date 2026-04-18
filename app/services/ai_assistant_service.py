"""AI智能问答助手服务 - 基于腾讯混元大模型和历史数据"""
import os
import json
import httpx
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.utils.logger import get_logger
from app.objects.alarm_case import AlarmCase

load_dotenv()
logger = get_logger()


class AIAssistantService:
    """AI智能问答助手服务 - 集成腾讯混元大模型"""

    HUNYUAN_API_KEY = os.getenv("HUNYUAN_API_KEY", "")
    HUNYUAN_MODEL = os.getenv("HUNYUAN_MODEL", "hunyuan-lite")
    HUNYUAN_API_URL = "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"

    @classmethod
    def get_system_context(cls, db: Session) -> str:
        """构建系统上下文，包含当前园区安全数据"""
        try:
            from app.DB_models.alarm_db import AlarmDB

            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=7)
            month_start = today_start.replace(day=1)

            today_count = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= today_start
            ).scalar() or 0

            week_count = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= week_start
            ).scalar() or 0

            month_count = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= month_start
            ).scalar() or 0

            total_count = db.query(func.count(AlarmDB.alarm_id)).scalar() or 0

            context = f"""你是园区智能安防系统的AI助手。以下是当前系统的数据概况：

【实时数据】
- 今日告警数：{today_count}次
- 本周告警数：{week_count}次
- 本月告警数：{month_count}次
- 累计告警数：{total_count}次

【告警类型说明】
- 类型0：安全规范违规（未戴安全帽、未穿反光衣）
- 类型1：区域入侵（人员、车辆进入禁止区域）
- 类型2：火警隐患（火焰、烟雾）

【告警状态说明】
- 状态0：未处理
- 状态1：处理中
- 状态2：已解决
- 状态3：误报

请根据这些数据回答用户的问题。如果用户的问题与数据相关，请提供具体的分析和建议。如果问题超出你的能力范围，请诚实告知。"""

            return context

        except Exception as e:
            logger.error(f"构建系统上下文失败：{str(e)}")
            return "你是园区智能安防系统的AI助手。请根据用户的问题提供专业回答。"

    @classmethod
    def handle_question(cls, question: str, db: Session) -> Dict:
        """
        处理用户问题，优先使用腾讯混元API，失败时回退到关键词匹配
        :param question: 用户问题
        :param db: 数据库会话
        :return: 包含回答的字典
        """
        try:
            if cls.HUNYUAN_API_KEY:
                return cls._ask_hunyuan(question, db)
            else:
                logger.warning("腾讯混元API密钥未配置，使用本地关键词匹配")
                return cls._ask_local(question, db)
        except Exception as e:
            logger.error(f"AI问答处理失败：{str(e)}")
            return {
                "answer": f"抱歉，处理问题时出现错误：{str(e)}",
                "data": None
            }

    @classmethod
    def _ask_hunyuan(cls, question: str, db: Session) -> Dict:
        """使用腾讯混元大模型回答问题"""
        try:
            system_context = cls.get_system_context(db)

            headers = {
                "Authorization": f"Bearer {cls.HUNYUAN_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": cls.HUNYUAN_MODEL,
                "messages": [
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }

            with httpx.Client(timeout=30) as client:
                response = client.post(cls.HUNYUAN_API_URL, json=payload, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                    # 尝试从回答中提取数据结构
                    data = None
                    if "【" in answer and "】" in answer:
                        data = {"source": "hunyuan"}

                    return {
                        "answer": answer,
                        "data": data,
                        "source": "hunyuan"
                    }
                else:
                    logger.error(f"腾讯混元API调用失败：{response.status_code}, {response.text}")
                    return cls._ask_local(question, db)

        except Exception as e:
            logger.error(f"调用腾讯混元API失败：{str(e)}")
            return cls._ask_local(question, db)

    @classmethod
    def _ask_local(cls, question: str, db: Session) -> Dict:
        """本地关键词匹配（回退方案）"""
        question = question.strip().lower()

        if any(kw in question for kw in ['告警', '报警', 'alarm']):
            if any(kw in question for kw in ['今天', '今日', 'today']):
                return cls._answer_today_alarms(db)
            elif any(kw in question for kw in ['总数', '多少', '统计', 'total']):
                return cls._answer_total_alarms(db)
            elif any(kw in question for kw in ['类型', '分类', 'type']):
                return cls._answer_alarm_types(db)
            elif any(kw in question for kw in ['趋势', 'trend']):
                return cls._answer_alarm_trend(db)
            else:
                return cls._answer_alarm_overview(db)

        elif any(kw in question for kw in ['区域', 'area', '地方', '地点']):
            if any(kw in question for kw in ['危险', '风险', 'risk', 'high']):
                return cls._answer_high_risk_areas(db)
            else:
                return cls._answer_area_overview(db)

        elif any(kw in question for kw in ['摄像头', 'camera', '设备']):
            return cls._answer_camera_status(db)

        elif any(kw in question for kw in ['安全', '安全分', 'score', '评分']):
            return cls._answer_safety_score(db)

        elif any(kw in question for kw in ['建议', '优化', 'improve', '怎么']):
            return cls._answer_suggestions(db)

        elif any(kw in question for kw in ['预测', 'forecast', '明天', '未来']):
            return cls._answer_prediction(db)

        elif any(kw in question for kw in ['你好', 'hello', 'hi', '帮助', 'help']):
            return cls._answer_help()

        else:
            return cls._answer_unknown(question)

    @classmethod
    def _answer_today_alarms(cls, db: Session) -> Dict:
        """回答今日告警情况"""
        try:
            from app.DB_models.alarm_db import AlarmDB
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            total = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= today_start
            ).scalar() or 0

            type_stats = db.query(
                AlarmDB.alarm_type,
                func.count(AlarmDB.alarm_id)
            ).filter(
                AlarmDB.alarm_time >= today_start
            ).group_by(AlarmDB.alarm_type).all()

            type_details = []
            for alarm_type, count in type_stats:
                type_details.append({
                    "type": AlarmCase.descs.get(alarm_type, "未知"),
                    "count": count
                })

            status_stats = db.query(
                AlarmDB.alarm_status,
                func.count(AlarmDB.alarm_id)
            ).filter(
                AlarmDB.alarm_time >= today_start
            ).group_by(AlarmDB.alarm_status).all()

            status_map = {0: "未处理", 1: "处理中", 2: "已解决", 3: "误报"}
            status_details = [{"status": status_map.get(s, "未知"), "count": c} for s, c in status_stats]

            answer = f"📊 今日告警统计\n\n"
            answer += f"• 今日告警总数：**{total}** 次\n\n"

            if type_details:
                answer += "• 按类型分布：\n"
                for item in type_details:
                    answer += f"  - {item['type']}：{item['count']}次\n"
                answer += "\n"

            if status_details:
                answer += "• 处理状态：\n"
                for item in status_details:
                    answer += f"  - {item['status']}：{item['count']}次\n"

            return {
                "answer": answer,
                "data": {
                    "total": total,
                    "by_type": type_details,
                    "by_status": status_details
                }
            }
        except Exception as e:
            logger.error(f"查询今日告警失败：{str(e)}")
            return {"answer": "抱歉，查询今日告警时出现错误，请稍后重试。", "data": None}

    @classmethod
    def _answer_total_alarms(cls, db: Session) -> Dict:
        """回答告警总数统计"""
        try:
            from app.DB_models.alarm_db import AlarmDB

            total = db.query(func.count(AlarmDB.alarm_id)).scalar() or 0

            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_total = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= month_start
            ).scalar() or 0

            last_month_start = (month_start - timedelta(days=1)).replace(day=1)
            last_month_total = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= last_month_start,
                AlarmDB.alarm_time < month_start
            ).scalar() or 0

            change_rate = 0
            if last_month_total > 0:
                change_rate = ((month_total - last_month_total) / last_month_total) * 100

            answer = f"📈 告警总数统计\n\n"
            answer += f"• 系统累计告警：**{total}** 次\n"
            answer += f"• 本月告警：**{month_total}** 次\n"
            answer += f"• 上月告警：**{last_month_total}** 次\n"

            if change_rate != 0:
                direction = "上升" if change_rate > 0 else "下降"
                answer += f"• 环比变化：**{abs(change_rate):.1f}% {direction}**\n"
            else:
                answer += f"• 环比变化：持平\n"

            return {
                "answer": answer,
                "data": {
                    "total": total,
                    "month_total": month_total,
                    "last_month_total": last_month_total,
                    "change_rate": round(change_rate, 2)
                }
            }
        except Exception as e:
            logger.error(f"查询告警总数失败：{str(e)}")
            return {"answer": "抱歉，查询告警总数时出现错误。", "data": None}

    @classmethod
    def _answer_alarm_types(cls, db: Session) -> Dict:
        """回答告警类型分布"""
        try:
            from app.DB_models.alarm_db import AlarmDB

            type_stats = db.query(
                AlarmDB.alarm_type,
                func.count(AlarmDB.alarm_id)
            ).group_by(AlarmDB.alarm_type).all()

            total = sum(count for _, count in type_stats)

            answer = f"🔍 告警类型分布\n\n"
            answer += f"系统共检测到以下告警类型：\n\n"

            for alarm_type, count in sorted(type_stats, key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0
                type_name = AlarmCase.descs.get(alarm_type, f"类型{alarm_type}")
                answer += f"• **{type_name}**：{count}次（{percentage:.1f}%）\n"

            answer += f"\n总计：**{total}** 次告警"

            return {
                "answer": answer,
                "data": {
                    "types": [
                        {"type": AlarmCase.descs.get(t, f"类型{t}"), "count": c}
                        for t, c in type_stats
                    ],
                    "total": total
                }
            }
        except Exception as e:
            logger.error(f"查询告警类型失败：{str(e)}")
            return {"answer": "抱歉，查询告警类型时出现错误。", "data": None}

    @classmethod
    def _answer_alarm_trend(cls, db: Session) -> Dict:
        """回答告警趋势"""
        try:
            from app.DB_models.alarm_db import AlarmDB

            today = datetime.now().date()
            trends = []

            for i in range(6, -1, -1):
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

            avg_daily = sum(t["count"] for t in trends) / 7 if trends else 0

            answer = f"📊 近7天告警趋势\n\n"
            for item in trends:
                bar = "█" * item["count"] if item["count"] > 0 else "░"
                answer += f"• {item['date']}：{item['count']}次 {bar}\n"

            answer += f"\n日均告警：**{avg_daily:.1f}** 次"

            return {
                "answer": answer,
                "data": {
                    "trends": trends,
                    "avg_daily": round(avg_daily, 2)
                }
            }
        except Exception as e:
            logger.error(f"查询告警趋势失败：{str(e)}")
            return {"answer": "抱歉，查询告警趋势时出现错误。", "data": None}

    @classmethod
    def _answer_alarm_overview(cls, db: Session) -> Dict:
        """回答告警概览"""
        return cls._answer_today_alarms(db)

    @classmethod
    def _answer_high_risk_areas(cls, db: Session) -> Dict:
        """回答高风险区域"""
        try:
            from app.DB_models.alarm_db import AlarmDB
            from app.DB_models.camera_info_db import CameraInfoDB
            from app.DB_models.park_area_db import ParkAreaDB

            area_stats = db.query(
                ParkAreaDB.area_name,
                func.count(AlarmDB.alarm_id)
            ).join(
                CameraInfoDB, CameraInfoDB.area_id == ParkAreaDB.area_id
            ).join(
                AlarmDB, AlarmDB.camera_id == CameraInfoDB.camera_id
            ).group_by(
                ParkAreaDB.area_name
            ).order_by(
                func.count(AlarmDB.alarm_id).desc()
            ).limit(5).all()

            answer = f"⚠️ 高风险区域排名\n\n"
            if area_stats:
                for i, (area_name, count) in enumerate(area_stats, 1):
                    risk_level = "🔴 高风险" if i <= 2 else "🟡 中风险"
                    answer += f"{i}. **{area_name}**：{count}次告警 {risk_level}\n"

                answer += f"\n建议加强对排名前列区域的巡查和管理。"
            else:
                answer = "暂无区域告警数据。"

            return {
                "answer": answer,
                "data": {
                    "areas": [{"name": n, "count": c} for n, c in area_stats]
                }
            }
        except Exception as e:
            logger.error(f"查询高风险区域失败：{str(e)}")
            return {"answer": "抱歉，查询区域风险时出现错误。", "data": None}

    @classmethod
    def _answer_area_overview(cls, db: Session) -> Dict:
        """回答区域概览"""
        return cls._answer_high_risk_areas(db)

    @classmethod
    def _answer_camera_status(cls, db: Session) -> Dict:
        """回答摄像头状态"""
        try:
            from app.DB_models.camera_info_db import CameraInfoDB

            total = db.query(func.count(CameraInfoDB.camera_id)).scalar() or 0

            status_stats = db.query(
                CameraInfoDB.camera_status,
                func.count(CameraInfoDB.camera_id)
            ).group_by(CameraInfoDB.camera_status).all()

            status_map = {
                0: "离线",
                1: "在线未分析",
                2: "在线分析中"
            }

            answer = f"📹 摄像头状态概览\n\n"
            answer += f"• 摄像头总数：**{total}** 个\n\n"

            for status, count in status_stats:
                status_name = status_map.get(status, "未知")
                icon = {"离线": "🔴", "在线未分析": "🟢", "在线分析中": "🔵"}.get(status_name, "⚪")
                answer += f"• {icon} {status_name}：{count}个\n"

            analyzing = sum(c for s, c in status_stats if s == 2)
            answer += f"\n• AI分析覆盖率：**{analyzing}/{total}**"

            return {
                "answer": answer,
                "data": {
                    "total": total,
                    "by_status": [
                        {"status": status_map.get(s, "未知"), "count": c}
                        for s, c in status_stats
                    ]
                }
            }
        except Exception as e:
            logger.error(f"查询摄像头状态失败：{str(e)}")
            return {"answer": "抱歉，查询摄像头状态时出现错误。", "data": None}

    @classmethod
    def _answer_safety_score(cls, db: Session) -> Dict:
        """回答安全评分"""
        try:
            from app.DB_models.alarm_db import AlarmDB

            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            today_alarms = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= today_start
            ).scalar() or 0

            base_score = 100
            deduction_per_alarm = 2
            score = max(0, base_score - today_alarms * deduction_per_alarm)

            if score >= 90:
                level = "优秀 🟢"
            elif score >= 70:
                level = "良好 🟡"
            elif score >= 50:
                level = "一般 🟠"
            else:
                level = "较差 🔴"

            answer = f"🛡️ 今日安全评分\n\n"
            answer += f"• 安全评分：**{score}** 分\n"
            answer += f"• 安全等级：**{level}**\n"
            answer += f"• 今日告警：**{today_alarms}** 次（每次扣{deduction_per_alarm}分）\n\n"

            if score < 70:
                answer += "⚠️ 建议加强安全巡查和管理！"
            else:
                answer += "✅ 当前安全状况良好，请继续保持！"

            return {
                "answer": answer,
                "data": {
                    "score": score,
                    "level": level,
                    "today_alarms": today_alarms
                }
            }
        except Exception as e:
            logger.error(f"计算安全评分失败：{str(e)}")
            return {"answer": "抱歉，计算安全评分时出现错误。", "data": None}

    @classmethod
    def _answer_suggestions(cls, db: Session) -> Dict:
        """回答优化建议"""
        try:
            from app.DB_models.alarm_db import AlarmDB
            from app.DB_models.camera_info_db import CameraInfoDB
            from app.DB_models.park_area_db import ParkAreaDB

            suggestions = []

            area_stats = db.query(
                ParkAreaDB.area_name,
                func.count(AlarmDB.alarm_id)
            ).join(
                CameraInfoDB, CameraInfoDB.area_id == ParkAreaDB.area_id
            ).join(
                AlarmDB, AlarmDB.camera_id == CameraInfoDB.camera_id
            ).group_by(
                ParkAreaDB.area_name
            ).order_by(
                func.count(AlarmDB.alarm_id).desc()
            ).limit(3).all()

            if area_stats:
                suggestions.append({
                    "type": "区域优化",
                    "suggestion": f"建议在 **{area_stats[0][0]}** 增加巡查频次，该区域告警数最多（{area_stats[0][1]}次）"
                })

            type_stats = db.query(
                AlarmDB.alarm_type,
                func.count(AlarmDB.alarm_id)
            ).group_by(AlarmDB.alarm_type).order_by(
                func.count(AlarmDB.alarm_id).desc()
            ).first()

            if type_stats:
                type_name = AlarmCase.descs.get(type_stats[0], "未知")
                suggestions.append({
                    "type": "安全培训",
                    "suggestion": f"针对 **{type_name}** 问题，建议开展专项安全培训"
                })

            unhandled = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_status == 0
            ).scalar() or 0

            if unhandled > 5:
                suggestions.append({
                    "type": "告警处理",
                    "suggestion": f"当前有 **{unhandled}** 条未处理告警，建议尽快处理"
                })

            answer = f"💡 AI优化建议\n\n"
            for i, item in enumerate(suggestions, 1):
                answer += f"{i}. 【{item['type']}】\n"
                answer += f"   {item['suggestion']}\n\n"

            if not suggestions:
                answer += "当前系统运行良好，暂无特殊建议。"

            return {
                "answer": answer,
                "data": {"suggestions": suggestions}
            }
        except Exception as e:
            logger.error(f"生成优化建议失败：{str(e)}")
            return {"answer": "抱歉，生成建议时出现错误。", "data": None}

    @classmethod
    def _answer_prediction(cls, db: Session) -> Dict:
        """回答预测分析"""
        try:
            from app.DB_models.alarm_db import AlarmDB

            week_ago = datetime.now() - timedelta(days=7)
            week_total = db.query(func.count(AlarmDB.alarm_id)).filter(
                AlarmDB.alarm_time >= week_ago
            ).scalar() or 0

            daily_avg = week_total / 7

            min_pred = int(daily_avg * 0.8)
            max_pred = int(daily_avg * 1.2)

            answer = f"🔮 AI预测分析\n\n"
            answer += f"基于近7天数据（日均 {daily_avg:.1f} 次告警）：\n\n"
            answer += f"• 预计明天告警数：**{min_pred}-{max_pred}** 次\n"
            answer += f"• 预计本周告警总数：**{int(daily_avg * 5)}-{int(daily_avg * 5 * 1.2)}** 次\n\n"

            if daily_avg > 10:
                answer += "⚠️ 告警频次较高，建议加强监控力量"
            elif daily_avg > 5:
                answer += "📊 告警频次中等，建议关注高风险时段"
            else:
                answer += "✅ 告警频次较低，建议继续保持"

            return {
                "answer": answer,
                "data": {
                    "daily_avg": round(daily_avg, 2),
                    "tomorrow_prediction": {"min": min_pred, "max": max_pred}
                }
            }
        except Exception as e:
            logger.error(f"生成预测分析失败：{str(e)}")
            return {"answer": "抱歉，生成预测时出现错误。", "data": None}

    @classmethod
    def _answer_help(cls) -> Dict:
        """回答帮助信息"""
        answer = f"🤖 AI助手使用指南\n\n"
        answer += "您可以问我以下问题：\n\n"
        answer += "**告警查询**\n"
        answer += "• 今天有多少告警？\n"
        answer += "• 告警总数统计\n"
        answer += "• 告警类型分布\n"
        answer += "• 近7天告警趋势\n\n"

        answer += "**区域分析**\n"
        answer += "• 哪个区域最危险？\n"
        answer += "• 区域告警统计\n\n"

        answer += "**设备管理**\n"
        answer += "• 摄像头状态如何？\n\n"

        answer += "**安全评分**\n"
        answer += "• 今日安全评分是多少？\n\n"

        answer += "**预测建议**\n"
        answer += "• 明天告警预测\n"
        answer += "• 有什么优化建议？\n\n"

        return {
            "answer": answer,
            "data": {
                "help_topics": [
                    "告警查询", "区域分析", "设备管理",
                    "安全评分", "预测建议"
                ]
            }
        }

    @classmethod
    def _answer_unknown(cls, question: str) -> Dict:
        """回答未知问题"""
        answer = f"抱歉，我暂时无法回答这个问题。\n\n"
        answer += f"您的问题：\"{question}\"\n\n"
        answer += "您可以尝试问我：\n"
        answer += "• 今日告警情况\n"
        answer += "• 哪个区域最危险\n"
        answer += "• 摄像头状态\n"
        answer += "• 安全评分\n"
        answer += "• 优化建议\n"

        return {"answer": answer, "data": None}
