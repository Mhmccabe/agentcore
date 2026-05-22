# AWS Bedrock & AgentCore Learning

Experiments and examples for AWS Bedrock and AgentCore using the Strands Agents SDK.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # only needed for the browser example
cp .env.example .env          # fill in your AWS credentials
aws configure                 # set region to eu-west-1
```

## Examples

| Directory | What it covers |
|---|---|
| `01_bedrock_runtime/` | Raw boto3 API — InvokeModel, streaming, Converse, tool use |
| `02_strands_basics/` | Strands fundamentals — agents, custom tools, built-ins, streaming |
| `03_knowledge_bases/` | RAG with Bedrock Knowledge Bases via a Strands tool |
| `04_agentcore/memory/` | AgentCore Memory Store — persist and recall facts across sessions |
| `04_agentcore/code_interpreter/` | AgentCore sandboxed Python execution |
| `04_agentcore/browser/` | Headless browser for real-time web access |
| `05_multi_agent/` | Orchestrator pattern — sub-agents composed with `as_tool()` |
| `06_llm_wiki/` | Karpathy-style LLM wiki — entity extraction and knowledge curation |
| `07_mcp/` | MCP server definition and client agent that discovers tools at runtime |
| `08_drawio/` | ArchiMate 3.2 architecture diagram from a problem statement via draw.io MCP |

## Estimated Cost per Example

All costs are in USD. Estimates are based on typical runs and will vary with response length.
Models used: `eu.anthropic.claude-haiku-4-5` ($0.80/$4.00 per 1M tokens in/out) and
`eu.anthropic.claude-sonnet-4-6` ($3.00/$15.00 per 1M tokens in/out).

| Example | Model | Est. Cost | Notes |
|---|---|---|---|
| `01_bedrock_runtime/01_invoke_model.py` | Haiku 4.5 | ~$0.0004 | Single short prompt |
| `01_bedrock_runtime/02_streaming.py` | Haiku 4.5 | ~$0.0003 | Same as above, streamed |
| `01_bedrock_runtime/03_converse.py` | Haiku 4.5 | ~$0.002 | 3 conversational turns |
| `01_bedrock_runtime/04_tool_use.py` | Haiku 4.5 | ~$0.001 | 2 API calls (tool loop) |
| `02_strands_basics/01_hello_agent.py` | Haiku 4.5 | ~$0.001 | Single agent call |
| `02_strands_basics/02_custom_tools.py` | Haiku 4.5 | ~$0.002 | Agent with 2 tool calls |
| `02_strands_basics/03_builtin_tools.py` | Haiku 4.5 | ~$0.003 | 2 calls, python_repl + shell |
| `02_strands_basics/04_streaming_agent.py` | Haiku 4.5 | ~$0.001 | Single streamed call |
| `03_knowledge_bases/retrieve_and_generate.py` | Haiku 4.5 | ~$0.002 | Requires KB setup |
| `04_agentcore/memory/memory_store.py` | Haiku 4.5 | ~$0.003 | Requires AgentCore setup |
| `04_agentcore/code_interpreter/code_interpreter.py` | Haiku 4.5 | ~$0.004 | Requires AgentCore setup |
| `04_agentcore/browser/browser_agent.py` | Sonnet 4.6 | ~$0.50-$1.00 | High — full page DOM loaded into context |
| `05_multi_agent/orchestrator.py` | Sonnet 4.6 + Haiku 4.5 | ~$0.10-$0.30 | Multiple agents, several round trips |
| `06_llm_wiki/ingest.py` (per file) | Sonnet 4.6 | ~$0.15-$0.25 | Scales with number of entities found |
| `06_llm_wiki/query.py` (per query) | Haiku 4.5 | ~$0.005-$0.01 | Scales with wiki size |
| `07_mcp/client.py` | Haiku 4.5 | ~$0.04 | 6 agent calls; Tools + Resources + Prompts via MCP server |
| `08_drawio/archimate_diagram.py` | Sonnet 4.6 | ~$0.05–$0.15 | Generates ArchiMate 3.2 XML, opens in draw.io |

> **Tip:** The browser and multi-agent examples are the most expensive. Run them sparingly
> while learning. All other examples cost well under $0.01 per run.

## Start here

```bash
# Immediately runnable (just needs AWS creds + Bedrock model access)
python examples/01_bedrock_runtime/01_invoke_model.py
python examples/02_strands_basics/01_hello_agent.py

# LLM Wiki — build and query a knowledge base from text
cd examples/06_llm_wiki
python ingest.py sample_inputs/01_aws_ai.md
python query.py "What is the relationship between Anthropic and AWS?"

# ArchiMate 3.2 diagram — opens draw.io (requires npx / Node.js)
python examples/08_drawio/archimate_diagram.py
python examples/08_drawio/archimate_diagram.py "Describe your own system here"

# Requires AgentCore enabled in your account
python examples/04_agentcore/memory/memory_store.py
python examples/04_agentcore/code_interpreter/code_interpreter.py
```

## Model access

Enable model access in the [AWS Bedrock console](https://eu-west-1.console.aws.amazon.com/bedrock/home?region=eu-west-1#/modelaccess)
for the models used in these examples:

- Anthropic — Claude Haiku 4.5
- Anthropic — Claude Sonnet 4.6
