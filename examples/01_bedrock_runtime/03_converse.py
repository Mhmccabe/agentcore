"""
Bedrock Runtime - Converse API
The Converse API provides a unified interface across all Bedrock models,
handling message history for multi-turn conversations automatically.
Prefer this over InvokeModel for new applications.
Requires: AWS credentials with bedrock:InvokeModel permission.

Architecture:
    conversation_history = []

    Turn 1                  Turn 2                  Turn 3
    ──────────────────      ──────────────────      ──────────────────
    [user msg]         -->  [user msg 1]       -->  [user msg 1]
         |                  [asst msg 1]            [asst msg 1]
         v                  [user msg 2]       -->  [user msg 2]
    Converse API                 |                  [asst msg 2]
         |                       v                  [user msg 3]  -->
         v                  Converse API                 |
    Claude Haiku                 |                       v
         |                       v                  Converse API
         v                  Claude Haiku                 |
    assistant msg 1              |                       v
                                 v                  Claude Haiku
                            assistant msg 2
    History grows with each turn; the full context is sent every call.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import boto3
from dotenv import load_dotenv
from utils.cost_tracker import print_cost, SessionTotal, _calculate

load_dotenv()

# Cross-region inference prefix allows Bedrock to route across AWS regions
# for better availability on newer models.
MODEL_ID = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"

client = boto3.client("bedrock-runtime", region_name="eu-west-1")

conversation_history = []
session = SessionTotal()


def chat(user_message: str) -> str:
    conversation_history.append({"role": "user", "content": [{"text": user_message}]})

    response = client.converse(
        modelId=MODEL_ID,
        messages=conversation_history,
        system=[{"text": "You are a helpful AWS expert."}],
        inferenceConfig={"maxTokens": 512, "temperature": 0.7},
    )

    assistant_message = response["output"]["message"]
    conversation_history.append(assistant_message)

    usage = response["usage"]
    call = _calculate(MODEL_ID, usage["inputTokens"], usage["outputTokens"])
    session.add(call)
    call.print()

    return assistant_message["content"][0]["text"]


print("Turn 1:", chat("What is Amazon Bedrock?"))
print()
print("Turn 2:", chat("What models does it support?"))
print()
print("Turn 3:", chat("Which one is best for coding tasks?"))

session.print()
