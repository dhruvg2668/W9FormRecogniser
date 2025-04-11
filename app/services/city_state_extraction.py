import json
import boto3
import os
import sys
import botocore.config
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.configuration.logger_setup import Logger

# Initialize AWS Bedrock Client
session = boto3.Session(
    aws_access_key_id=os.getenv("aws_access_key_id"),
    aws_secret_access_key=os.getenv("aws_secret_access_key"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

bedrock_client = session.client(
    "bedrock-runtime",
    region_name="us-east-1",
    config=botocore.config.Config(read_timeout=120)
)

def extract_city_state_zip(text):
    """
    Uses AWS Bedrock's Claude 3 API to extract and separate City, State, and Zip Code.
    """
    messages = [
    {"role": "user", "content": f"Extract and separate City, State, and Zip Code from the following address:\n\n{text}\n\nReturn the output strictly in JSON format like this:\n\n{{\n    \"City\": \"Extracted City\",\n    \"State\": \"Extracted State Abbreviation\",\n    \"Zip Code\": \"Extracted Zip Code\"\n}}\n\nIMPORTANT: For the State field, please return the two-letter state abbreviation (e.g., 'CA' for California, 'NY' for New York) instead of the full state name."}
    ]

    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"  # Make sure this model ID exists in your AWS region

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",  # REQUIRED for Claude 3 in AWS Bedrock
        "messages": messages,
        "max_tokens": 200,
        "temperature": 0.2
    }

    try:
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )

        result = json.loads(response["body"].read().decode("utf-8"))
        Logger.info(f"Bedrock raw response: {result}")

        if "content" in result and isinstance(result["content"], list):
            assistant_response = result["content"][0].get("text", "").strip()
            parsed_data = json.loads(assistant_response)  # Convert response to JSON
            Logger.info(f"Extracted City/State/Zip: {parsed_data}")
            return parsed_data
        else:
            Logger.warning("Bedrock response missing expected content field.")
            return {"City": None, "State": None, "Zip Code": None}

    except Exception as e:
        Logger.error(f"Error extracting City, State, Zip Code: {str(e)}")
        return {"City": None, "State": None, "Zip Code": None}
