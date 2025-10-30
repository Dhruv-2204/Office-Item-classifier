import cv2
import time
from PySide6.QtCore import QThread, Signal


class CameraThread(QThread):
    frame_ready = Signal(object)
    fps_update = Signal(float)
    camera_error = Signal(str)

    def __init__(self):
        super().__init__()
        self.camera = None
        self.is_running = False
        self.port = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.target_fps = 60
        self.frame_interval = 1.0 / self.target_fps
        self.last_frame_time = 0
        self.consecutive_failures = 0
        self.max_failures = 10

    def start_camera(self, port=0):
        """Start camera optimized for 60 FPS"""
        self.stop_camera()
        time.sleep(0.2)  # Let previous camera fully release

        for test_port in [port, 1, 2, 3]:
            try:
                # Try DirectShow first (best for Windows)
                self.camera = cv2.VideoCapture(test_port, cv2.CAP_DSHOW)

                if self.camera.isOpened():
                    # Optimize camera settings for maximum FPS
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv2.CAP_PROP_FPS, 60)
                    self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
                    self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

                    # Verify camera works
                    for _ in range(3):  # Try a few times
                        ret, frame = self.camera.read()
                        if ret and frame is not None:
                            print(f"Camera {test_port}: {frame.shape[1]}x{frame.shape[0]} @ 60 FPS")
                            self.port = test_port
                            self.is_running = True
                            self.consecutive_failures = 0
                            self.start()
                            return True

                    self.camera.release()
                    self.camera = None

            except Exception as e:
                if self.camera:
                    self.camera.release()
                    self.camera = None

        self.camera_error.emit("No camera found on ports 0-3")
        return False

    def stop_camera(self):
        """Stop camera immediately"""
        self.is_running = False
        if self.camera:
            self.camera.release()
            self.camera = None
        if self.isRunning():
            self.wait(300)  # Quick timeout

    def run(self):
        """60 FPS camera loop with precise timing"""
        while self.is_running:
            current_time = time.time()

            # Precise timing control for 60 FPS
            time_since_last = current_time - self.last_frame_time
            if time_since_last < self.frame_interval:
                sleep_time = (self.frame_interval - time_since_last) * 1000
                self.msleep(max(1, int(sleep_time)))
                continue

            try:
                if not self.camera or not self.camera.isOpened():
                    self.consecutive_failures += 1
                    if self.consecutive_failures > self.max_failures:
                        break
                    self.msleep(10)
                    continue

                # Fast frame capture
                ret, frame = self.camera.read()
                if not ret:
                    self.consecutive_failures += 1
                    if self.consecutive_failures > self.max_failures:
                        break
                    continue

                # Success - reset failure counter
                self.consecutive_failures = 0
                self.last_frame_time = current_time

                # FPS calculation (update every 0.5 seconds for responsiveness)
                self.frame_count += 1
                if current_time - self.last_fps_time >= 0.5:
                    fps = self.frame_count / (current_time - self.last_fps_time)
                    self.fps_update.emit(fps)
                    self.frame_count = 0
                    self.last_fps_time = current_time

                # Emit frame for processing
                self.frame_ready.emit(frame)

            except Exception as e:
                self.consecutive_failures += 1
                if self.consecutive_failures > self.max_failures:
                    break
                self.msleep(1)