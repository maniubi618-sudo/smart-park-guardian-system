import cv2
import sys

def test_camera(index):
    """测试指定索引的摄像头"""
    print(f"\n=== 测试摄像头索引 {index} ===")
    try:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            print(f"✓ 摄像头 {index} 打开成功")
            # 尝试读取一帧
            ret, frame = cap.read()
            if ret:
                print(f"✓ 成功读取图像，尺寸: {frame.shape}")
            else:
                print(f"✗ 无法读取图像")
            cap.release()
            return True
        else:
            print(f"✗ 摄像头 {index} 打开失败")
            return False
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        return False

def test_camera_with_backend(index, backend):
    """使用指定后端测试摄像头"""
    backend_name = "DirectShow" if backend == cv2.CAP_DSHOW else "MSMF"
    print(f"\n=== 测试摄像头索引 {index} 使用 {backend_name} 后端 ===")
    try:
        cap = cv2.VideoCapture(index, backend)
        if cap.isOpened():
            print(f"✓ 摄像头 {index} 使用 {backend_name} 打开成功")
            ret, frame = cap.read()
            if ret:
                print(f"✓ 成功读取图像，尺寸: {frame.shape}")
            else:
                print(f"✗ 无法读取图像")
            cap.release()
            return True
        else:
            print(f"✗ 摄像头 {index} 使用 {backend_name} 打开失败")
            return False
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        return False

if __name__ == "__main__":
    print("OpenCV 版本:", cv2.__version__)
    print("=" * 50)
    
    # 测试默认方式
    for i in range(3):
        test_camera(i)
    
    # 在 Windows 上使用 DirectShow 后端测试
    print("\n" + "=" * 50)
    print("尝试使用 DirectShow 后端...")
    for i in range(3):
        test_camera_with_backend(i, cv2.CAP_DSHOW)
    
    print("\n" + "=" * 50)
    print("测试完成")
