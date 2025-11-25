"""
Model registry for multi-model evaluation.

All models are accessed via OpenRouter using their OpenRouter model identifiers.
"""

from typing import Dict

# Models available for evaluation via OpenRouter
EVAL_MODELS: Dict[str, str] = {
    # Claude models (Anthropic)
    "claude-sonnet": "anthropic/claude-sonnet-4-20250514",
    "claude-opus": "anthropic/claude-opus-4-20250514",
    # OpenAI models
    "gpt-4o": "openai/gpt-4o",
    "gpt-4.1": "openai/gpt-4.1",
    "gpt-4.1-codex": "openai/codex-mini",
    # Google models
    "gemini-pro": "google/gemini-2.5-pro-preview",
    # Qwen models (Alibaba)
    "qwen-plus": "qwen/qwen-plus",
    # Other models
    "kimi-k2": "moonshotai/kimi-k2",
}

# Judge model for evaluating answer correctness
JUDGE_MODEL = "anthropic/claude-opus-4-20250514"

# Cost per 1M tokens (approximate, for reference - OpenRouter provides actual costs)
# These are fallback estimates if OpenRouter doesn't return cost info
MODEL_COSTS_PER_1M_TOKENS: Dict[str, Dict[str, float]] = {
    "anthropic/claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "anthropic/claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    "openai/gpt-4o": {"input": 2.5, "output": 10.0},
    "openai/gpt-4.1": {"input": 2.0, "output": 8.0},
    "openai/codex-mini": {"input": 1.5, "output": 6.0},
    "google/gemini-2.5-pro-preview": {"input": 1.25, "output": 10.0},
    "qwen/qwen-plus": {"input": 0.5, "output": 2.0},
    "moonshotai/kimi-k2": {"input": 0.6, "output": 2.4},
}


def get_model_id(model_name: str) -> str:
    """Get the OpenRouter model ID for a given model name."""
    if model_name in EVAL_MODELS:
        return EVAL_MODELS[model_name]
    # If it's already a full model ID, return as-is
    if "/" in model_name:
        return model_name
    raise ValueError(f"Unknown model: {model_name}. Available models: {list(EVAL_MODELS.keys())}")


def get_all_model_names() -> list[str]:
    """Get all available model names."""
    return list(EVAL_MODELS.keys())


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a model based on token counts (fallback if OpenRouter doesn't provide cost)."""
    if model_id in MODEL_COSTS_PER_1M_TOKENS:
        costs = MODEL_COSTS_PER_1M_TOKENS[model_id]
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return input_cost + output_cost
    return 0.0

