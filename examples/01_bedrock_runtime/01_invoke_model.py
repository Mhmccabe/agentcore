"""
Bedrock Runtime - InvokeModel
Sends a single prompt to a foundation model and gets a response.
Requires: AWS credentials with bedrock:InvokeModel permission.

Architecture:
    Your Code
        |
        | JSON request body
        v
    Bedrock Runtime  (eu-west-1)
    InvokeModel API
        |
        | routes to
        v
    Claude Haiku 4.5
        |
        | JSON response body
        v
    Your Code  <-- parse result["content"][0]["text"]
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import boto3
from dotenv import load_dotenv
from utils.cost_tracker import print_cost

load_dotenv()

MODEL_ID = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"

client = boto3.client("bedrock-runtime", region_name="eu-west-1")

request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 512,
    "messages": [
        {
            "role": "user",
            "content": "Explain AWS Bedrock in two sentences.",
        }
    ],
}

response = client.invoke_model(
    modelId=MODEL_ID,
    body=json.dumps(request_body),
    contentType="application/json",
    accept="application/json",
)

result = json.loads(response["body"].read())
print(result["content"][0]["text"])

usage = result["usage"]
print_cost(MODEL_ID, usage["input_tokens"], usage["output_tokens"])
