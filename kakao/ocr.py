import cv2
import pytesseract
from PIL import Image

def preprocess_image(image_path):
    """이미지 전처리 (흑백 변환 + 대비 조정 + 노이즈 제거)"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # 노이즈 제거 (가우시안 블러)
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # 대비 조정 (Adaptive Threshold)
    processed_img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    processed_image_path = "processed_kakao.jpeg"
    cv2.imwrite(processed_image_path, processed_img)

    return processed_image_path

def extract_text(image_path):
    """OCR 실행 (한글+영어, 고정밀 모드)"""
    processed_path = preprocess_image(image_path)

    image = Image.open(processed_path)
    custom_config = r'--oem 1 --psm 6'  # LSTM OCR + 한 줄씩 인식
    extracted_text = pytesseract.image_to_string(image, lang="kor+eng", config=custom_config)

    print("🔍 추출된 텍스트:")
    print(extracted_text)

if __name__ == "__main__":
    extract_text("kakao.jpeg")

