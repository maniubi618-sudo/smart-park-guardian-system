# 测试IP地址获取函数
import socket
import os

def get_local_ip():
    try:
        # 不同操作系统的命令
        if os.name == 'nt':  # Windows
            import subprocess
            output = subprocess.check_output(['ipconfig', '/all'], universal_newlines=True)
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if 'IPv4 Address' in line or 'IPv4 地址' in line:
                    # 提取IP地址
                    parts = line.split(':')
                    if len(parts) > 1:
                        ip = parts[1].strip()
                        # 处理"(首选)"后缀
                        if '(首选)' in ip:
                            ip = ip.replace('(首选)', '').strip()
                        # 排除环回地址和169.254开头的自动专用IP
                        if ip != '127.0.0.1' and not ip.startswith('169.254.'):
                            # 优先选择192.168、10或172.16-31开头的私有IP
                            if ip.startswith('192.168.') or ip.startswith('10.') or (ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31):
                                return ip
        
        # 如果Windows命令失败或其他系统，使用原方法
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# 测试函数
if __name__ == "__main__":
    ip = get_local_ip()
    print(f"获取到的IP地址: {ip}")
    print(f"IP地址类型: {'私有IP' if (ip.startswith('192.168.') or ip.startswith('10.') or (ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31)) else '公网IP'}")
