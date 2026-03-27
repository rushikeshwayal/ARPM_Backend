from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
from Agent.Main.Prompt import get_ocr_correction_prompt


class OCRCorrectionAgent:
    def __init__(self, model_name="gemini-2.5-flash"):
        load_dotenv()

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

        self.prompt = get_ocr_correction_prompt()
        self.chain = self.prompt | self.llm | StrOutputParser()

    def correct_text(self, text: str) -> str:
        return self.chain.invoke({"text": text})