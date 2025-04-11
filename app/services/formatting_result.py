import re
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))  #needed for streamlit to identify relative system paths
from app.configuration.logger_setup import Logger  #add any module imports after  the above line


def format_extracted_json(result, extracted_json):
    try:
        pattern = r"\bRev\.\s*([A-Za-z]+)\s*(\d{4})"
        match = re.search(pattern, result.content, re.IGNORECASE)
        if match:
            revision = f"Rev. {match.group(1)} {match.group(2)}"
        else:
               revision = ""
        formatted_json = {
                                "Entity Name" :{
                                        "value":None,
                                        "confidence":None
                                },
                                "Business Name" :{
                                        "value":None,
                                        "confidence":None
                                },
                                "Address" :{
                                        "value":None,
                                        "confidence":None
                                },
                                "City/State/Zip Code" :{
                                        "value":None,
                                        "confidence":None
                                },
                                "SSN" :{
                                        "value":None,
                                        "confidence":None
                                },
                                "EIN" :{
                                        "value":None,
                                        "confidence":None
                                },
                                "Date" :{
                                        "value":None,
                                        "confidence":None
                                },
                                "Signature":{
                                      "value":None,
                                    "confidence":None
                                },
                                "Address": {
                                        "value":None,
                                    "confidence":None
                                },
                                
                                "W9 Form Revision" : revision
                        }
        
 
        for k,v in extracted_json.items():
                    
                    if "Name" in k:
                            formatted_json["Entity Name"]["value"] = v["value"]
                            formatted_json["Entity Name"]["confidence"] = v["confidence"]

                    elif "Business name" in k:
                            formatted_json["Business Name"]["value"] = v["value"]
                            formatted_json["Business Name"]["confidence"] = v["confidence"]

                    elif "City, state, and ZIP code" in k:
                            formatted_json["City/State/Zip Code"]["value"] = v["value"]
                            formatted_json["City/State/Zip Code"]["confidence"] = v["confidence"]

                    elif "Employer identification number" in k:
                        formatted_json["EIN"]["value"] = v["value"]
                        formatted_json["EIN"]["confidence"] = v["confidence"]

                    elif "Social security number" in k:
                        formatted_json["SSN"]["value"] = v["value"]
                        formatted_json["SSN"]["confidence"] = v["confidence"]
                    
                    elif "Date" in k:
                        formatted_json["Date"]["value"] = v["value"]
                        formatted_json["Date"]["confidence"] = v["confidence"]

                    elif "Signature" in k:
                        formatted_json["Signature"]["value"] = v["value"]
                        formatted_json["Signature"]["confidence"] = v["confidence"]

                    elif "Address" in k:
                        formatted_json["Address"]["value"] = v["value"]
                        formatted_json["Address"]["confidence"] = v["confidence"]

        return formatted_json

    except Exception as e:
          Logger.error(f"got error during formatting: {str(e)}")
          return f"Error occurred during formatting: {str(e)}"