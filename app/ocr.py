import pytesseract
import pdfplumber
from PIL import Image

def extract_text(path):
    if path.endswith(".pdf"):
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    else:
        img = Image.open(path)
        return pytesseract.image_to_string(img, lang="eng")

