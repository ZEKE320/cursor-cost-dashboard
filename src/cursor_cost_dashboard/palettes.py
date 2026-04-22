COST_BINS = [-float("inf"), 0.1, 0.5, 1.0, 2.0, 3.0, 5.0, float("inf")]
CATEGORY_ORDER = [
    "Cold (<$0.10)",
    "Cool ($0.10-$0.49)",
    "Warm ($0.50-$0.99)",
    "Hot ($1.00-$1.99)",
    "Very Hot ($2.00-$2.99)",
    "Burning ($3.00-$4.99)",
    "Blazing ($5.00+)",
]
CATEGORY_COLORS = {
    "Cold (<$0.10)": "#dbe9f6",
    "Cool ($0.10-$0.49)": "#9ecae1",
    "Warm ($0.50-$0.99)": "#3182bd",
    "Hot ($1.00-$1.99)": "#fdae6b",
    "Very Hot ($2.00-$2.99)": "#f16913",
    "Burning ($3.00-$4.99)": "#cb181d",
    "Blazing ($5.00+)": "#67000d",
}
MODEL_COLORS = {
    "gpt-5.4-high": "#0b3c78",
    "gpt-5.4-medium": "#4f88c6",
    "Premium (Codex 5.3)": "#8ab6d6",
    "claude-4.6-opus-high-thinking": "#d97706",
    "gemini-3.1-pro": "#2f855a",
    "gemini-3.1-pro-preview": "#86c99a",
    "composer-2": "#7c3aed",
    "composer-2-fast": "#c4b5fd",
    "auto": "#6b7280",
}

def infer_provider(model: str) -> str:
    if model.startswith("gpt-") or "Codex" in model:
        return "OpenAI"
    if model.startswith("claude-"):
        return "Anthropic"
    if model.startswith("gemini-"):
        return "Google"
    return "Unspecified"
