import os
import re
import hashlib
import urllib.request
import urllib.parse
import json
import time

import ollama

SAFE_SANDBOX_DIR = os.path.abspath("./autonomous_company_projects")
DESIGN_MEMORY_DIR = os.path.abspath("./agent_design_lessons")
os.makedirs(SAFE_SANDBOX_DIR, exist_ok=True)
os.makedirs(DESIGN_MEMORY_DIR, exist_ok=True)

# Global caches: avoid reading lesson files repeatedly and avoid repeating same LLM call text
_LESSON_CACHE = {}
_OLLAMA_CACHE = {}
_OFFLINE_MODE = os.getenv("OFFLINE_MODE", "0").lower() in {"1", "true", "yes", "on"}
_LOW_POWER_MODE = os.getenv("LOW_POWER_MODE", "1").lower() not in {"0", "false", "no"}


def _read_design_lessons(max_chars: int = 2000):
    """Read and cache lesson files; return a concise memory summary (truncated)."""
    global _LESSON_CACHE
    if _LESSON_CACHE:
        # return an aggregated summary to keep prompts short
        combined = "\n".join(list(_LESSON_CACHE.values()))
        return combined[:max_chars]
    memory_context = ""
    try:
        if os.path.exists(DESIGN_MEMORY_DIR):
            for f in sorted(os.listdir(DESIGN_MEMORY_DIR)):
                if f.endswith(".txt"):
                    path = os.path.join(DESIGN_MEMORY_DIR, f)
                    try:
                        with open(path, "r", encoding="utf-8") as file:
                            _LESSON_CACHE[f] = file.read()
                    except Exception:
                        pass
            memory_context = "\n".join(_LESSON_CACHE.values())
    except Exception:
        memory_context = ""
    return memory_context[:max_chars]


def search_duckduckgo(query: str) -> str:
    print(f"🌐 [CEO Researching Web Markets]: '{query}'")
    query = (query or "").strip()
    if not query:
        return "No market research available."

    try:
        encoded = urllib.parse.quote(query)
        url = f"https://duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode("utf-8", errors="ignore")

        snippets = re.findall(r'<a rel="nofollow" class="result-link".*?href="(.*?)".*?>(.*?)</a>.*?<a class="result-snippet".*?>(.*?)</a>', html, re.DOTALL)
        if not snippets:
            snippets = re.findall(r'<a rel="nofollow" class="result-link".*?>(.*?)</a>.*?<a class="result-snippet".*?>(.*?)</a>', html, re.DOTALL)

        text = []
        for item in snippets[:5]:
            if isinstance(item, tuple):
                snippet = " ".join([part for part in item if isinstance(part, str)])
            else:
                snippet = str(item)
            snippet = re.sub(r"<.*?>", " ", snippet)
            snippet = re.sub(r"\s+", " ", snippet).strip()
            if snippet:
                text.append(snippet)

        if not text:
            return "No major competitors found in this vector."
        return "\n".join(text)
    except Exception:
        return "No major competitors found in this vector."


def _ollama_stub(model_name: str, system_prompt: str, user_prompt: str) -> str:
    if isinstance(user_prompt, list):
        user_prompt = " ".join([str(item) for item in user_prompt])
    else:
        user_prompt = str(user_prompt)

    summary = f"[LOCAL-STUB] Model={model_name}. System={str(system_prompt)[:120]}... User={user_prompt[:160]}"
    return summary.strip()


def _make_cache_key(model_name: str, system_prompt: str, user_prompt: str, options: dict | None = None) -> str:
    raw = f"{model_name}\n{system_prompt}\n{user_prompt}\n{json.dumps(options, sort_keys=True) if options else ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def call_ollama(model_name: str, system_prompt: str, user_prompt: str, options: dict = None) -> str:
    """Call ollama with caching and offline fallback. Options are passed through to the model run (e.g., temperature).

    Keeps prompt context short by summarizing lessons, and caches responses keyed by model+system+user+options.
    """
    # Ultra-safe offline mode: no model calls
    if _OFFLINE_MODE:
        return _ollama_stub(model_name, system_prompt, user_prompt)

    if isinstance(user_prompt, list):
        user_prompt = " ".join([str(item) for item in user_prompt])
    else:
        user_prompt = str(user_prompt)

    key = _make_cache_key(model_name, system_prompt, user_prompt, options)
    if key in _OLLAMA_CACHE:
        return _OLLAMA_CACHE[key]

    memory_context = _read_design_lessons()
    full_system = f"{system_prompt}\n\n### PAST LESSONS:\n{memory_context}"

    # Fast fail if Ollama is not available on this machine
    try:
        call_options = options or {"temperature": 0.4, "num_ctx": 16384}
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": str(full_system)},
                {"role": "user", "content": user_prompt},
            ],
            options=call_options,
        )
        result = re.sub(r"<thought>.*?</thought>", "", response['message']['content'], flags=re.DOTALL).strip()
    except Exception:
        print(f"Warning: Ollama call failed for model {model_name}; using a local stub response.")
        result = _ollama_stub(model_name, system_prompt, user_prompt)

    _OLLAMA_CACHE[key] = result
    return result


def get_memory_snapshot(limit: int = 5):
    lessons = []
    for name in sorted(os.listdir(DESIGN_MEMORY_DIR)):
        if name.endswith(".txt"):
            path = os.path.join(DESIGN_MEMORY_DIR, name)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lessons.append({"name": name, "content": f.read()})
            except Exception:
                pass
    return lessons[:limit]
