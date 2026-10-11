import os
import json
import re
import subprocess
from datetime import datetime
from utils import call_ollama, search_duckduckgo, SAFE_SANDBOX_DIR, DESIGN_MEMORY_DIR

BRAIN_MODEL = "deepseek-r1:32b"
DESIGN_MODEL = "llama3:latest"
ENGINE_MODEL = "qwen2.5-coder:32b"
FLASH_MODEL = "gemma3:270m"
ARCHIVE_MODEL = "smollm2:135m"

def build_and_deploy_fullstack_company():
    print(f"\n⚡ Startup Cycle Initiated: {datetime.now().strftime('%H:%M:%S')}")
    
    query = call_ollama(BRAIN_MODEL, "Output ONLY a 3-word web search query for a software niche.", "Find a gap.")
    query = re.sub(r"[```\n]", "", query).strip()
    market_data = search_duckduckgo(query)

    ceo_prompt = f"Competitors:\n{market_data}\nDesign a premium SaaS web utility. Output raw JSON object matching: " + '{"name": "Brand", "prd": "features"}'
    try:
        idea_json = json.loads(re.sub(r"```[a-z]*\n|```", "", call_ollama(BRAIN_MODEL, ceo_prompt, "Create blueprint.")))
        project_name = idea_json["name"].replace(" ", "_")
        prd = idea_json["prd"]
    except Exception:
        project_name = f"Aero_Matrix_{datetime.now().strftime('%M%S')}"
        prd = "Premium workspace dashboard utilizing local browser memory."

    print(f"✨ Brand Concept Secured: 【 {project_name} 】")
    project_path = os.path.join(SAFE_SANDBOX_DIR, project_name)
    os.makedirs(project_path, exist_ok=True)

    branding = call_ollama(DESIGN_MODEL, "Create a luxury color palette and viral headline hook.", prd)
    
    for file_name in ["index.html", "app.js", "styles.css"]:
        print(f"  🛠️  Writing asset: {file_name}...")
        code = call_ollama(ENGINE_MODEL, "Write full production code using Tailwind CSS and Supabase JS links. No placeholders. Output ONLY raw code.", f"Build {file_name} for {prd}")
        with open(os.path.join(project_path, file_name), "w", encoding="utf-8") as f:
            f.write(re.sub(r"```[a-z]*\n|```", "", code).strip())

    print("📦 [DevOps Automation] Initializing local Git repository...")
    subprocess.run(["git", "init"], cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "add", "."], cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "commit", "-m", "'Initial package'"], cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print("☁️ [Vercel CLI] Compiling to Vercel production servers...")
    vercel_logs = subprocess.run(["vercel", "--yes", "--prod"], cwd=project_path, stdout=subprocess.PIPE, text=True, shell=True).stdout
    print(vercel_logs)

    lesson = call_ollama(BRAIN_MODEL, "Identify what was plain or unoriginal. Start answer exactly with: 'DESIGN LESSON learned:'", prd)
    lesson_id = len(os.listdir(DESIGN_MEMORY_DIR)) + 1
    with open(os.path.join(DESIGN_MEMORY_DIR, f"lesson_{lesson_id}.txt"), "w", encoding="utf-8") as lf:
        lf.write(lesson)
