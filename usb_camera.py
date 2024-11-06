import pyaudio
import wave
import threading
import time
import os
from datetime import datetime

class AudioRecorder:
    def __init__(self):
        # 设置保存路径
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.join(self.current_dir, "recordings")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        print(f"\n文件将保存在: {self.output_dir}")
        
        # 初始化音频设置
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.RATE = 44100
        self.recording = False
        self.frames = []
        
        # 检查麦克风
        print("\n=== 检查麦克风 ===")
        self.audio = pyaudio.PyAudio()
        
        # 列出所有音频设备
        input_devices = self.list_audio_devices()
        
        if input_devices:
            while True:
                try:
                    device_index = int(input("\n请选择音频输入设备编号: "))
                    if device_index not in input_devices:
                        print("无效的设备编号，请重试")
                        continue
                    
                    dev_info = self.audio.get_device_info_by_index(device_index)
                    
                    # 保存设备索引
                    self.device_index = device_index
                    
                    # 设置通道数
                    self.CHANNELS = min(1, dev_info['maxInputChannels'])
                    print(f"\n使用音频设备: {dev_info['name']}")
                    print(f"通道数: {self.CHANNELS}")
                    
                    # 测试选择的设备
                    if self.test_audio_input():
                        print("音频测试通过！")
                        break
                    else:
                        retry = input("测试失败，是否选择其他设备？(y/n): ")
                        if retry.lower() != 'y':
                            raise Exception("音频设备测试失败")
                except ValueError:
                    print("请输入有效的数字")
                except Exception as e:
                    print(f"设备选择错误: {e}")
                    retry = input("是否重试？(y/n): ")
                    if retry.lower() != 'y':
                        raise Exception("设备选择失败")
        else:
            print("没有找到可用的音频输入设备")
            raise Exception("无音频设备")

    def list_audio_devices(self):
        """详细列出所有音频设备"""
        print("\n=== 音频设备列表 ===")
        input_devices = []
        
        for i in range(self.audio.get_device_count()):
            try:
                dev_info = self.audio.get_device_info_by_index(i)
                if dev_info['maxInputChannels'] > 0:  # 只显示输入设备
                    print(f"\n设备 {i}:")
                    print(f"  名称: {dev_info['name']}")
                    print(f"  设备类型: {'USB设备' if 'USB' in dev_info['name'] else '内置设备'}")
                    print(f"  输入通道: {dev_info['maxInputChannels']}")
                    print(f"  默认采样率: {dev_info['defaultSampleRate']}")
                    print(f"  设备索引: {dev_info['index']}")
                    print(f"  主机API: {dev_info['hostApi']}")
                    input_devices.append(i)
            except Exception as e:
                print(f"获取设备 {i} 信息时出错: {e}")
        
        return input_devices

    def test_audio_input(self):
        """测试音频输入设备"""
        print("\n=== 音频输入测试 ===")
        print("将进行5秒音频测试，请对着麦克风说话...")
        
        test_frames = []
        stream = None
        
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.CHUNK
            )
            
            print("开始录音测试...")
            for i in range(0, int(self.RATE / self.CHUNK * 5)):
                data = stream.read(self.CHUNK)
                test_frames.append(data)
                # 显示音量指示器
                rms = sum(abs(int.from_bytes(data[i:i+2], 'little', signed=True)) 
                         for i in range(0, len(data), 2)) / (len(data)/2)
                bars = int(rms / 100)
                print('\r' + '█' * bars + ' ' * (50-bars), end='')
                
            print("\n录音测试完成")
            
            # 保存测试音频
            test_file = os.path.join(self.output_dir, "audio_test.wav")
            wf = wave.open(test_file, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(test_frames))
            wf.close()
            
            print(f"\n测试文件已保存: {test_file}")
            print("请播放测试文件检查录音效果")
            
            # 自动打开文件夹
            os.system(f'explorer "{self.output_dir}"')
            
            result = input("\n能听到清晰的声音吗？(y/n): ")
            return result.lower() == 'y'
            
        except Exception as e:
            print(f"测试过程出错: {e}")
            return False
        finally:
            if stream:
                stream.stop_stream()
                stream.close()

    def start_recording(self):
        """开始录音"""
        if not self.recording:
            self.recording = True
            self.frames = []
            self.audio_thread = threading.Thread(target=self.record_audio)
            self.audio_thread.start()
            print("\n=== 开始录音 ===")
            print("按 Enter 键停止录音...")

    def stop_recording(self):
        """停止录音"""
        if self.recording:
            self.recording = False
            # 等待录制线程结束
            if hasattr(self, 'video_thread'):
                self.video_thread.join(timeout=1)
            if hasattr(self, 'audio_thread'):
                self.audio_thread.join(timeout=1)
            
            # 释放资源
            if hasattr(self, 'video_writer'):
                self.video_writer.release()
            if hasattr(self, 'cap'):
                self.cap.release()
            if hasattr(self, 'audio_stream'):
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            cv2.destroyAllWindows()
            print("\n=== 录音已停止 ===")

    def record_audio(self):
        """录音线程"""
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.CHUNK
        )
        
        while self.recording:
            try:
                data = stream.read(self.CHUNK)
                self.frames.append(data)
            except Exception as e:
                print(f"录音错误: {e}")
                break
        
        stream.stop_stream()
        stream.close()

    def save_audio(self):
        """保存录音文件"""
        if not self.frames:
            print("没有录制到音频数据")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"recording_{timestamp}.wav")
        
        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            print(f"\n=== 文件已保存 ===")
            print(f"位置: {filename}")
            
            # 打开文件夹
            os.system(f'explorer "{self.output_dir}"')
            
        except Exception as e:
            print(f"保存音频失败: {e}")

    def run(self):
        """运行录音程序"""
        print("\n=== 录音程序就绪 ===")
        print("按 Enter 键开始录音")
        print("再次按 Enter 键停止录音")
        print("输入 'q' 退出程序")
        
        while True:
            cmd = input()
            if cmd.lower() == 'q':
                if self.recording:
                    self.stop_recording()
                break
            elif not self.recording:
                self.start_recording()
            else:
                self.stop_recording()
        
        self.audio.terminate()
        print("\n程序已退出")

if __name__ == "__main__":
    try:
        print("=== 录音程序 ===")
        recorder = AudioRecorder()
        recorder.run()
    except Exception as e:
        print(f"程序初始化失败: {e}")