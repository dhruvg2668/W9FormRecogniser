import os
import sys
import base64
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from app.services.city_state_extraction import extract_city_state_zip
import logging
import re

load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

STATE_NAME_TO_ABBR = {
    # US States
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", 
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
    
    # Indian States
    "Rajasthan": "RJ",
    "Andhra Pradesh": "AP", "Arunachal Pradesh": "AR", "Assam": "AS", "Bihar": "BR", 
    "Chhattisgarh": "CG", "Goa": "GA", "Gujarat": "GJ", "Haryana": "HR", 
    "Himachal Pradesh": "HP", "Jharkhand": "JH", "Karnataka": "KA", "Kerala": "KL", 
    "Madhya Pradesh": "MP", "Maharashtra": "MH", "Manipur": "MN", "Meghalaya": "ML", 
    "Mizoram": "MZ", "Nagaland": "NL", "Odisha": "OD", "Punjab": "PB", 
    "Sikkim": "SK", "Tamil Nadu": "TN", "Telangana": "TG", "Tripura": "TR", 
    "Uttar Pradesh": "UP", "Uttarakhand": "UK", "West Bengal": "WB"
}

# List of US States (Full Names and Abbreviations)
STATES = {
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia","Rajasthan",
    "Wisconsin", "Wyoming", "District of Columbia"
}

STATE_ABBREVIATIONS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
    "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT","RJ",
    "VA", "WA", "WV", "WI", "WY", "DC"
}

INDIAN_STATES = {
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal"
}

# Create combined sets for easier validation
ALL_STATES = STATES.union(STATE_ABBREVIATIONS).union(INDIAN_STATES)

def parse_address(address_str):
    """
    Parses an address string and extracts City, State, and Zip Code.
    
    :param address_str: A string containing city, state, and zip code.
    :return: A dictionary with 'City', 'State', and 'ZipCode' or an error message.
    """
    result = {
        "City": {"value": None, "confidence": None},
        "State": {"value": None, "confidence": None},
        "ZipCode": {"value": None, "confidence": None}
    }
    
    if not address_str:
        return result
    
    # First, try to extract the zip code from the end of the string
    zip_pattern = re.compile(r'(\d{5,6}(?:-\d{4})?)$')
    zip_match = zip_pattern.search(address_str)
    
    if not zip_match:
        logger.warning(f"No valid ZIP code found in: {address_str}")
        return result
    
    zip_code = zip_match.group(1)
    result["ZipCode"]["value"] = zip_code
    
    # Remove the zip code from the original string
    address_without_zip = address_str[:zip_match.start()].strip()
    
    # Now try to find a valid state in what's left
    remaining_parts = address_without_zip.replace(",", " ").split()
    
    # Try to find valid state working backwards
    state_found = False
    for i in range(len(remaining_parts), 0, -1):
        # Check individual words
        if remaining_parts[i-1] in ALL_STATES:
            state = remaining_parts[i-1]
            city = " ".join(remaining_parts[:i-1])
            state_found = True
            break
        
        # Check two-word states (like New York)
        if i >= 2 and " ".join(remaining_parts[i-2:i]) in ALL_STATES:
            state = " ".join(remaining_parts[i-2:i])
            city = " ".join(remaining_parts[:i-2])
            state_found = True
            break
        
        # Check three-word states (like North/South Carolina/Dakota)
        if i >= 3 and " ".join(remaining_parts[i-3:i]) in ALL_STATES:
            state = " ".join(remaining_parts[i-3:i])
            city = " ".join(remaining_parts[:i-3])
            state_found = True
            break
    
    if state_found:
        result["City"]["value"] = city.strip()
        # Convert state name to abbreviation if it's a full name
        if state in STATE_NAME_TO_ABBR:
            result["State"]["value"] = STATE_NAME_TO_ABBR[state]
        # If it's already an abbreviation, keep it as is
        elif state in STATE_ABBREVIATIONS:
            result["State"]["value"] = state
        # Otherwise, store the original value
        else:
            result["State"]["value"] = state
    else:
        logger.warning(f"No valid state found in: {address_without_zip}")
    
    return result

