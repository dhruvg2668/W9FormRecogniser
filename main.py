from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
from dotenv import load_dotenv
from form_processor import FormProcessor  # Renamed from calloutManager.py
from tempfile import NamedTemporaryFile

load_dotenv()
app = FastAPI()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")

if not AZURE_ENDPOINT or not AZURE_API_KEY:
    raise ValueError("Azure credentials missing in .env")

processor = FormProcessor(endpoint=AZURE_ENDPOINT, key=AZURE_API_KEY)

@app.post("/extract_w9")
async def extract_w9_data(request: Request):
    try:
        binary_data = await request.body()
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(binary_data)
            temp_path = temp_file.name
        extracted_data = processor.process_form(temp_path)
        os.remove(temp_path)
        return JSONResponse(content={"extracted_data": extracted_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
