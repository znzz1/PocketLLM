from typing import List, Optional
import json, hashlib


# ===============================
# Token Estimator
# ===============================

def estimate_tokens(text: Optional[str]) -> int:
    """Better multilingual token estimation."""
    if not text:
        return 0
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    english = len(text.split())
    return chinese * 2 + english


MAX_HISTORY_TOKENS = 1024

def trim_conversation(messages: List, max_tokens: int = MAX_HISTORY_TOKENS):
    total = 0
    trimmed = []
    for msg in reversed(messages):
        tokens = estimate_tokens(msg.content)
        if total + tokens > max_tokens:
            break
        trimmed.insert(0, msg)
        total += tokens
    return trimmed


# ===============================
# System prompt loader
# ===============================

def load_system_prompt(path="prompt.txt") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            # Remove the template placeholders if they exist
            content = content.replace("Instruction: {prompt}", "").strip()
            content = content.replace("Response:", "").strip()
            if not content:
                return "You are a helpful AI assistant."
            return content
    except:
        return "You are a helpful AI assistant."


# ===============================
# Chat Formatters
# ===============================

def fmt_chat(role: str, content: str) -> str:
    """Unified <|im_start|> format (works for Qwen/DeepSeek/LLaMA)."""
    return f"<|im_start|>{role}\n{content}<|im_end|>\n"


# ===============================
# Prompt Builder
# ===============================

def build_prompt(messages: List, system_prompt: str, new_user_prompt: str) -> str:
    """Build a properly formatted prompt for the model.
    
    Args:
        messages: List of previous conversation messages
        system_prompt: System instructions for the model
        new_user_prompt: The new user message to respond to
        
    Returns:
        Formatted prompt string ready for model inference
    """
    # Start with system message
    prompt = fmt_chat("system", system_prompt)

    # Add conversation history
    for msg in messages:
        role = msg.role
        content = (msg.content or "").strip()
        if not content:
            continue
        prompt += fmt_chat(role, content)

    # Add new user message
    prompt += fmt_chat("user", new_user_prompt.strip())

    # Start assistant response
    prompt += "<|im_start|>assistant\n"

    return prompt


# ===============================
# Cache Key
# ===============================

def build_cache_key(user_id: str, session_id: str, prompt: str, prev_response: str | None = None) -> str:
    """Build a cache key for storing/retrieving cached responses."""
    import json
    cache_key = json.dumps({
        "user_id": user_id,
        "session_id": session_id,
        "prompt": prompt.strip(),
        "prev_response": prev_response.strip() if prev_response else None
    }, sort_keys=True)
    return cache_key