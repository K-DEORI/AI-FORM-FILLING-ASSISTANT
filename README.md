# 🧠 AI Form Filling Assistant Pro

An AI-powered system that extracts personal information from scanned documents (PDFs / Images) and auto-fills Indian government form data such as Aadhaar, PAN, Passport, Voter ID, Income Tax, and Driving Licence.

Built using **FastAPI, OCR (Tesseract), NLP (spaCy)** with robust, label-independent field detection.

---

## 🚀 Features

- OCR for PDF, JPG, PNG
- Works **with or without field labels**
- Aadhaar (masked & unmasked) detection
- Name, DOB, Address, PAN, Phone extraction
- Government form templates with fillable links
- Download filled PDF forms
- Language detection
- Confidence scoring per field

---



## 🛠️ Tech Stack

**Backend:**Python, FastAPI, Tesseract OCR, spaCy, PyMuPDF, ReportLab  
**Frontend:** HTML, CSS, JavaScript  

---

## Dependencies

All Python dependencies are listed in `backend/requirements.txt`.

### Core Backend
- **FastAPI** – REST API framework
- **Uvicorn** – ASGI server
- **python-multipart** – File upload handling

### OCR & Document Processing
- **pytesseract** – OCR engine wrapper
- **Pillow** – Image processing
- **pdfplumber** – PDF text extraction

### NLP & AI
- **spaCy** – Named Entity Recognition (NER)
- **whisper** – Optional speech-to-text support (future-ready)

### Document Generation
- **reportlab** – Generate filled PDF forms

---

## ⚙️ Setup Instructions

#### 1️⃣ Clone Repository
```bash
git clone https://github.com/K-DEORI/AI-FORM-FILLING-ASSISTANT.git
cd AI-FORM-FILLING-ASSISTANT
```

#### 2️⃣ Create Virtual Environment
```bash
Copy code:

python -m venv venv

venv\Scripts\activate
```
- terminal should display something like this: (venv) PS D:\Intel\ai-form-filling-assistant>
- then run: cd backend

![demo video](./screenshots/Recording 2026-01-05 201426.mp4)

#### 3️⃣ Install Dependencies
```bash
Copy code
pip install -r backend/requirements.txt
```

#### 4️⃣ Install Tesseract OCR (Windows)
Download from:
https://github.com/UB-Mannheim/tesseract/wiki

##### Install path:

makefile
Copy code
C:\Program Files\Tesseract-OCR\tesseract.exe
Ensure the following line exists in main.py:

python
Copy code
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


#### 5️⃣ Install spaCy Model
```bash
Copy code
python -m spacy download en_core_web_sm
```

#### 6️⃣ Run Backend Server
```bash
Copy code and run it in terminal:
python -m uvicorn app.main:app --reload

Backend URL:
Copy code
http://127.0.0.1:8000
```

#### 7️⃣ Open Frontend
Open the following file in your browser:

```bash
Copy code
frontend/index.html
```
- use live server by downloading it in extensions
- right click on index.html and click open with live server

#### 📡 API Endpoints
- GET /health – Health check
- POST /process?template=standard – Process document
- GET /templates – Available form templates
- GET /download/{session_id} – Download filled PDF
- POST /auto-fill-govt-form – Prefilled government form links

#### 📄 Supported Forms
- Aadhaar
- PAN
- Passport
- Voter ID
- Income Tax
- Driving Licence

#### 🧠 Extraction Strategy
- Regex-based ID detection
- NLP (NER) for name extraction
- Heuristic multi-line address detection
- Works even when labels are missing or reordered

#### 🔒 Privacy
- No permanent file storage
- Temporary files auto-deleted
- Sensitive folders ignored via .gitignore

#### 📌 Future Improvements
- OCR language expansion (Hindi, Assamese)
- Online PDF form auto-filling
- Authentication & user sessions
- ML-based address segmentation
- Cloud deployment (Docker / AWS)

## License
This project is licensed under the MIT License.

### Author

