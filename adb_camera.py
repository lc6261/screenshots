
from ppadb.client import Client as AdbClient

def check_and_grant_camera_permissions():
    try:
        # 连接ADB
        client = AdbClient(host="127.0.0.1", port=5037)
        devices = client.devices()
        
        if not devices:
            print("没有找到设备")
            return
            
        device = devices[0]
        
        # 检查标准Android相机权限
        print("检查标准相机权限：")
        device.shell('pm list permissions -g | grep android.permission.CAMERA')
        
        # 获取当前运行的Python程序包名
        print("\n尝试授予相机权限...")
        
        # 授予标准相机权限
        permissions = [
            "android.permission.CAMERA",
            "android.permission.WRITE_EXTERNAL_STORAGE",
            "android.permission.READ_EXTERNAL_STORAGE"
        ]
        
        for permission in permissions:
            result = device.shell(f'pm grant com.android.shell {permission}')
            print(f"授予权限 {permission}: {result}")
        
        # 检查华为特定权限
        huawei_permissions = [
            "com.huawei.camera.permission.CARDREADER",
            "com.huawei.camera.permission.REMOTECONTROLLER",
            "com.huawei.camera.permission.RAPID_CAPTURE",
            "com.huawei.camera.permission.PRIVATE",
            "com.huawei.camera.permission.QRCODE_SCAN",
            "com.huawei.camera.permission.PREFERENCE_PROVIDER"
        ]
        
        print("\n检查华为特定权限：")
        for permission in huawei_permissions:
            status = device.shell(f'pm list permissions -g | grep {permission}')
            print(f"{permission}: {status if status else '未找到'}")
            
        # 检查相机服务状态
        print("\n相机服务状态：")
        camera_service = device.shell('dumpsys media.camera')
        print(camera_service)
        
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    print("开始检查和授予相机权限...")
    check_and_grant_camera_permissions()
    
    # 建议安装IP Webcam应用
    print("\n建议：")
    print("1. 请在手机上安装 IP Webcam 应用")
    print("2. 打开 IP Webcam 并允许相机权限")
    print("3. 点击 'Start server' 开始服务")
    print("4. 记下显示的IP地址和端口号")