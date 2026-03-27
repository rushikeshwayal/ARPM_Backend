from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os
import fitz
from paddleocr import PaddleOCR

app = FastAPI(title="OCR")

ocr = PaddleOCR(use_angle_cls=True, lang="en")


# -------------------------------
# Convert PDF to Images
# -------------------------------
def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=300)
        img_path = f"temp_page_{page_num}.png"
        pix.save(img_path)
        image_paths.append(img_path)

    return image_paths


# -------------------------------
# OCR
# -------------------------------
def extract_text(image_paths):
    full_text = ""

    for img_path in image_paths:
        result = ocr.ocr(img_path)

        lines = []
        for line in result[0]:
            text = line[1][0]
            lines.append(text)

        page_text = "\n".join(lines)
        full_text += page_text + "\n\n"

        os.remove(img_path)  # cleanup temp image

    return full_text


# -------------------------------
# Clean Text
# -------------------------------
def clean_text(text):
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if len(line) > 1:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# -------------------------------
# API Endpoint
# -------------------------------
@app.post("/ocr")
async def run_ocr(file: UploadFile = File(...)):
    temp_pdf = "temp_upload.pdf"

    # Save uploaded file
    with open(temp_pdf, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR Pipeline
    images = pdf_to_images(temp_pdf)
    raw_text = extract_text(images)
    final_text = clean_text(raw_text)

    os.remove(temp_pdf)

    return JSONResponse(content={
        "extracted_text": final_text
    })