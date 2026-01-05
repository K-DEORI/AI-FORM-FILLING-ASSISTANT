from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image
import shutil
import os
import re
from pdf2image import convert_from_path

# -------------------
# Tesseract path (IMPORTANT for Windows)
# -------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = FastAPI(title="AI Form Filling Assistant")

# -------------------
# Enable CORS
# -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------
# FIELD EXTRACTION LOGIC
# -------------------
def extract_fields(text: str):
    result = {
        "full_name": "",
        "dob": "",
        "address": "",
        "aadhaar": ""
    }

    # Name (with or without label)
    name_match = re.search(
        r"(NAME\s*[:\-]?\s*)?([A-Z][A-Z ,]{3,})",
        text,
        re.IGNORECASE
    )
    if name_match:
        result["full_name"] = name_match.group(2).strip()

    # Date of Birth (DD/MM/YYYY or YYYY-MM-DD)
    dob_match = re.search(
        r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})",
        text
    )
    if dob_match:
        result["dob"] = dob_match.group(1)

    # Aadhaar number (12 digits with spaces)
    aadhaar_match = re.search(
        r"\b(\d{4}\s?\d{4}\s?\d{4})\b",
        text
    )
    if aadhaar_match:
        result["aadhaar"] = aadhaar_match.group(1)

    # Address (after keyword ADDRESS)
    address_match = re.search(
        r"ADDRESS\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE
    )
    if address_match:
        result["address"] = address_match.group(1).strip()

    return result

# -------------------
# OCR FUNCTION
# -------------------
def perform_ocr(file_path: str):
    text = ""

    if file_path.lower().endswith(".pdf"):
        pages = convert_from_path(file_path)
        for page in pages:
            text += pytesseract.image_to_string(page) + "\n"
    else:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)

    return text

# -------------------
# API ENDPOINT
# -------------------
@app.post("/process")
async def process_document(file: UploadFile = File(...)):

    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        ocr_text = perform_ocr(temp_path)
        print("OCR Text Extracted:\n", ocr_text)

        extracted_fields = extract_fields(ocr_text)

        return {
            "ocr_text": ocr_text,
            "filled_form": extracted_fields
        }

    except Exception as e:
        print("Error in OCR:", e)
        return {
            "error": str(e),
            "ocr_text": "",
            "filled_form": {}
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
