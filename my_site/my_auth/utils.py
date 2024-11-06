import os
from django.conf import settings
from io import BytesIO
from PIL import Image
# Run in the venv environment
import os
import pytesseract  # pip install pytesseract # need to install Tesseract-OCR.exe before using pytesseract.

# pasrsing.py # test
import re

def parse_text(text_data):
    text_data = {
        "student_id": re.search(r"학번\s+(\d+)", text_data).group(1) if re.search(r"학번\s+(\d+)", text_data) else "unknown",
        "korean_name": re.search(r"한글성명\s+(\S+)", text_data).group(1) if re.search(r"한글성명\s+(\S+)", text_data) else "unknown",
        "grade": re.search(r"학년\s+(\d+학년)", text_data).group(1) if re.search(r"학년\s+(\d+학년)", text_data) else "unknown",
        "status": re.search(r"학적상태\s+(\S+)", text_data).group(1) if re.search(r"학적상태\s+(\S+)", text_data) else "unknown",
        "department": re.search(r"학부\(과\)\s+(\S+)", text_data).group(1) if re.search(r"학부\(과\)\s+(\S+)", text_data) else "unknown",
        "phone_number": re.search(r"전화번호\*\s+([\d-]+)", text_data).group(1) if re.search(r"전화번호\*\s+([\d-]+)", text_data) else "unknown",
        "mobile_number": re.search(r"휴대폰\s+(\d+)", text_data).group(1) if re.search(r"휴대폰\s+(\d+)", text_data) else "unknown",
        "email": re.search(r"E-Mail\s+(\S+)", text_data).group(1) if re.search(r"E-Mail\s+(\S+)", text_data) else "unknown"
    }
    
    return text_data

def get_unknown_fields(data):
    """
    딕셔너리에서 value 값이 "unknown"인 항목을 찾아서 반환합니다.
    
    Parameters:
        data (dict): 'unknown' 값을 포함한 데이터 딕셔너리
    
    Returns:
        list: 'unknown' 값을 가진 키의 목록
    """
    unknown_fields = [key for key, value in data.items() if value == "unknown"]
    return unknown_fields

# Tesseract 실행 파일 경로 설정 (윈도우 사용자만 필요)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def perform_ocr(image):
    image.seek(0)
    image = Image.open(BytesIO(image.read()))
    
    # OCR 실행 (한국어와 영어 혼용 인식)
    text = pytesseract.image_to_string(image, lang='kor+eng')
    
    # 텍스트 파싱
    clean_dict = parse_text(text)
    
    return clean_dict

def save_student_card(directory, extension, clean_dict):
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filename_base = 'student_card_' + clean_dict.get('korean_name', 'unknown')
    filename = f"{filename_base}.{extension}"
    counter = 1
    while os.path.exists(os.path.join(directory, filename)):
        filename = f"{filename_base}_{counter}.{extension}"
        counter += 1
    
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', encoding='utf-8') as file:
        for key, value in clean_dict.items():
            file.write(f"{key}: {value}\n")
    
    return filepath
