import pytesseract
from PIL import Image

class OCRReader:
    def extract_text(self, image_path: str) -> str:
        image = Image.open(image_path)
        custom_config = r'--oem 1 --psm 6'  # LSTM OCR + single line recognition
        return pytesseract.image_to_string(image, lang="kor+eng", config=custom_config)
