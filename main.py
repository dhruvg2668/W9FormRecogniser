from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from dotenv import load_dotenv
import tempfile
import os
from typing import Dict
import json

app = FastAPI()
load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")

if not AZURE_ENDPOINT or not AZURE_API_KEY:
    raise ValueError("Azure endpoint or key is missing. Check your .env file.")

document_analysis_client = DocumentAnalysisClient(
    AZURE_ENDPOINT, AzureKeyCredential(AZURE_API_KEY)
)


def process_w9_from_bytes(file_bytes: bytes) -> Dict:
    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-document", document=file_bytes
    )
    result = poller.result()

    extracted_data = {}
    for kv_pair in result.key_value_pairs:
        key = kv_pair.key.content.strip() if kv_pair.key else None
        value = kv_pair.value.content.strip() if kv_pair.value else None
        if key and value:
            extracted_data[key] = value

    return extracted_data


@app.post("/extract_w9")
async def extract_w9_data(request: Request):
    try:
        file_bytes = await request.body()

        # Optional: Save for debugging or logging
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        # Process the file bytes
        extracted_data = process_w9_from_bytes(file_bytes)

        return JSONResponse(content={"extracted_data": extracted_data})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
