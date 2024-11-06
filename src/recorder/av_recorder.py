import cv2
import pyaudio
import wave
import threading
from datetime import datetime
import os
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import time

class AVRecorder:
    def __init__(self, log_text, video_label):
        self.log_text = log_text
        self.video_label = video_label
        self.recording = False
        
        # 创建输出目录
        self.output_dir = os.path.join(os.getcwd(), "recordings")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 音频设置
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1  # 单声道
        self.RATE = 44100
        self.audio = pyaudio.PyAudio()
        
        # 添加时间戳相关变量
        self.start_time = None
        self.audio_frames_timestamp = []
        self.video_frames_timestamp = []
        self.fps = 30.0  # 设置固定的视频帧率
        self.frame_time = 1.0 / self.fps  # 每帧的理想时间
        self.frame_count = 0
        self.last_audio_time = 0
        
        self.audio_delay = 0
        
        self.current_fps = self.fps
        self.sync_threshold = 0.1  # 100ms的同步阈值
        
        self.sync_mode = "delay"  # 默认使用音频延迟模式
        self.buffer_size = 1024
        
        # 先初始化摄像头
        self.init_camera()
        
        # 然后检测帧率
        self.detected_fps = self._detect_camera_fps()
        self.fps = self.detected_fps
        self.log(f"检测到摄像头实际帧率: {self.detected_fps:.1f}")
        
    def log(self, message):
        """添加日志"""
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
        print(message)
        
    def start_recording(self):
        """开始录制"""
        try:
            # 检查音频设备
            device_count = self.audio.get_device_count()
            found_input = False
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info.get('maxInputChannels') > 0:
                    found_input = True
                    self.log(f"找到音频输入设备: {device_info.get('name')}")
                    break
                    
            if not found_input:
                raise Exception("未找到可用的音频输入设备")
            
            # 初始化视频录制
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("无法打开摄像头")
            
            # 创建视频写入器
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.video_filename = os.path.join(self.output_dir, f"video_{timestamp}.mp4")
            self.audio_filename = os.path.join(self.output_dir, f"audio_{timestamp}.wav")
            
            # 设置视频编码器和参数
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                self.video_filename,
                fourcc,
                self.fps,
                (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                 int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))),
                True
            )
            
            # 重置计数器
            self.frame_count = 0
            self.audio_frames = []
            
            # 初始化音频录制
            self.audio_frames = []
            self.audio_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            # 设置视频帧率
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # 记录开始时间
            self.start_time = time.time()
            self.audio_frames = []
            self.audio_frames_timestamp = []
            self.video_frames_timestamp = []
            
            self.recording = True
            
            # 启动视频录制线程
            self.video_thread = threading.Thread(target=self._record_video)
            self.video_thread.daemon = True
            self.video_thread.start()
            
            # 启动音频录制线程
            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
            # 启动同步监控线程
            self.monitor_thread = threading.Thread(target=self._monitor_sync)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            self.log("开始录制音视频...")
            
        except Exception as e:
            self.log(f"启动录制失败: {str(e)}")
            self.recording = False
            import traceback
            self.log(traceback.format_exc())
            
    def _record_video(self):
        """视频录制循环"""
        try:
            start_time = time.perf_counter()
            self.current_fps = self.fps  # 初始帧率
            
            while self.recording:
                # 使用当前帧率计算延迟
                frame_delay = 1.0 / self.current_fps
                
                ret, frame = self.cap.read()
                if ret:
                    self.video_writer.write(frame)
                    self.update_preview(frame)
                    self.frame_count += 1
                    
                    # 精确控制帧率
                    elapsed = time.perf_counter() - start_time
                    expected_frame_time = self.frame_count * frame_delay
                    sleep_time = expected_frame_time - elapsed
                    
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    
        except Exception as e:
            self.log(f"视频录制错误: {str(e)}")
    
    def _record_audio(self):
        """音频录制循环"""
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=self._audio_callback  # 使用回调方式处理音频
            )
            
            stream.start_stream()
            while self.recording:
                time.sleep(0.1)
                
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            self.log(f"音频录制错误: {str(e)}")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """音频回调处理"""
        if self.recording:
            self.audio_frames.append(in_data)
        return (None, pyaudio.paContinue)
    
    def update_preview(self, frame):
        """更新视频预览"""
        try:
            # 转换OpenCV的BGR格式到RGB格式
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 转换为PhotoImage
            image = Image.fromarray(rgb_frame)
            # 调整图像大小以适应预览窗口
            image = image.resize((640, 480), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image=image)
            # 更新预览标签
            self.video_label.configure(image=photo)
            self.video_label.image = photo  # 保持引用防止垃圾回收
        except Exception as e:
            self.log(f"更新预览失败: {str(e)}")
            
    def stop_recording(self):
        """停止录制"""
        if self.recording:
            self.recording = False
            self.log("正在停止录制...")
            
            # 创建后台保存线程
            save_thread = threading.Thread(target=self._save_recording)
            save_thread.daemon = True
            save_thread.start()
            
    def _save_recording(self):
        """在后台线程中保存录制文件"""
        try:
            # 等待录制线程结束
            if hasattr(self, 'video_thread'):
                self.video_thread.join(timeout=1)  # 设置超时时间
            if hasattr(self, 'audio_thread'):
                self.audio_thread.join(timeout=1)  # 设置超时时间
            
            # 保存音频
            self._save_audio()
            
            # 释放视频资源
            if hasattr(self, 'video_writer'):
                self.video_writer.release()
            if hasattr(self, 'cap'):
                self.cap.release()
            
            # 释放音资源
            if hasattr(self, 'audio_stream'):
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            
            self.log(f"录制已完成\n视频: {self.video_filename}\n音频: {self.audio_filename}")
            
        except Exception as e:
            self.log(f"停止录制时出错: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            
    def _save_audio(self):
        """保存音频文件"""
        if self.audio_frames:
            try:
                wf = wave.open(self.audio_filename, 'wb')
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.audio_frames))
                wf.close()
            except Exception as e:
                self.log(f"保存音频失败: {str(e)}")
                
    def merge_av(self, merge_method="FFmpeg"):
        """合并音视频"""
        try:
            # 检查文件是否存在
            if not os.path.exists(self.video_filename):
                self.log(f"找不到视频文件: {self.video_filename}")
                return
            if not os.path.exists(self.audio_filename):
                self.log(f"找不到音频文件: {self.audio_filename}")
                return
            
            self.log("开始合并音视频...")
            # 创建后台合并线程
            merge_thread = threading.Thread(target=self._do_merge_av, args=(merge_method,))
            merge_thread.daemon = True
            merge_thread.start()
        except Exception as e:
            self.log(f"合并准备失败: {str(e)}")
            raise

    def _do_merge_av(self, merge_method):
        try:
            output_file = self.video_filename.replace('.mp4', '_with_audio.mp4')
            
            if merge_method == "FFmpeg":
                import subprocess
                
                # 根据延迟值的正负选择不同的处理方式
                if self.audio_delay >= 0:
                    # 音频延迟（正值）：使用 adelay
                    filter_complex = f'adelay={self.audio_delay}|{self.audio_delay}'
                else:
                    # 音频提前（负值）：使用 atrim 和 asetpts
                    delay_sec = abs(self.audio_delay) / 1000.0  # 转换为秒
                    filter_complex = f'atrim=start={delay_sec},asetpts=PTS-STARTPTS'
                
                cmd = [
                    'ffmpeg', '-y',
                    '-i', self.video_filename,
                    '-i', self.audio_filename,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-vsync', 'cfr',
                    '-async', '1',
                    '-af', filter_complex,
                    output_file
                ]
                
                # 添加错误输出捕获
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                if result.stderr:
                    self.log(f"FFmpeg 输出: {result.stderr}")
                    
            else:
                # moviepy 方式保持不变
                from moviepy.editor import VideoFileClip, AudioFileClip
                video = VideoFileClip(self.video_filename)
                audio = AudioFileClip(self.audio_filename)
                
                # 计算音频偏移（秒）
                offset = self.audio_delay / 1000.0
                
                if offset >= 0:
                    # 音频延迟
                    final_clip = video.set_audio(audio.set_start(offset))
                else:
                    # 音频提前
                    final_clip = video.set_audio(audio).subclip(abs(offset))
                
                final_clip.write_videofile(output_file,
                                         codec='libx264',
                                         audio_codec='aac',
                                         temp_audiofile='temp-audio.m4a',
                                         remove_temp=True)
                
                # 清理资源
                video.close()
                audio.close()
                
            self.log(f"音视频合并完成: {output_file}")
            
        except Exception as e:
            self.log(f"合并音视频失败: {str(e)}")
            import traceback
            self.log(traceback.format_exc())

    def _monitor_sync(self):
        """监控并纠正音视频同步状态"""
        while self.recording:
            video_time = self.frame_count / self.fps
            audio_time = len(self.audio_frames) * self.CHUNK / float(self.RATE)
            drift = audio_time - video_time  # 正值表示音频快于视频
            
            if abs(drift) > 0.1:  # 超过100ms就纠正
                self.log(f"检测到同步偏差: {drift:.3f}秒")
                
                if drift > 0:  # 音频快于视频
                    # 调整视频帧率以追赶音频
                    self.current_fps = self.fps * 1.1  # 临时提高10%的帧率
                    self.log("加快视频采集速度")
                else:  # 视频快于音频
                    # 降低视频帧率以等待音频
                    self.current_fps = self.fps * 0.9  # 临时降低10%的帧率
                    self.log("降低视频采集速度")
            else:
                # 恢复正常帧率
                self.current_fps = self.fps
                
            time.sleep(0.5)  # 每0.5秒检查一次

    @property
    def fps(self):
        return self._fps
        
    @fps.setter
    def fps(self, value):
        """设置帧率"""
        self._fps = float(value)
        if hasattr(self, 'recording') and self.recording:
            self.current_fps = self._fps  # 如果正在录制，同时更新当前帧率
            self.log(f"帧率已调整为: {self._fps:.1f}")

    def init_camera(self):
        """初始化摄像头"""
        self.log("正在初始化摄像头...")
        self.cap = cv2.VideoCapture(0)  # 默认使用第一个摄像头
        
        if not self.cap.isOpened():
            raise Exception("无法打开摄像头")
            
        # 设置摄像头属性
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # 读取一帧测试
        ret, _ = self.cap.read()
        if not ret:
            raise Exception("无法从摄像头读取画面")
            
        self.log("摄像头初始化成功")
        
    def _detect_camera_fps(self, test_duration=3.0):
        """检测摄像头实际帧率"""
        self.log("正在检测摄像头实际帧率...")
        frames = 0
        start_time = time.perf_counter()
        
        while (time.perf_counter() - start_time) < test_duration:
            ret, _ = self.cap.read()
            if ret:
                frames += 1
            else:
                self.log("警告：读取视频帧失败")
                break
                
        actual_time = time.perf_counter() - start_time
        detected_fps = frames / actual_time
        
        # 为了稳定性，略微降低检测到的帧率
        safe_fps = detected_fps * 0.95
        
        # 确保帧率在合理范围内
        return max(min(safe_fps, 60.0), 15.0)

    def merge_videos(self):
        """合并视频"""
        # 检查是否有录制文件
        if not os.path.exists(self.output_dir):
            raise Exception("输出目录不存在")
            
        video_files = [f for f in os.listdir(self.output_dir) 
                      if f.endswith('.mp4') and f.startswith('temp_')]
                      
        if not video_files:
            raise Exception("没有找到可合并的视频文件")

    def __del__(self):
        try:
            if hasattr(self, 'cap'):
                self.cap.release()
            if hasattr(self, 'video_writer'):
                self.video_writer.release()
            if hasattr(self, 'audio'):
                self.audio.terminate()
            cv2.destroyAllWindows()
        except:
            pass