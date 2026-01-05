import spacy
import re

nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    doc = nlp(text)
    entities = {}

    for ent in doc.ents:
        entities[ent.label_] = ent.text

    # Extract Aadhaar number if present
    aadhaar = re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", text)
    if aadhaar:
        entities["AADHAAR"] = aadhaar.group()

    return entities
