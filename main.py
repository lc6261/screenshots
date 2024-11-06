import os
import sys
import tkinter as tk
from tkinter import ttk  # 添加 ttk 用于更现代的下拉框
from tkinter import scrolledtext
from PIL import Image, ImageTk
from src.recorder.av_recorder import AVRecorder
import tkinter.messagebox as messagebox
import cv2  # 添加这行

class RecorderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("音视频录制器")
        self.root.geometry("1024x768")  # 设置默认窗口大小
        
        # 添加这一行来初始化 merge_method
        self.merge_method = tk.StringVar(value="FFmpeg")
        
        # 创建主框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 创建左侧控制面板
        self.control_panel = tk.Frame(self.main_frame)
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 创建右侧视频预览区域
        self.preview_panel = tk.Frame(self.main_frame)
        self.preview_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 视频预览框架移到右侧
        self.video_frame = tk.Frame(self.preview_panel, width=640, height=480)
        self.video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.video_frame.pack_propagate(False)
        
        # 视频预览标签
        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框移到视频预览下方
        self.log_text = scrolledtext.ScrolledText(self.preview_panel, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始化录制器
        self.recorder = AVRecorder(self.log_text, self.video_label)
        
        # 在 __init__ 方法中添加状态标签
        self.status_label = tk.Label(self.main_frame, text="就绪")
        self.status_label.pack(pady=5)
        
        self.has_recordings = False  # 添加录制状态标记
        
        self.setup_ui()
        
    def setup_ui(self):
        # 在左侧控制面板中添加控件
        
        # 合并方式选择框架
        merge_frame = tk.LabelFrame(self.control_panel, text="合并设置")
        merge_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(merge_frame, text="合并方式:").pack(side=tk.LEFT, padx=5)
        self.merge_combo = ttk.Combobox(
            merge_frame,
            textvariable=self.merge_method,
            values=["FFmpeg", "MoviePy"],
            state="readonly",
            width=10
        )
        self.merge_combo.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 控制按钮框架
        button_frame = tk.LabelFrame(self.control_panel, text="操作控制")
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮垂直排列，统一使用 ttk.Button
        self.start_btn = ttk.Button(button_frame, text="开始录制", command=self.start_recording)
        self.start_btn.pack(fill=tk.X, padx=5, pady=2)
        
        self.stop_btn = ttk.Button(button_frame, text="停止录制", command=self.stop_recording, state='disabled')
        self.stop_btn.pack(fill=tk.X, padx=5, pady=2)
        
        self.merge_button = ttk.Button(button_frame, text="合并视频", command=self.merge_videos, state=tk.DISABLED)
        self.merge_button.pack(fill=tk.X, padx=5, pady=2)
        
        self.quit_btn = ttk.Button(button_frame, text="退出", command=self.quit_app)
        self.quit_btn.pack(fill=tk.X, padx=5, pady=2)
        
        # 同步控制框架
        sync_frame = tk.LabelFrame(self.control_panel, text="同步控制")
        sync_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 同步模式选择
        sync_mode_frame = tk.Frame(sync_frame)
        sync_mode_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(sync_mode_frame, text="同步模式:").pack(side=tk.LEFT, padx=5)
        self.sync_mode = tk.StringVar(value="delay")
        ttk.Radiobutton(sync_mode_frame, text="音频延迟", variable=self.sync_mode, 
                       value="delay", command=self.update_sync_mode).pack(side=tk.LEFT)
        ttk.Radiobutton(sync_mode_frame, text="帧率调整", variable=self.sync_mode, 
                       value="fps", command=self.update_sync_mode).pack(side=tk.LEFT)
        
        # 创建一个固定高度的容器来放置控制条
        self.sync_controls_container = tk.Frame(sync_frame, height=50)
        self.sync_controls_container.pack(fill=tk.X, padx=5, pady=2)
        self.sync_controls_container.pack_propagate(False)
        
        # 音频延迟控制
        self.delay_frame = tk.Frame(self.sync_controls_container)
        tk.Label(self.delay_frame, text="音频延迟(ms):").pack(side=tk.LEFT, padx=5)
        self.delay_scale = ttk.Scale(
            self.delay_frame,
            from_=-500,
            to=500,
            orient=tk.HORIZONTAL,
            value=0,
            command=self.update_delay
        )
        self.delay_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.delay_value_label = tk.Label(self.delay_frame, text="0 ms")
        self.delay_value_label.pack(side=tk.LEFT, padx=5)
        
        # 帧率控制
        self.fps_frame = tk.Frame(self.sync_controls_container)
        tk.Label(self.fps_frame, text="视频帧率:").pack(side=tk.LEFT, padx=5)
        self.fps_scale = ttk.Scale(
            self.fps_frame,
            from_=15.0,
            to=60.0,
            orient=tk.HORIZONTAL,
            value=self.recorder.detected_fps,
            command=self.update_fps
        )
        self.fps_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.fps_value_label = tk.Label(self.fps_frame, text=f"{self.recorder.detected_fps:.1f} fps")
        self.fps_value_label.pack(side=tk.LEFT, padx=5)
        
        # 缓冲区大小控制
        self.buffer_frame = tk.Frame(self.control_panel)
        self.buffer_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(self.buffer_frame, text="缓冲区大小:").pack(side=tk.LEFT, padx=5)
        self.buffer_scale = ttk.Scale(
            self.buffer_frame,
            from_=512,
            to=4096,
            orient=tk.HORIZONTAL,
            value=1024,
            command=self.update_buffer
        )
        self.buffer_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.buffer_value_label = tk.Label(self.buffer_frame, text="1024")
        self.buffer_value_label.pack(side=tk.LEFT, padx=5)
        
        # 添加重置按钮
        self.reset_btn = ttk.Button(
            self.control_panel,
            text="重置设置",
            command=self.reset_settings
        )
        self.reset_btn.pack(pady=5)
        
        # 在所有控件创建完成后，调用update_sync_mode来显示正确的控制面板
        self.update_sync_mode()
        
    def start_recording(self):
        self.recorder.start_recording()
        self.status_label.config(text="正在录制...")
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.merge_button.config(state='disabled')  # 录制时禁用合并按钮
        self.merge_combo.config(state='disabled')
        
    def stop_recording(self):
        """停止录制"""
        self.recorder.stop_recording()  # 使用 recorder 对象的方法
        self.status_label.config(text="就绪")
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.has_recordings = True  # 标记已有录制
        self.merge_button.config(state='normal')  # 启用合并按钮
        self.merge_combo.config(state='normal')
        
    def merge_videos(self):
        """合并视频"""
        if not self.has_recordings:
            messagebox.showwarning("提示", "没有可合并的视频！\n请先进行录制。")
            return
            
        try:
            # 检查文件是否存在
            if not hasattr(self.recorder, 'video_filename') or not hasattr(self.recorder, 'audio_filename'):
                messagebox.showwarning("提示", "找不到录制文件！\n请先进行录制。")
                return
                
            # 获取合并方式
            merge_method = self.merge_method.get()
            # 调用合并方法
            self.recorder.merge_av(merge_method)
            self.log("开始合并音视频...")
        except Exception as e:
            self.log(f"合并失败: {str(e)}")
            messagebox.showerror("错误", f"合并失败：{str(e)}")
            
    def quit_app(self):
        try:
            if self.recorder.recording:
                self.stop_recording()
            # 确保释放所有资源    
            if hasattr(self.recorder, 'cap'):
                self.recorder.cap.release()
            if hasattr(self.recorder, 'video_writer'):
                self.recorder.video_writer.release()
            if hasattr(self.recorder, 'audio'):
                self.recorder.audio.terminate()
            cv2.destroyAllWindows()
            self.root.destroy()  # 使用destroy代替quit
        except Exception as e:
            print(f"退出时发生错误: {e}")
            self.root.destroy()  # 确保窗口关闭
        
    def run(self):
        self.root.mainloop()

    def show_sync_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("同步设置")
        
        tk.Label(settings_window, text="视频帧率:").pack()
        fps_var = tk.StringVar(value=str(self.recorder.fps))
        tk.Entry(settings_window, textvariable=fps_var).pack()
        
        tk.Label(settings_window, text="音频延迟(ms):").pack()
        delay_var = tk.StringVar(value="100")
        tk.Entry(settings_window, textvariable=delay_var).pack()
        
        def apply_settings():
            self.recorder.fps = float(fps_var.get())
            self.recorder.audio_delay = int(delay_var.get())
            settings_window.destroy()
        
        tk.Button(settings_window, text="应用", command=apply_settings).pack()

    def update_buffer(self, value):
        """更新音频缓冲区大小"""
        buffer_size = int(float(value))
        self.buffer_value_label.config(text=str(buffer_size))
        if hasattr(self.recorder, 'buffer_size'):
            self.recorder.buffer_size = buffer_size
            self.log(f"缓冲区大小已调整为: {buffer_size}")
            
    def update_delay(self, value):
        """更新音频延迟"""
        delay_value = int(float(value))
        self.delay_value_label.config(text=f"{delay_value} ms")
        if hasattr(self.recorder, 'audio_delay'):
            self.recorder.audio_delay = delay_value
            self.log(f"音频延迟已调整为: {delay_value}ms")
            
    def update_fps(self, fps):
        """更新帧率设置"""
        try:
            fps = float(fps)
            self.recorder.fps = fps
            self.fps_value_label.config(text=f"{fps:.1f} fps")
        except ValueError:
            pass

    def reset_settings(self):
        """重置所有设置"""
        if self.recorder.recording:  # 使用 recorder 的 recording 属性
            messagebox.showwarning("提示", "请先停止录制！")
            return
            
        self.has_recordings = False
        self.merge_button.config(state=tk.DISABLED)
        
        # 重置到检测到的帧率
        self.fps_scale.set(self.recorder.detected_fps)
        self.update_fps(self.recorder.detected_fps)
        
        # 重置其他设置
        self.sync_mode.set("delay")
        self.update_sync_mode()
        self.delay_scale.set(0)
        self.update_delay(0)
        self.buffer_scale.set(1024)
        self.update_buffer(1024)
        
        self.merge_combo.config(state='normal')
        self.log("所有设置已重置为默认值")
        
    def log(self, message):
        """添加日志"""
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)

    def update_sync_mode(self):
        """更新同步模式"""
        mode = self.sync_mode.get()
        # 确保先隐藏所有控制面板
        if hasattr(self, 'fps_frame'):
            self.fps_frame.pack_forget()
        if hasattr(self, 'delay_frame'):
            self.delay_frame.pack_forget()
        
        # 根据模式显示对应的控制面板
        if mode == "delay":
            self.delay_frame.pack(fill=tk.X, expand=True)
        else:
            self.fps_frame.pack(fill=tk.X, expand=True)
        
        if hasattr(self, 'recorder'):
            self.recorder.sync_mode = mode
            self.log(f"切换到{mode}同步模式")

if __name__ == "__main__":
    app = RecorderApp()
    app.run() 