"""
Bedrock Runtime - Streaming
Streams tokens as they are generated instead of waiting for the full response.
Useful for chat UIs and long responses.
Requires: AWS credentials with bedrock:InvokeModelWithResponseStream permission.

Architecture:
    Your Code
        |
        | JSON request body
        v
    Bedrock Runtime
    InvokeModelWithResponseStream API
        |
        | EventStream (Server-Sent Events)
        v
    for event in response["body"]:
        |
        +-- message_start   --> capture input_tokens
        +-- content_block_delta --> print token to stdout
        +-- message_delta   --> capture output_tokens
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
            "content": "Write a short poem about cloud computing.",
        }
    ],
}

response = client.invoke_model_with_response_stream(
    modelId=MODEL_ID,
    body=json.dumps(request_body),
    contentType="application/json",
    accept="application/json",
)

print("Streaming response:\n")
input_tokens = output_tokens = 0

for event in response["body"]:
    chunk = json.loads(event["chunk"]["bytes"])
    if chunk["type"] == "content_block_delta":
        print(chunk["delta"].get("text", ""), end="", flush=True)
    # Usage arrives in the final message_delta event
    elif chunk["type"] == "message_delta" and "usage" in chunk:
        output_tokens = chunk["usage"].get("output_tokens", 0)
    elif chunk["type"] == "message_start" and "message" in chunk:
        input_tokens = chunk["message"].get("usage", {}).get("input_tokens", 0)

print()
print_cost(MODEL_ID, input_tokens, output_tokens)
