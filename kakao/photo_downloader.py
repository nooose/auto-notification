import subprocess
import cv2
import numpy as np
import threading

class PhotoDownloader:
    def __init__(self, url: str, width: int = 1280, height: int = 720):
        self.url = url
        self.width = width
        self.height = height
        self.latest_frame = None
        self.running = True
        self.lock = threading.Lock()
        self._start_ffmpeg()
        self.read_thread = threading.Thread(target=self._read_frames_loop, daemon=True)
        self.read_thread.start()

    def _start_ffmpeg(self):
        self.proc = subprocess.Popen(
            [
                "ffmpeg",
                "-probesize", "5M",
                "-analyzeduration", "10M",
                "-fflags", "+nobuffer",
                "-flags", "low_delay",
                "-i", self.url,
                "-s", f"{self.width}x{self.height}",
                "-f", "image2pipe",
                "-pix_fmt", "bgr24",
                "-vcodec", "rawvideo",
                "-"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**8
        )

    def _read_frames_loop(self):
        frame_size = self.width * self.height * 3
        while self.running:
            try:
                raw_image = self.proc.stdout.read(frame_size)
                if not raw_image:
                    continue
                frame = np.frombuffer(raw_image, dtype=np.uint8).reshape((self.height, self.width, 3))
                with self.lock:
                    self.latest_frame = frame
            except Exception as e:
                print(f"[프레임 수신 실패] {e}")
                break

    def download_latest_photo(self, path: str):
        with self.lock:
            if self.latest_frame is not None:
                cropped_frame = self._remove_black_borders(self.latest_frame)
                cv2.imwrite(path, cropped_frame)
            else:
                print("프레임 수신 전입니다.")

    def _remove_black_borders(self, frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        coords = cv2.findNonZero(thresh)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            return frame[y:y+h, x:x+w]
        return frame

    def close(self):
        self.running = False
        self.read_thread.join()
        self.proc.terminate()
        self.proc.wait()
