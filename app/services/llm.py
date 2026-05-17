from __future__ import annotations

from functools import lru_cache

import anyio

from ..settings import get_settings


@lru_cache(maxsize=1)
def _get_llm():
    s = get_settings()
    if not s.llm_model_path:
        return None
    try:
        from llama_cpp import Llama
    except Exception:
        return None
    return Llama(model_path=s.llm_model_path, n_ctx=512, n_threads=4, verbose=False)


async def answer_chat(messages: list[dict[str, str]]) -> str:
    llm = _get_llm()
    if llm is None:
        return "LLM not configured. Set MODEL_PATH in .env to point to a .gguf model file."
    prompt = "\n".join(
        [f"{m.get('role', 'user').title()}: {m.get('content', '')}" for m in messages[-12:]]
    )
    result = await anyio.to_thread.run_sync(
        lambda: llm(
            f"{prompt}\nAssistant:",
            max_tokens=512,
            stop=["User:", "\nUser"],
            stream=False,
        )
    )
    text = str(result["choices"][0]["text"])
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()
