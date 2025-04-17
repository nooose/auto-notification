import cv2

class PhotoProcessor:
    def preprocess_image(self, image_path: str, output_path: str) -> str:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        # Noise removal (Gaussian Blur)
        img = cv2.GaussianBlur(img, (5, 5), 0)

        # Contrast adjustment (Adaptive Threshold)
        processed_img = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        cv2.imwrite(output_path, processed_img)
        return output_path

    def crop_image(self, image_path: str, output_path: str, crop_rect: tuple[int, int, int, int] = None) -> str:
        img = cv2.imread(image_path)

        if img is None:
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {image_path}")

        x, y, w, h = crop_rect
        cropped = img[y:y+h, x:x+w]

        cv2.imwrite(output_path, cropped)
        return output_path