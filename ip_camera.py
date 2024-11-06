import os
from ppadb.client import Client as AdbClient

def setup_ip_webcam():
    try:
        # 连接ADB
        client = AdbClient(host="127.0.0.1", port=5037)
        device = client.devices()[0]
        
        print("检查IP Webcam是否已安装...")
        result = device.shell('pm list packages | grep webcam')
        
        if not result:
            print("IP Webcam未安装，请按以下步骤操作：")
            print("1. 在手机上打开应用商店")
            print("2. 搜索并安装 'IP Webcam'")
            print("3. 安装完成后手动授予相机权限")
            
            # 等待用户确认
            input("完成安装后按回车继续...")
        
        # 检查IP Webcam权限
        print("\n检查IP Webcam权限...")
        perms = device.shell('dumpsys package ip.webcam | grep permission')
        print(perms)
        
        # 获取手机IP地址
        print("\n获取手机IP地址...")
        ip_info = device.shell('ip addr show wlan0')
        print(ip_info)
        
        print("\n请确保：")
        print("1. 手机和电脑在同一WiFi网络")
        print("2. 已打开IP Webcam应用")
        print("3. 在应用中点击'Start server'")
        
        # 让用户输入IP地址
        ip = input("\n请输入手机IP地址: ")
        port = input("请输入端口号（默认8080）: ") or "8080"
        
        return f"http://{ip}:{port}/video"
        
    except Exception as e:
        print(f"设置过程出错: {e}")
        return None

def test_camera_connection(url):
    import cv2
    print(f"\n测试连接: {url}")
    
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("无法连接摄像头")
        return False
    
    print("连接成功！按 'q' 退出预览")
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow('IP Camera Test', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print("无法获取画面")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return True

if __name__ == "__main__":
    print("开始设置IP摄像头...")
    url = setup_ip_webcam()
    
    if url:
        test_camera_connection(url)