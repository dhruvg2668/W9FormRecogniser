import tempfile
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from app.services.form_extraction import W9FormExtraction
from app.configuration.logger_setup import Logger

router = APIRouter()
w9_form_extractor = W9FormExtraction()

@router.post("/")
def extract_w9_form_data(file: UploadFile = File(...)):

    try:

        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file.file.read())  
            temp_file_path = temp_file.name 

        Logger.info("✅ PDF Uploaded Successfully. Extracting data now...")
        extracted_data = w9_form_extractor.extract_form_data(temp_file_path)
        Logger.info("✅ Data Extraction Complete.")
  
        Path(temp_file_path).unlink(missing_ok=True)

        return JSONResponse(content=extracted_data)

       
    
    except Exception as e:
        print (f" Error occurred: {str(e)}")
        return f"An error occurred : {str(e)}"

