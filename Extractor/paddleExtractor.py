import fitz  # PyMuPDF
from paddleocr import PaddleOCR
import os

# -------------------------------
# STEP 1: Convert PDF to images
# -------------------------------
def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=300)
        img_path = f"page_{page_num}.png"
        pix.save(img_path)
        image_paths.append(img_path)

    return image_paths


# -------------------------------
# STEP 2: OCR using PaddleOCR
# -------------------------------
def extract_text(image_paths):
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    full_text = ""

    for img_path in image_paths:
        result = ocr.ocr(img_path)

        lines = []
        for line in result[0]:
            text = line[1][0]
            lines.append(text)

        # Merge lines nicely
        page_text = "\n".join(lines)
        full_text += page_text + "\n\n"

    return full_text


# -------------------------------
# STEP 3: Simple Cleanup
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
# STEP 4: Create Clean PDF
# -------------------------------
def create_pdf(text, output_file="output.pdf"):
    doc = fitz.open()
    page = doc.new_page()

    rect = fitz.Rect(50, 50, 550, 800)
    page.insert_textbox(rect, text, fontsize=12)

    doc.save(output_file)
    doc.close()


# -------------------------------
# MAIN EXECUTION
# -------------------------------
if __name__ == "__main__":
    input_pdf = "./Extractor/NOC.pdf"

    print("📄 Converting PDF to images...")
    images = pdf_to_images(input_pdf)

    print("🔍 Running PaddleOCR...")
    raw_text = extract_text(images)

    print("🧹 Cleaning text...")
    final_text = clean_text(raw_text)

    print("Raw Txt:  ",final_text)
    print("📝 Generating new PDF...")
    create_pdf(final_text)
    print("✅ Done! Output saved as output.pdf")