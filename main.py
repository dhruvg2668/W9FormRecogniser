from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

import os

app = FastAPI()
load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")

if not AZURE_ENDPOINT or not AZURE_API_KEY:
    raise ValueError("Azure endpoint or key is missing. Check your .env file.")
  
document_analysis_client = DocumentAnalysisClient(
    AZURE_ENDPOINT, AzureKeyCredential(AZURE_API_KEY)
)

@app.post("/extract_w9")
async def extract_w9_data(request: Request):
    try:
        contents = await request.body()
        poller = document_analysis_client.begin_analyze_document("prebuilt-document", document=contents)
        result = poller.result()
        extracted_data = {}
        for kv_pair in result.key_value_pairs:
            key = kv_pair.key.content.strip() if kv_pair.key else None
            value = kv_pair.value.content.strip() if kv_pair.value else None
            if key and value:
                extracted_data[key] = value
        return JSONResponse(content={"extracted_data": extracted_data})
    except Exception as e:
        print("Error occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
