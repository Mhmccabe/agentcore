"""
Cost tracking wrapper for Strands agents.
Prints token usage and estimated cost after every agent call.

Prices are per 1M tokens — verify current rates at:
https://aws.amazon.com/bedrock/pricing/
"""
from dataclasses import dataclass, field
from strands import Agent

# (input_per_1m_usd, output_per_1m_usd)
# Verify these at https://aws.amazon.com/bedrock/pricing/
PRICES: dict[str, tuple[float, float]] = {
    "eu.anthropic.claude-haiku-4-5-20251001-v1:0": (0.80, 4.00),
    "eu.anthropic.claude-sonnet-4-6":              (3.00, 15.00),
    "eu.anthropic.claude-sonnet-4-5-20250929-v1:0": (3.00, 15.00),
    "eu.anthropic.claude-opus-4-5-20251101-v1:0":  (15.00, 75.00),
}


@dataclass
class CallCost:
    model_id: str
    input_tokens: int
    output_tokens: int
    input_cost_usd: float
    output_cost_usd: float

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def total_cost_usd(self) -> float:
        return self.input_cost_usd + self.output_cost_usd

    def print(self):
        known = self.model_id in PRICES
        cost_str = f"~${self.total_cost_usd:.6f}" if known else "unknown (add to PRICES dict)"
        print(
            f"\n{'─' * 50}\n"
            f"  Model:  {self.model_id}\n"
            f"  Tokens: {self.input_tokens} in + {self.output_tokens} out = {self.total_tokens} total\n"
            f"  Cost:   {cost_str}\n"
            f"{'─' * 50}"
        )


@dataclass
class SessionTotal:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost_usd: float = 0.0

    def add(self, call: CallCost):
        self.calls += 1
        self.input_tokens += call.input_tokens
        self.output_tokens += call.output_tokens
        self.total_cost_usd += call.total_cost_usd

    def print(self):
        print(
            f"\n{'═' * 50}\n"
            f"  Session total ({self.calls} calls)\n"
            f"  Tokens: {self.input_tokens} in + {self.output_tokens} out = {self.input_tokens + self.output_tokens} total\n"
            f"  Cost:   ~${self.total_cost_usd:.6f}\n"
            f"{'═' * 50}"
        )


def print_cost(model_id: str, input_tokens: int, output_tokens: int):
    """Print cost summary for a single boto3 call — use when not using TrackedAgent."""
    call = _calculate(model_id, input_tokens, output_tokens)
    call.print()


def _calculate(model_id: str, input_tokens: int, output_tokens: int) -> CallCost:
    rates = PRICES.get(model_id, (0.0, 0.0))
    return CallCost(
        model_id=model_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_usd=input_tokens / 1_000_000 * rates[0],
        output_cost_usd=output_tokens / 1_000_000 * rates[1],
    )


class TrackedAgent:
    """
    Wraps a Strands Agent to print token usage and cost after every call.
    Use exactly like a regular Agent: response = agent("your prompt")
    """

    def __init__(self, agent: Agent):
        self._agent = agent
        self._model_id = agent.model.config.get("model_id", "unknown")
        self.session = SessionTotal()

    def __call__(self, prompt: str):
        response = self._agent(prompt)
        usage = response.metrics.accumulated_usage
        call = _calculate(self._model_id, usage["inputTokens"], usage["outputTokens"])
        self.session.add(call)
        call.print()
        return response

    def print_session_total(self):
        self.session.print()
