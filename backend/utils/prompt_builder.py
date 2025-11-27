from typing import List, Optional
import json, hashlib

def load_system_prompt(path="prompt.txt") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "You are a helpful assistant."

def fmt_chat(role: str, content: str) -> str:
    return (
        f"<|start_header_id|>{role}<|end_header_id|>\n"
        f"{content.strip()}\n"
    )

def build_prompt(messages: List, system_prompt: str, new_user_prompt: str) -> str:
    parts = []
    parts.append(fmt_chat("system", system_prompt))

    for msg in messages:
        role = msg.role
        content = (msg.content or "").strip()
        if content:
            parts.append(fmt_chat(role, content))

    parts.append(fmt_chat("user", new_user_prompt.strip()))
    parts.append("<|start_header_id|>assistant<|end_header_id|>\n")

    return "".join(parts)

def build_cache_key(user_id: str, session_id: str, prompt: str, prev_response: str | None = None) -> str:
    cache_key = json.dumps({
        "user_id": user_id,
        "session_id": session_id,
        "prompt": prompt.strip(),
        "prev_response": prev_response.strip() if prev_response else None
    }, sort_keys=True)
    return cache_key
