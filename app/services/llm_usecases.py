from __future__ import annotations

from ..settings import get_settings


async def get_llm_status() -> dict[str, object]:
    s = get_settings()

    llama_cpp_ok = False
    if s.llm_model_path:
        try:
            from llama_cpp import Llama
            llama_cpp_ok = bool(Llama)
        except Exception:
            llama_cpp_ok = False

    return {
        "configured": llama_cpp_ok,
        "llama_cpp": llama_cpp_ok,
        "model_path": s.llm_model_path,
    }
