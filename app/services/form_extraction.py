import os
import sys
from pathlib import Path
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))  #needed for streamlit to identify relative system paths
from app.services.formatting_result import format_extracted_json     #add any module imports after  the above line
from app.configuration.logger_setup import Logger
load_dotenv()

class W9FormExtraction:

    def __init__ (self):
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT")
        self.azure_api_key= os.getenv("AZURE_API_KEY")

    def client(self):
        """Initialize Azure Form Recognizer client"""
        return DocumentAnalysisClient(self.azure_endpoint, AzureKeyCredential(self.azure_api_key))
    
    def extract_form_data(self, pdf_path):
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return {"error": "PDF file not found"}
        
       
        try:
            document_ai_client = self.client()

            with open(pdf_path, "rb") as file:
                poller = document_ai_client.begin_analyze_document("prebuilt-document", document=file)
            
            result = poller.result(timeout=30) 
           
            extracted_json = {}


            for index, kv_pair in enumerate(result.key_value_pairs):
                key = kv_pair.key.content.strip() if kv_pair.key and kv_pair.key.content else None
                value = kv_pair.value.content.strip() if kv_pair.value and kv_pair.value.content else None
                confidence = kv_pair.confidence
                
                if key:
                    extracted_json[key] = {
                       "value" : value,
                       "confidence" : confidence
                    }

            Logger.info(f"printing extracted json:{extracted_json}")
            formatted_json = format_extracted_json(result, extracted_json)

            return formatted_json

        except Exception as e:
            import traceback
            error_message = traceback.format_exc()
            print("An error occured during processing:", error_message) 
            return {"error": f"Error extracting form: {str(e)}"}
