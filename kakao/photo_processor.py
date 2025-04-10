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
