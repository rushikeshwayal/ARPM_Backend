from fastapi import  UploadFile, File, APIRouter
import requests
import os
from dotenv import load_dotenv
import json


from Agent.Main.Agent import OCRCorrectionAgent

load_dotenv()

router = APIRouter(prefix="/Agent", tags=["Agents"])

# Initialize agent once
agent = OCRCorrectionAgent()

OCR_API_URL = "http://127.0.0.1:8080/ocr"


@router.post("/process-pdf")
async def process_pdf(file: UploadFile = File(...)):

    # -----------------------------
    # 1️⃣ Send PDF to OCR API
    # -----------------------------
    files = {
        "file": (file.filename, await file.read(), "application/pdf")
    }

    ocr_response = requests.post(OCR_API_URL, files=files)

    if ocr_response.status_code != 200:
        return {"error": "OCR service failed"}

    extracted_text = ocr_response.json().get("extracted_text")

    if not extracted_text:
        return {"error": "No text extracted"}

    # -----------------------------
    # 2️⃣ Send text to AI Agent
    # -----------------------------
    corrected_text = agent.correct_text(extracted_text)

    # -----------------------------
    # 3️⃣ Return Final Output
    # -----------------------------
    result = agent.correct_text(corrected_text)
    result = result.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(result)
    
    return parsed