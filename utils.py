import os
import re
import urllib.request
import urllib.parse
import ollama

SAFE_SANDBOX_DIR = os.path.abspath("./autonomous_company_projects")
DESIGN_MEMORY_DIR = os.path.abspath("./agent_design_lessons")
os.makedirs(SAFE_SANDBOX_DIR, exist_ok=True)
os.makedirs(DESIGN_MEMORY_DIR, exist_ok=True)

def search_duckduckgo(query: str) -> str:
    print(f"🌐 [CEO Researching Web Markets]: '{query}'")
    try:
        url = f"https://duckduckgo.com{urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode('utf-8')
        snippets = re.findall(r'<a class="result__snippet".*?>(.*?)</a>', html, re.DOTALL)
        return "\n".join([re.sub(r'<.*?>', '', s).strip() for s in snippets[:5]])
    except Exception:
        return "No major competitors found in this vector."

def call_ollama(model_name: str, system_prompt: str, user_prompt: str) -> str:
    memory_context = ""
    if os.path.exists(DESIGN_MEMORY_DIR):
        for f in os.listdir(DESIGN_MEMORY_DIR):
            if f.endswith(".txt"):
                with open(os.path.join(DESIGN_MEMORY_DIR, f), "r", encoding="utf-8") as file:
                    memory_context += file.read() + "\n"
    
    full_system = f"{system_prompt}\n\n### PAST LESSONS:\n{memory_context}"
    response = ollama.chat(
        model=model_name,
        messages=[{"role": "system", "content": full_system}, {"role": "user", "content": user_prompt}],
        options={"temperature": 0.4, "num_ctx": 16384}
    )
    return re.sub(r"<thought>.*?</thought>", "", response['message']['content'], flags=re.DOTALL).strip()
