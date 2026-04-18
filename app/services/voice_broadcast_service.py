"""AI语音播报服务 - 用于告警语音提示"""
import platform
import subprocess
from app.utils.logger import get_logger

logger = get_logger()


class VoiceBroadcastService:
    """语音播报服务类"""

    @classmethod
    def broadcast_alarm(cls, alarm_desc: str, area_name: str = "") -> bool:
        """
        播报告警语音
        :param alarm_desc: 告警描述，如"未戴安全帽"
        :param area_name: 区域名称
        :return: 是否成功播报
        """
        try:
            # 构建完整的告警语音文本
            if area_name:
                voice_text = f"警告！{area_name}检测到{alarm_desc}！请立即处理！"
            else:
                voice_text = f"警告！检测到{alarm_desc}！请立即处理！"

            logger.info(f"准备语音播报：{voice_text}")

            # 根据操作系统选择语音播报方式
            system = platform.system()

            if system == "Windows":
                cls._windows_tts(voice_text)
            elif system == "Darwin":  # macOS
                cls._macos_tts(voice_text)
            elif system == "Linux":
                cls._linux_tts(voice_text)
            else:
                logger.warning(f"不支持的操作系统：{system}")
                return False

            return True

        except Exception as e:
            logger.error(f"语音播报失败：{str(e)}")
            return False

    @classmethod
    def _windows_tts(cls, text: str):
        """Windows系统TTS - 使用PowerShell"""
        try:
            # 使用PowerShell的SAPI.SpVoice进行语音播报
            ps_script = f'''
            Add-Type -AssemblyName System.Speech
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $synth.Speak("{text}")
            '''
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                timeout=30
            )
            logger.info("Windows语音播报完成")
        except Exception as e:
            logger.error(f"Windows TTS失败：{str(e)}")
            # 降级方案：使用系统提示音
            cls._play_system_beep()

    @classmethod
    def _macos_tts(cls, text: str):
        """macOS系统TTS"""
        try:
            subprocess.run(
                ["say", text],
                capture_output=True,
                timeout=30
            )
            logger.info("macOS语音播报完成")
        except Exception as e:
            logger.error(f"macOS TTS失败：{str(e)}")

    @classmethod
    def _linux_tts(cls, text: str):
        """Linux系统TTS"""
        try:
            # 尝试使用espeak
            subprocess.run(
                ["espeak", "-v", "zh", text],
                capture_output=True,
                timeout=30
            )
            logger.info("Linux语音播报完成")
        except Exception as e:
            logger.error(f"Linux TTS失败：{str(e)}")
            # 尝试使用aplay播放系统提示音
            cls._play_system_beep()

    @classmethod
    def _play_system_beep(cls):
        """播放系统提示音作为降级方案"""
        try:
            if platform.system() == "Windows":
                # Windows系统提示音
                subprocess.run(
                    ["powershell", "-Command", "[System.Media.SystemSounds]::Beep.Play()"],
                    capture_output=True,
                    timeout=5
                )
            else:
                # Linux/macOS使用bell
                print("\a")
            logger.info("系统提示音已播放")
        except Exception as e:
            logger.error(f"播放系统提示音失败：{str(e)}")

    @classmethod
    def get_alarm_voice_text(cls, alarm_type: int, camera_name: str = "") -> str:
        """
        根据告警类型获取语音文本
        :param alarm_type: 告警类型编码
        :param camera_name: 摄像头名称
        :return: 语音文本
        """
        alarm_type_map = {
            0: "未戴安全帽或未穿反光衣",
            1: "区域入侵",
            2: "火焰或烟雾",
        }
        alarm_desc = alarm_type_map.get(alarm_type, "异常情况")
        return cls.broadcast_alarm(alarm_desc, camera_name)