class W9FormExtraction:
    def __init__(self):
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT")
        self.azure_api_key = os.getenv("AZURE_API_KEY")

    def client(self):
        """Initialize Azure Form Recognizer client"""
        return DocumentAnalysisClient(self.azure_endpoint, AzureKeyCredential(self.azure_api_key))

    def extract_form_data(self, pdf_path):
        try:
            document_ai_client = self.client()
            with open(pdf_path, "rb") as file:
                poller = document_ai_client.begin_analyze_document("prebuilt-document", document=file)
            result = poller.result(timeout=30)
            
            extracted_json = {}
            for kv_pair in result.key_value_pairs:
                key = kv_pair.key.content.strip() if kv_pair.key and kv_pair.key.content else None
                value = kv_pair.value.content.strip() if kv_pair.value and kv_pair.value.content else None
                confidence = kv_pair.confidence
                
                if key:
                    extracted_json[key] = {"value": value, "confidence": confidence}
            
            logger.info(f"Extracted JSON: {extracted_json}")
            formatted_json = format_extracted_json(result, extracted_json)
            return formatted_json
        except Exception as e:
            logger.error(f"Error extracting form: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error extracting form: {str(e)}")


def format_extracted_json(result, extracted_json):
    try:
        pattern = r"\bRev\.\s*([A-Za-z]+)\s*(\d{4})"
        match = re.search(pattern, result.content, re.IGNORECASE)
        revision = f"{match.group(1)} {match.group(2)}" if match else ""
        
        formatted_json = {
            "Entity Name": {"value": None, "confidence": None},
            "Business Name": {"value": None, "confidence": None},
            "Address": {"value": None, "confidence": None},
            "City": {"value": None, "confidence": None},
            "State": {"value": None, "confidence": None},
            "ZipCode": {"value": None, "confidence": None},
            "SSN": {"value": None, "confidence": None},
            "EIN": {"value": None, "confidence": None},
            "Date": {"value": None, "confidence": None},
            "Signature": {"value": None, "confidence": None},
            "W9 Form Revision": revision
        }

        for k, v in extracted_json.items():
            if "Name" in k:
                formatted_json["Entity Name"]["value"] = v["value"]
                formatted_json["Entity Name"]["confidence"] = v["confidence"]
            elif "Business name" in k:
                formatted_json["Business Name"]["value"] = v["value"]
                formatted_json["Business Name"]["confidence"] = v["confidence"]
            elif "City, state, and ZIP code" in k:
                parsed_address = extract_city_state_zip(v["value"])  # Use AWS Bedrock
                confidence = v["confidence"]
                if parsed_address:
                    formatted_json["City"] = {"value": parsed_address.get("City", None), "confidence": confidence}
                    formatted_json["State"] = {"value": parsed_address.get("State", None), "confidence": confidence}
                    formatted_json["ZipCode"] = {"value": parsed_address.get("Zip Code", None), "confidence": confidence}
                else:
                    Logger.warning(f"Bedrock failed to parse City/State/Zip from: {v['value']}")
            elif "Employer identification number" in k:
                formatted_json["EIN"]["value"] = v["value"]
                formatted_json["EIN"]["confidence"] = v["confidence"]
            elif "Social security number" in k:
                formatted_json["SSN"]["value"] = v["value"]
                formatted_json["SSN"]["confidence"] = v["confidence"]
            elif "Date" in k:
                # Format the date as YYYY-MM-DD (with hyphens)
                if v["value"]:
                    original_date = v["value"].strip()
                    logger.info(f"Attempting to parse date: {original_date}")
                    
                    try:
                        # First try a direct approach for the most common formats
                        date_str = original_date
                        
                        # Specific handling for "Month DD, YYYY" format (including abbreviated months)
                        month_pattern = re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})', re.IGNORECASE)
                        month_match = month_pattern.search(date_str)
                        
                        if month_match:
                            logger.info(f"Found month pattern match: {month_match.groups()}")
                            month_abbr = month_match.group(1).lower()
                            day = int(month_match.group(2))
                            year = month_match.group(3)
                            
                            # Map month abbreviation to number
                            month_map = {
                                "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
                                "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"
                            }
                            
                            month = month_map.get(month_abbr.lower())
                            if month:
                                formatted_date = f"{year}-{month}-{str(day).zfill(2)}"
                                logger.info(f"Successfully parsed date to: {formatted_date}")
                                formatted_json["Date"]["value"] = formatted_date
                            else:
                                logger.warning(f"Could not map month abbreviation: {month_abbr}")
                                formatted_json["Date"]["value"] = original_date
                        else:
                            # If the specific pattern didn't match, try standard datetime parsing
                            from datetime import datetime
                            
                            # Common date formats to try
                            date_formats = [
                                "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y", "%B %d, %Y",
                                "%d %B %Y", "%Y/%m/%d", "%Y-%m-%d", "%d.%m.%Y", "%m.%d.%Y", "%Y.%m.%d",
                                "%m-%d-%y", "%d-%m-%y", "%m/%d/%y", "%d/%m/%y", 
                                "%b %d, %Y", "%d %b %Y", "%b %d %Y", "%Y %b %d"
                            ]
                            
                            parsed_date = None
                            
                            for fmt in date_formats:
                                try:
                                    logger.info(f"Trying format: {fmt}")
                                    parsed_date = datetime.strptime(date_str, fmt)
                                    logger.info(f"Success with format: {fmt}")
                                    break
                                except ValueError:
                                    continue
                            
                            if parsed_date:
                                # Format in YYYY-MM-DD with hyphens
                                formatted_date = parsed_date.strftime("%Y-%m-%d")
                                logger.info(f"Successfully parsed date to: {formatted_date}")
                                formatted_json["Date"]["value"] = formatted_date
                            else:
                                # Last resort: try to extract just digits
                                logger.warning(f"All standard date parsing failed for: {date_str}")
                                digits = re.findall(r'\d+', date_str)
                                
                                if len(digits) == 3:
                                    logger.info(f"Found 3 digits: {digits}")
                                    # Assume day, month, year if first number is ≤ 31 and second is ≤ 12
                                    if len(digits[0]) <= 2 and int(digits[0]) <= 31 and len(digits[1]) <= 2 and int(digits[1]) <= 12:
                                        # Make sure year is 4 digits
                                        year = digits[2]
                                        if len(year) == 2:
                                            prefix = "20" if int(year) < 50 else "19"
                                            year = prefix + year
                                        
                                        day = digits[0].zfill(2)
                                        month = digits[1].zfill(2)
                                        formatted_date = f"{year}-{month}-{day}"
                                        logger.info(f"Parsed from digits to: {formatted_date}")
                                        formatted_json["Date"]["value"] = formatted_date
                                    else:
                                        logger.warning(f"Digit pattern didn't match expected ranges")
                                        formatted_json["Date"]["value"] = original_date
                                else:
                                    logger.warning(f"Could not parse date: {date_str}")
                                    formatted_json["Date"]["value"] = original_date
                    
                    except Exception as e:
                        logger.error(f"Error parsing date {original_date}: {str(e)}")
                        formatted_json["Date"]["value"] = original_date
                formatted_json["Date"]["confidence"] = v["confidence"]       
            elif "Signature" in k:
                formatted_json["Signature"]["value"] = v["value"]
                formatted_json["Signature"]["confidence"] = v["confidence"]
            elif "Address" in k:
                formatted_json["Address"]["value"] = v["value"]
                formatted_json["Address"]["confidence"] = v["confidence"]
        
        return formatted_json
    except Exception as e:
        logger.error(f"Error during formatting: {str(e)}")
        return {"error": f"Error during formatting: {str(e)}"}

class FileBase64Request(BaseModel):
    file_base64: str

@app.post("/extract-w9")
async def extract_w9(request: FileBase64Request):
    try:
        file_bytes = base64.b64decode(request.file_base64)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(file_bytes)
            temp_pdf_path = temp_pdf.name
        
        extractor = W9FormExtraction()
        result = extractor.extract_form_data(temp_pdf_path)
        os.remove(temp_pdf_path)  # Clean up temp file
        return {"extracted_data": result}
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
