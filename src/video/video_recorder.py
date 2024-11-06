import cv2
import threading
from datetime import datetime
import os

class VideoRecorder:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.recording = False
        
    def start(self, device_index=0):
        if not self.recording:
            self.recording = True
            self.device_index = device_index
            self.video_thread = threading.Thread(target=self._record)
            self.video_thread.start()
            
    def stop(self):
        if self.recording:
            self.recording = False
            self.video_thread.join()
            
    def _record(self):
        cap = cv2.VideoCapture(self.device_index)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"video_{timestamp}.avi")
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640,480))
        
        while self.recording:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
                cv2.imshow('Recording', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        cap.release()
        out.release()
        cv2.destroyAllWindows() 