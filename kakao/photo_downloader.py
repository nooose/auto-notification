import subprocess
import cv2
import numpy as np
import threading

class PhotoDownloader:
    def __init__(self, url: str, width: int = 1920, height: int = 1080, restart_interval: int = 70):
        self.url = url
        self.width = width
        self.height = height
        self.restart_interval = restart_interval
        self.frame_count = 0

        self.latest_frame = None
        self.running = True
        self.lock = threading.Lock()
        self.proc = None
        self.read_thread = None

        self._start_ffmpeg()
        self._start_reader()

    def _start_ffmpeg(self):
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except Exception as e:
                print(f"[프로세스 종료 오류] {e}")

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
            stderr=subprocess.DEVNULL,
            bufsize=10**8
        )

    def _start_reader(self):
        if self.read_thread and self.read_thread.is_alive():
            self.running = False
            self.read_thread.join()

        self.running = True
        self.read_thread = threading.Thread(target=self._read_frames_loop, daemon=True)
        self.read_thread.start()

    def _restart_ffmpeg(self):
        print(f"[FFmpeg 재시작]")
        self._start_ffmpeg()
        self._start_reader()
        self.frame_count = 0
        self.latest_frame = None

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
        self.frame_count += 1
        if self.frame_count >= self.restart_interval:
            self._restart_ffmpeg()

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
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join()
        if self.proc:
            self.proc.terminate()
            self.proc.wait()
