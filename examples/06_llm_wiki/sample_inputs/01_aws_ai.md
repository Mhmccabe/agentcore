# AWS AI Services — Overview

## Amazon Bedrock

Amazon Web Services launched **Amazon Bedrock** in 2023, a fully managed service that gives
developers API access to foundation models from multiple AI companies without managing
infrastructure. Bedrock supports models from Anthropic, Meta, Cohere, Mistral, and Amazon's
own **Titan** model family.

## Anthropic and Claude

**Anthropic** is an AI safety company founded in 2021 by **Dario Amodei** and **Daniela Amodei**,
along with other former OpenAI researchers. Their flagship model family is **Claude**, which is
known for its strong reasoning, long context window, and focus on safety. Claude 3.5 Sonnet and
Claude 3.5 Haiku are the most widely used Anthropic models on Bedrock in 2024.

## AgentCore

AWS launched **AgentCore** in 2025, a platform for deploying and managing AI agents at scale.
AgentCore provides managed infrastructure for:

- Agent memory
- Code execution
- Web browsing
- API gateway capabilities

AgentCore is designed to work with the **Strands Agents SDK**.

## Strands Agents SDK

The **Strands Agents SDK** is an open-source Python framework released by AWS for building AI
agents. Key features include:

- Decorator-based tool definition (`@tool`)
- Multi-agent orchestration
- Native integration with Amazon Bedrock as a model provider
- Support for specialist sub-agents via `agent.as_tool()`
