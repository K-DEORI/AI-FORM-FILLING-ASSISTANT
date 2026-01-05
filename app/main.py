from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import re
import spacy
import os
import io
import traceback
import fitz  # PyMuPDF
import langdetect
from langdetect import detect, DetectorFactory
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import unicodedata

DetectorFactory.seed = 0

app = FastAPI(title="AI Form Filling Assistant Pro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tesseract path - Update if different
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# spaCy models
nlp_en = None
try:
    nlp_en = spacy.load("en_core_web_sm")
    print("✅ English spaCy loaded")
except:
    print("⚠️ Install: python -m spacy download en_core_web_sm")

# 🚀 EXTENDED FORM TEMPLATES with Govt Form Links + Fill Options
FORM_TEMPLATES = {
    "standard": {
        "fields": ["full_name", "dob", "address", "aadhaar", "pan", "phone"],
        "title": "Standard Form",
        "gov_links": [
            {"name": "Aadhaar Enrolment", "url": "https://uidai.gov.in/en/my-aadhaar/get-aadhaar.html", "fillable": True},
            {"name": "PAN Application", "url": "https://www.onlineservices.nsdl.com/paam/endUserRegisterContact.html", "fillable": True},
            {"name": "Passport Seva", "url": "https://www.passportindia.gov.in/", "fillable": True},
            {"name": "Voter ID", "url": "https://voters.eci.gov.in/", "fillable": True}
        ]
    },
    "aadhaar": {
        "fields": ["full_name", "dob", "address", "aadhaar"],
        "title": "Aadhaar Form",
        "gov_links": [
            {"name": "UIDAI Portal", "url": "https://uidai.gov.in/", "fillable": True},
            {"name": "Aadhaar Update", "url": "https://myaadhaar.uidai.gov.in/", "fillable": True},
            {"name": "e-Aadhaar Download", "url": "https://myaadhaar.uidai.gov.in/downloadEAadhaar", "fillable": False}
        ]
    },
    "pan": {
        "fields": ["full_name", "dob", "address", "pan", "phone"],
        "title": "PAN Form",
        "gov_links": [
            {"name": "NSDL PAN", "url": "https://www.tin-nsdl.com/services/pan/panindex.html", "fillable": True},
            {"name": "UTIITSL PAN", "url": "https://www.pan.utiitsl.com/", "fillable": True},
            {"name": "PAN Status", "url": "https://www.tin-nsdl.com/pan2/servlet/PanApplicationStatus", "fillable": False}
        ]
    },
    "passport": {
        "fields": ["full_name", "dob", "address", "phone", "pan"],
        "title": "Passport Form",
        "gov_links": [
            {"name": "Passport Seva", "url": "https://www.passportindia.gov.in/AppOnlineProject/online/formAvailable", "fillable": True},
            {"name": "PSIL Form Download", "url": "https://portal2.passportindia.gov.in/AppOnlineProject/online/formAvailable", "fillable": True},
            {"name": "Track Application", "url": "https://portal2.passportindia.gov.in/AppOnlineProject/statusTracker", "fillable": False}
        ]
    },
    "voter": {
        "fields": ["full_name", "dob", "address", "phone"],
        "title": "Voter ID Form",
        "gov_links": [
            {"name": "NVSP Portal", "url": "https://www.nvsp.in/", "fillable": True},
            {"name": "Voters Service", "url": "https://voters.eci.gov.in/", "fillable": True},
            {"name": "Form 6 (New Voter)", "url": "https://nvsp.in/FormsReg/Registration", "fillable": True}
        ]
    },
    "income_tax": {
        "fields": ["full_name", "dob", "address", "pan", "phone"],
        "title": "Income Tax Form",
        "gov_links": [
            {"name": "ITR-1 (Sahaj)", "url": "https://www.incometax.gov.in/iec/foportal/", "fillable": True},
            {"name": "e-Filing Portal", "url": "https://www.incometax.gov.in/iec/foportal/", "fillable": True},
            {"name": "Form 16 Download", "url": "https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1", "fillable": False}
        ]
    },
    "driving_licence": {
        "fields": ["full_name", "dob", "address", "phone"],
        "title": "Driving Licence Form",
        "gov_links": [
            {"name": "Sarathi Parivahan", "url": "https://sarathi.parivahan.gov.in/", "fillable": True},
            {"name": "DL Application", "url": "https://sarathi.parivahan.gov.in/sarathiservice/stateSelection.do", "fillable": True},
            {"name": "Track DL Status", "url": "https://parivahan.gov.in/parivahan/", "fillable": False}
        ]
    }
}

def preprocess_image(image: Image.Image) -> Image.Image:
    """Enhanced preprocessing for better OCR"""
    image = image.convert('L')
    image = image.filter(ImageFilter.MedianFilter(size=3))
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(2.0)

def detect_language(text: str) -> str:
    try:
        return detect(text[:1000]) if text.strip() else "en"
    except:
        return "en"

def pdf_to_images(pdf_path: str) -> list:
    try:
        doc = fitz.open(pdf_path)
        images = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        doc.close()
        return images
    except:
        return []

# 🚀 ULTIMATE Aadhaar Detection - Full + ALL Masked Formats
def extract_aadhaar(text: str) -> str:
    """🚀 Detects FULL Aadhaar + ALL masked formats with/without field labels"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidates = []
    
    # 1. FULL Aadhaar Numbers (Highest Priority)
    full_patterns = [
        r'\b[2-9]\d{3}\s*\d{4}\s*\d{4}\b',     # 2345 6789 0123
        r'\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b',
        r'\b[2-9]\d{11}\b',                    # 234567890123
        r'\b\d{4}\s+\d{4}\s+\d{4}\b',
    ]
    
    for pattern in full_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        candidates.extend(matches)
    
    # 2. MASKED Aadhaar (All formats)
    masked_patterns = [
        r'\b[x*X]{4}\s*[x*X]{4}\s*[x*X]{4}\b',      # xxxx xxxx xxxx
        r'\bXXXX\s+XXXX\s+XXXX\b',
        r'\b[x*X]{8}\d{4}\b',                       # xxxxxxxx4052
        r'\b\d{4}[x*X]{8}\b',
        r'\b\d{4}\s*[x*X]{4}\s*\d{4}\b',
        r'\b[x*X]{4}\s*\d{4}\s*[x*X]{4}\b',
        r'\b\d{4}[x*X]{4}\d{4}\b',
        r'\b[x*X]{4,12}\b',
        r'\b\d{1,4}[x*X]{4,8}\d{1,4}\b',
        r'\b[x*X]{4}\.[x*X]{4}\.[x*X]{4}\b',
    ]
    
    for pattern in masked_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        candidates.extend(matches)
    
    # 3. Context-based
    context_patterns = [
        r'(?:aadhaar?|aadhar|आधार|uid)\s*[:\-]?\s*([x*X\d\s.-]{8,16})',
        r'(?:no\.?|number|नं)\s*[:\-]?\s*([x*X\d\s.-]{8,16})',
    ]
    for pattern in context_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        candidates.extend(matches)
    
    # 4. Score & Filter
    def score_candidate(candidate):
        cleaned = re.sub(r'[\s*xX*.]', '', candidate)
        total_len = len(re.sub(r'\s', '', candidate))
        digit_count = len(re.sub(r'[^\d]', '', candidate))
        x_count = candidate.lower().count('x') + candidate.count('*')
        
        score = 0
        if re.match(r'^\d{12}$', cleaned): score += 1000
        elif re.match(r'^\d{4}\s+\d{4}\s+\d{4}$', candidate): score += 900
        elif x_count >= 4: score += 500 + x_count * 10
        elif total_len >= 12: score += 300
        elif digit_count >= 8: score += 200
        
        return score if 8 <= total_len <= 16 and digit_count >= 2 else 0
    
    scored_candidates = [(score_candidate(c), c) for c in candidates if score_candidate(c) > 0]
    return max(scored_candidates, key=lambda x: x[0])[1] if scored_candidates else ""

# 🚀 ULTIMATE PAN Detection
def extract_pan(text: str) -> str:
    patterns = [
        r'\b[A-Z]{5}\d{4}[A-Z]\b',
        r'\b[A-Z]{4}\d{3}[A-Z]{2}\b',
        r'\b[A-Z*]{5}\d{4}[A-Z*]\b',
        r'\b[A-Z]{3}\*{2,4}[A-Z]?\d{4}[A-Z]?\b',
        r'\b[A-Z]{1,4}\*\d{4}[A-Z]\b',
        r'\b[A-Z]{5}\*{4}[A-Z]?\b',
        r'(?:pan|pancard)\s*[:\-]?\s*([A-Z*]{3,5}\d{4}[A-Z*]?)',
        r'(?:p\.?a\.?n\.?|पैन)\s*[:\-]?\s*([A-Z*]{3,5}\d{4}[A-Z]?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group().strip()
    return ""

def extract_pincode(text: str) -> str:
    patterns = [r'\b\d{6}\b', r'(?:pin|pincode)[:\s]*(\d{6})', r'\d{6}\s*(?:pin|pincode)']
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return ""

def extract_address(text: str, lines: list) -> str:
    keywords = ["address", "पता", "ward", "street", "गली", "road", "village", 
                "ग्राम", "pin", "dist", "district", "जिला"]
    
    for i, line in enumerate(lines):
        if any(kw in line.lower() for kw in keywords):
            addr_block = " ".join([lines[j].strip() for j in range(i, min(i+4, len(lines)))])
            pincode = extract_pincode(text)
            if pincode and pincode not in addr_block:
                addr_block += f", {pincode}"
            return addr_block[:200]
    
    candidates = [line for line in lines[:20] if 3 <= len(line.split()) <= 12]
    if candidates:
        base_addr = candidates[0]
        pincode = extract_pincode(text)
        if pincode and pincode not in base_addr:
            base_addr += f", {pincode}"
        return base_addr[:200]
    return ""

def extract_dob(text: str) -> str:
    patterns = [
        r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\b',
        r'\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2})\b',
        r'\b(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})\b',
        r'\b(\d{1,2}\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4})\b',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0]
    return ""

def extract_phone(text: str) -> str:
    patterns = [r'\b9\d{9}\b', r'\b\d{10}\b', r'\b\d{5}\s?\d{5}\b', r'\+91\s?\d{10}']
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return re.sub(r'\D', '', match.group())
    return ""

def extract_name(text: str, lines: list) -> str:
    if nlp_en:
        try:
            doc = nlp_en(text[:2000])
            persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                return max(persons, key=len)[:50]
        except:
            pass
    
    for line in lines[:10]:
        if re.match(r"^[A-Z][a-zA-Z\s\-\.]{5,50}$", line) and len(line.split()) >= 2:
            return line.strip()
    return ""

def extract_fields(text: str, detected_lang: str = "en", template: str = "standard"):
    result = {
        "full_name": "", "dob": "", "address": "", 
        "aadhaar": "", "pan": "", "phone": "", "language": detected_lang,
        "confidence": {}
    }
    
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 2]
    
    result["full_name"] = extract_name(text, lines)
    result["dob"] = extract_dob(text)
    result["address"] = extract_address(text, lines)
    result["aadhaar"] = extract_aadhaar(text)
    result["pan"] = extract_pan(text)
    result["phone"] = extract_phone(text)
    
    result["confidence"] = {
        "full_name": 1 if result["full_name"] else 0,
        "dob": 1 if result["dob"] else 0,
        "address": 1 if len(result["address"].split()) > 2 else 0,
        "aadhaar": 1 if result["aadhaar"] and len(result["aadhaar"]) >= 8 else 0,
        "pan": 1 if re.search(r'[A-Z]{3,5}\d{4}[A-Z*]?', result["pan"]) else 0,
        "phone": 1 if len(result["phone"]) == 10 else 0
    }
    
    template_config = FORM_TEMPLATES.get(template, FORM_TEMPLATES["standard"])
    template_fields = template_config["fields"]
    filtered_result = {k: result[k] for k in template_fields}
    filtered_result.update({
        "language": detected_lang,
        "template": template,
        "template_title": template_config["title"],
        "gov_links": template_config["gov_links"],  # 🚀 Fillable govt forms
        "confidence": result["confidence"]
    })
    return filtered_result

# 🚀 NEW: Auto-fill Govt Form Links endpoint
@app.post("/auto-fill-govt-form")
async def auto_fill_govt_form(template: str = Query("standard"), data: dict = None):
    """🚀 Generate pre-filled govt form links with extracted data"""
    template_config = FORM_TEMPLATES.get(template, FORM_TEMPLATES["standard"])
    fillable_links = [link for link in template_config["gov_links"] if link.get("fillable", False)]
    
    prefilled_links = []
    for link in fillable_links:
        # Add extracted data as query params (example structure)
        params = f"?name={data.get('full_name', '')}&dob={data.get('dob', '')}"
        prefilled_links.append({
            "name": link["name"],
            "original_url": link["url"],
            "prefilled_url": link["url"] + params if data else link["url"],
            "fillable": True
        })
    
    return {
        "template": template,
        "fillable_forms": prefilled_links,
        "total_fillable": len(prefilled_links)
    }

def create_filled_form_pdf(data: dict, template_name: str = "standard") -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    template_config = FORM_TEMPLATES.get(template_name, FORM_TEMPLATES["standard"])
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.darkblue)
    c.drawCentredText(width/2.0, height - 60, f"{template_config['title']} - FILLED")
    
    c.setFillColor(colors.black)
    c.line(50, height - 80, width - 50, height - 80)
    
    y_pos = height - 120
    c.setFont("Helvetica-Bold", 12)
    
    fields = [
        ("Full Name", data.get("full_name", "N/A")),
        ("Date of Birth", data.get("dob", "N/A")),
        ("Address", data.get("address", "N/A")[:100]),
        ("Aadhaar", data.get("aadhaar", "N/A")),
        ("PAN", data.get("pan", "N/A")),
        ("Phone", data.get("phone", "N/A"))
    ]
    
    for label, value in fields:
        if value != "N/A":
            c.drawString(60, y_pos, f"{label}:")
            c.setFont("Helvetica-Bold", 11)
            c.drawString(180, y_pos, str(value))
            y_pos -= 30
    
    # Govt Fillable Forms Section
    y_pos -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y_pos, "🚀 FILLABLE GOVT FORMS:")
    y_pos -= 15
    c.setFont("Helvetica", 9)
    fillable_count = 0
    for link in data.get("gov_links", [])[:4]:
        if link.get("fillable", False):
            c.drawString(70, y_pos, f"• {link['name']}")
            y_pos -= 12
            fillable_count += 1
    
    c.setFont("Helvetica", 8)
    c.drawString(70, y_pos, f"{fillable_count} forms ready to fill with your data!")
    
    c.setFont("Helvetica", 10)
    c.drawCentredText(width/2.0, 50, "Generated by AI Form Filling Assistant Pro")
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

@app.get("/health")
async def health_check():
    return {"status": "alive"}

@app.post("/process")
async def process_document(file: UploadFile = File(...), template: str = Query("standard")):
    try:
        if not file.filename:
            return JSONResponse(status_code=400, content={"status": "error", "message": "No file"})
        
        contents = await file.read()
        filename = file.filename.lower()
        is_pdf = filename.endswith('.pdf')
        
        images = []
        temp_file = None
        try:
            if is_pdf:
                temp_file = f"temp_{os.urandom(8).hex()}.pdf"
                with open(temp_file, "wb") as f:
                    f.write(contents)
                images = pdf_to_images(temp_file)
            else:
                image = Image.open(io.BytesIO(contents))
                images = [preprocess_image(image)]
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
        
        full_text = ""
        for img in images:
            try:
                text = pytesseract.image_to_string(img, config='--psm 6')
                full_text += text + "\n"
            except:
                full_text += "OCR_FAILED\n"
        
        if not full_text.strip():
            return JSONResponse(status_code=400, content={
                "status": "error", 
                "message": "No text detected. Check Tesseract installation.",
                "filled_form": {}
            })
        
        lang = detect_language(full_text)
        extracted = extract_fields(full_text, lang, template)
        extracted["filename"] = file.filename
        extracted["page_count"] = len(images)
        extracted["raw_text_preview"] = full_text[:500]
        
        return {
            "status": "success",
            "filename": file.filename,
            "language": lang,
            "page_count": len(images),
            "template": template,
            "filled_form": extracted
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e), "filled_form": {}}
        )

@app.get("/download/{session_id}")
async def download_form(session_id: str, template: str = Query("standard")):
    demo_data = {
        "full_name": "Rahul Sharma", 
        "dob": "15/08/1990", 
        "address": "House 123, MG Road, Dispur, Assam - 781006",
        "aadhaar": "xxxx xxxx 4052",
        "pan": "ABCDE1234F",
        "phone": "9876543210",
        "gov_links": FORM_TEMPLATES[template]["gov_links"]
    }
    pdf_bytes = create_filled_form_pdf(demo_data, template)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={template}_form.pdf"}
    )

@app.get("/templates")
async def get_templates():
    templates_list = []
    for key, config in FORM_TEMPLATES.items():
        fillable_count = len([link for link in config["gov_links"] if link.get("fillable", False)])
        templates_list.append({
            "id": key,
            "title": config["title"],
            "fields": config["fields"],
            "gov_links_count": len(config["gov_links"]),
            "fillable_forms": fillable_count  # 🚀 NEW: Count of fillable forms
        })
    return {"templates": templates_list}

# Frontend
FRONTEND_DIR = "frontend"
os.makedirs(FRONTEND_DIR, exist_ok=True)
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
