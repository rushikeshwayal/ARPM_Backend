import requests
import json

from Agent.Main.Agent import OCRCorrectionAgent
from Budget_Document.model import BudgetDocument
from database import SessionLocal

OCR_API_URL = "http://127.0.0.1:8080/ocr"

agent = OCRCorrectionAgent()


async def generate_doc_summary(doc_id: int, file_bytes: bytes, filename: str):

    async with SessionLocal() as db:  # ✅ FIXED
        try:
            # 1️⃣ OCR
            ocr_response = requests.post(
                OCR_API_URL,
                files={"file": (filename, file_bytes, "application/pdf")}
            )

            if ocr_response.status_code != 200:
                return

            extracted_text = ocr_response.json().get("extracted_text")
            if not extracted_text:
                return

            # 2️⃣ LLM
            result = agent.correct_text(extracted_text)
            result = result.replace("```json", "").replace("```", "").strip()

            parsed = json.loads(result)

            # 3️⃣ Update DB
            doc = await db.get(BudgetDocument, doc_id)

            if doc:
                doc.doc_summary = parsed.get("summary")
                await db.commit()

        except Exception as e:
            print(f"❌ Summary failed for doc {doc_id}: {str(e)}")