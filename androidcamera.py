from ppadb.client import Client as AdbClient
import cv2
import time

def connect_device():
    # 初始化ADB客户端
    client = AdbClient(host="127.0.0.1", port=5037)
    print("正在查找设备...")
    
    # 获取设备列表
    devices = client.devices()
    
    if len(devices) == 0:
        print("没有找到设备，请确保：")
        print("1. 手机已通过USB连接")
        print("2. 已开启USB调试")
        print("3. 已允许USB调试权限")
        return None
    
    print(f"找到 {len(devices)} 个设备")
    return devices[0]

def test_cameras():
    # 测试多个摄像头索引
    for i in range(10):  # 测试索引0-9
        print(f"\n尝试打开摄像头索引 {i}")
        cap = cv2.VideoCapture(i)
        
        if cap.isOpened():
            print(f"成功打开摄像头 {i}")
            # 读取一帧测试
            ret, frame = cap.read()
            if ret:
                print(f"摄像头 {i} 可以正常读取画面")
                cv2.imshow(f'Camera {i}', frame)
                cv2.waitKey(1000)  # 显示1秒
            else:
                print(f"摄像头 {i} 无法读取画面")
            cap.release()
        else:
            print(f"无法打开摄像头 {i}")
    
    cv2.destroyAllWindows()

def show_camera(camera_index):
    print(f"尝试打开摄像头 {camera_index}")
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"无法打开摄像头 {camera_index}")
        return
    
    print("摄像头已打开，按 'q' 退出")
    
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow('Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print("无法获取画面")
            break
    
    cap.release()
    cv2.destroyAllWindows()

def main():
    try:
        # 确保已安装必要的包
        device = connect_device()
        if not device:
            return
        
        print("设备已连接")
        print(f"设备信息: {device.serial}")
        
        # 先测试所有可用摄像头
        print("正在测试可用摄像头...")
        test_cameras()
        
        # 让用户选择摄像头
        camera_index = int(input("\n请输入要使用的摄像头索引: "))
        show_camera(camera_index)
        
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    # 首先安装必要的包
    try:
        import ppadb
    except ImportError:
        print("正在安装 pure-python-adb...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'pure-python-adb'])
        print("pure-python-adb 安装完成")
    
    main()