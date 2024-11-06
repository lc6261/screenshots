import pyaudio
import wave
import threading
from datetime import datetime
import os

class AudioRecorder:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.RATE = 44100
        self.CHANNELS = 1
        self.recording = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        
    def start(self, device_index):
        if not self.recording:
            self.recording = True
            self.frames = []
            self.device_index = device_index
            self.audio_thread = threading.Thread(target=self._record)
            self.audio_thread.start()
            
    def stop(self):
        if self.recording:
            self.recording = False
            self.audio_thread.join()
            return self._save()
            
    def _record(self):
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
        
    def _save(self):
        if not self.frames:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"audio_{timestamp}.wav")
        
        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            return filename
        except Exception as e:
            print(f"保存音频失败: {e}")
            return None 