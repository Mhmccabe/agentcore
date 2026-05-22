"""
Knowledge Bases - Retrieve and Generate with Strands
Combines a Bedrock Knowledge Base (managed RAG) with a Strands agent.
The retrieve tool lets the agent query the KB; it then synthesises an answer.

Prerequisites:
  1. Create a Knowledge Base in the AWS console (Bedrock > Knowledge Bases)
  2. Attach an S3 data source with documents and sync it
  3. Set KNOWLEDGE_BASE_ID below

Requires: bedrock:InvokeModel, bedrock:Retrieve permissions.

Architecture:
    Your documents
         |
         | (one-time sync)
         v
    S3 Bucket  -->  Bedrock Knowledge Base
                         |
                    Titan Embeddings
                         |
                    Vector Store (managed)

    At query time:
    agent("question")
         |
         v
    Strands Agent + Claude Haiku
         |
         v
    @tool search_knowledge_base(query)
         |
         v
    bedrock-agent-runtime  -->  Knowledge Base
                                     |
                                 vector search
                                     |
                                 top-k chunks + scores
         |
         v
    Claude Haiku synthesises answer grounded in chunks
         |
         v
    Answer with source citations
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import boto3
from strands import Agent, tool
from strands.models import BedrockModel
from dotenv import load_dotenv
from utils.cost_tracker import TrackedAgent

load_dotenv()

KNOWLEDGE_BASE_ID = "YOUR_KNOWLEDGE_BASE_ID"  # replace with your KB ID
REGION = "eu-west-1"

kb_client = boto3.client("bedrock-agent-runtime", region_name=REGION)


@tool
def search_knowledge_base(query: str, num_results: int = 5) -> list[dict]:
    """
    Search the Bedrock Knowledge Base for documents relevant to the query.

    Args:
        query: The search query
        num_results: Number of results to retrieve (default 5)

    Returns:
        A list of dicts with 'text', 'score', and 'source' keys.
    """
    response = kb_client.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": num_results}},
    )

    results = []
    for r in response["retrievalResults"]:
        results.append({
            "text": r["content"]["text"],
            "score": round(r.get("score", 0), 4),
            "source": r.get("location", {}).get("s3Location", {}).get("uri", "unknown"),
        })
    return results


model = BedrockModel(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name=REGION,
)

agent = TrackedAgent(Agent(
    model=model,
    tools=[search_knowledge_base],
    system_prompt=(
        "You are a helpful assistant with access to a knowledge base. "
        "Always search the knowledge base before answering questions. "
        "Cite the sources you used in your response."
    ),
))

response = agent("What are the main topics covered in the knowledge base?")
print(response)
