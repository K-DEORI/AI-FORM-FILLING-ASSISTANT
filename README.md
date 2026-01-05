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

## 🏗️ Project Structure

ai-form-filling-assistant/
│
├── backend/
│ ├── app/
│ │ ├── main.py
│ │ ├── ocr.py
│ │ ├── ner.py
│ │ ├── utils.py
│ │ ├── form_mapper.py
│ │ └── voice.py
│ ├── requirements.txt
│
├── frontend/
│ ├── index.html
│ ├── style.css
│ └── script.js
│
├── uploads/ # ignored
├── output/ # ignored
├── docs/
│
├── README.md
├── .gitignore
└── venv/ # ignored

yaml
Copy code

---

## 🛠️ Tech Stack

**Backend:**Python, FastAPI, Tesseract OCR, spaCy, PyMuPDF, ReportLab  
**Frontend:** HTML, CSS, JavaScript  

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository
```bash
git clone https://github.com/K-DEORI/AI-FORM-FILLING-ASSISTANT.git
cd AI-FORM-FILLING-ASSISTANT


2️⃣ Create Virtual Environment
bash
Copy code
python -m venv venv
venv\Scripts\activate


3️⃣ Install Dependencies
bash
Copy code
pip install -r backend/requirements.txt


4️⃣ Install Tesseract OCR (Windows)
Download from:
https://github.com/UB-Mannheim/tesseract/wiki

Install path:

makefile
Copy code
C:\Program Files\Tesseract-OCR\tesseract.exe
Ensure the following line exists in main.py:

python
Copy code
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


5️⃣ Install spaCy Model
bash
Copy code
python -m spacy download en_core_web_sm


6️⃣ Run Backend Server
bash
Copy code
uvicorn backend.app.main:app --reload
Backend URL:

cpp
Copy code
http://127.0.0.1:8000


7️⃣ Open Frontend
Open the following file in your browser:

bash
Copy code
frontend/index.html


📡 API Endpoints
GET /health – Health check

POST /process?template=standard – Process document

GET /templates – Available form templates

GET /download/{session_id} – Download filled PDF

POST /auto-fill-govt-form – Prefilled government form links

📄 Supported Forms
Aadhaar

PAN

Passport

Voter ID

Income Tax

Driving Licence

🧠 Extraction Strategy
Regex-based ID detection

NLP (NER) for name extraction

Heuristic multi-line address detection

Works even when labels are missing or reordered

🔒 Privacy
No permanent file storage

Temporary files auto-deleted

Sensitive folders ignored via .gitignore



