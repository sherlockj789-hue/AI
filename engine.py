import os
import json
import re
import subprocess
import hashlib
import argparse
from datetime import datetime
from utils import call_ollama, search_duckduckgo, SAFE_SANDBOX_DIR, DESIGN_MEMORY_DIR

# Models (names kept for reference; actual resource use is controlled by LOW_POWER_MODE)
BRAIN_MODEL = "deepseek-r1:32b"
DESIGN_MODEL = "llama3:latest"
ENGINE_MODEL = "qwen2.5-coder:32b"

ULTIMATE_KIT = {
    "SUPABASE_REALTIME_AUTH": """
        const supabaseUrl = 'https://supabase.co';
        const supabaseKey = 'your-public-anon-key';
        const _supabase = supabase.createClient(supabaseUrl, supabaseKey);
        async function signupUser(e,p){const {data,error}=await _supabase.auth.signUp({email:e,password:p});if(error)throw error;return data.user;}
        async function signinUser(e,p){const {data,error}=await _supabase.auth.signInWithPassword({email:e,password:p});if(error)throw error;return data.session;}
        function subscribeToLiveTable(t,cb){return _supabase.channel('live').on('postgres_changes',{event:'*',schema:'public',table:t},p=>{cb(p.new);}).subscribe();}
    """,
    "LUXURY_GLASS_UI": """
        <link href="https://jsdelivr.net" rel="stylesheet">
        <script src="https://jsdelivr.net"></script>
        <script src="https://cloudflare.com"></script>
        <style>
          body { background: linear-gradient(145deg, #02040a 0%, #080f1e 100%); color: #f3f4f6; font-family: system-ui, sans-serif; min-height: 100vh; overflow-x: hidden; }
          .hyper-glass { background: rgba(13, 20, 35, 0.4); backdrop-filter: blur(24px); border: 1px solid rgba(255,255,255,0.05); border-radius: 1.5rem; }
          .premium-input { background: #010409; border: 1px solid #21262d; color: #f0f6fc; border-radius: 0.85rem; padding: 0.85rem 1.25rem; }
          .hyper-btn { background: linear-gradient(135deg, #06b6d4 0%, #6366f1 100%); border-radius: 0.85rem; padding: 0.85rem 2rem; font-weight: 700; transition: all 0.2s; cursor: pointer; }
          .hyper-btn:hover { transform: translateY(-3px); filter: brightness(1.15); }
        </style>
    """,
    "DYNAMIC_CANVAS_3D": """
        class ChartCanvasController {
            constructor(id) { this.ctx = document.getElementById(id).getContext('2d'); this.chart = null; }
            updateChart(l,v) { if(this.chart)this.chart.destroy(); this.chart = new Chart(this.ctx,{type:'line',data:{labels:l,datasets:[{label:'Data',data:v,borderColor:'#06b6d4',fill:true}]}}); }
        }
        function initProcedural3DBackground(id) {
            const el = document.getElementById(id); if(!el)return;
            const scene = new THREE.Scene(); const camera = new THREE.PerspectiveCamera(75, el.clientWidth/el.clientHeight, 0.1, 1000);
            const ren = new THREE.WebGLRenderer({alpha:true}); ren.setSize(el.clientWidth, el.clientHeight); el.appendChild(ren.domElement);
            const geo = new THREE.TorusKnotGeometry(10, 3, 100, 16); const mat = new THREE.MeshBasicMaterial({color:0x06b6d4,wireframe:true,opacity:0.1,transparent:true});
            const mesh = new THREE.Mesh(geo,mat); scene.add(mesh); camera.position.z = 30;
            function anim(){ requestAnimationFrame(anim); mesh.rotation.x+=0.005; mesh.rotation.y+=0.005; ren.render(scene,camera); } anim();
        }
    """,
    "SVG_CORE_ASSET_VAULT": """
        <g id="analytics"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" fill="currentColor"/></g>
    """
}

PERMANENT_COMPANY_NAME = "Nova_Core_Platform"

# Defaults: low-power and offline-safe to protect your machine and electricity bill
LOW_POWER_MODE = os.getenv("LOW_POWER_MODE", "1").lower() not in ("0", "false", "no")
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "1").lower() in ("1", "true", "yes", "on")

_PROMPT_CACHE_FILE = os.path.join(SAFE_SANDBOX_DIR, "prompt_cache.json")
_STATE_FILE = os.path.join(SAFE_SANDBOX_DIR, "agent_state.json")

try:
    with open(_PROMPT_CACHE_FILE, "r", encoding="utf-8") as _cf:
        _PROMPT_CACHE = json.load(_cf)
except Exception:
    _PROMPT_CACHE = {}


def _cache_get(key: str):
    return _PROMPT_CACHE.get(key)


def _cache_set(key: str, value: str):
    _PROMPT_CACHE[key] = value
    try:
        with open(_PROMPT_CACHE_FILE, "w", encoding="utf-8") as _cf:
            json.dump(_PROMPT_CACHE, _cf)
    except Exception:
        pass


def _hash_prompt(model: str, system: str, user: str) -> str:
    h = hashlib.sha256()
    h.update(model.encode("utf-8"))
    h.update(system.encode("utf-8"))
    h.update(user.encode("utf-8"))
    return h.hexdigest()


def load_agent_state():
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"runs": 0, "last_updated": None, "projects": []}


def save_agent_state(state):
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def sanitize_and_heal_code(raw_code: str) -> str:
    clean = re.sub(r"```[a-zA-Z]*\n", "", raw_code)
    clean = re.sub(r"\n```", "", clean).strip()
    if "<body>" in clean and "</body>" not in clean:
        clean += "\n</body></html>"
    return clean


def generate_additional_project_files(project_path: str, prd: str, branding: str):
    files = {
        "README.md": f"# {PERMANENT_COMPANY_NAME}\n\n## Product vision\n{prd[:1200]}\n\n## Brand\n{branding[:800]}\n\n## Deliverables\n- Landing page\n- Product dashboard\n- User auth\n- Live analytics\n- Launch checklist\n",
        "FEATURES.md": "# Product Features\n\n- Premium glassmorphism landing page\n- Realtime app data flow\n- Smart authentication and dashboard UX\n- Analytics and reporting layer\n- Marketing launch pack\n",
        "LAUNCH_CHECKLIST.md": "# Launch checklist\n\n- Validate auth flow\n- Test realtime updates\n- Confirm analytics charts\n- Verify responsive mobile UX\n- Publish marketing copy\n- Measure conversion and retention\n",
        "TASKS.md": "# Weekly execution plan\n\n1. Validate product direction\n2. Complete landing page and hero flow\n3. Add auth and live data pipeline\n4. Launch analytics and CTA section\n5. Ship launch campaign\n",
    }
    for name, content in files.items():
        try:
            with open(os.path.join(project_path, name), "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass


def build_project_plan(prd: str, current_code_context: str):
    base_prompt = (
        "You are a product strategist. Turn the product brief into a sharp execution plan.\n"
        "Return a concise list of 5 winning features, each with a short rationale and a business impact.\n"
        "Format as bullets."
    )
    plan = call_ollama(BRAIN_MODEL, base_prompt, f"Brief:\n{prd}\n\nCode context:\n{current_code_context}")
    return plan


def run_continuous_company_growth():
    project_path = os.path.join(SAFE_SANDBOX_DIR, PERMANENT_COMPANY_NAME)
    os.makedirs(project_path, exist_ok=True)

    state = load_agent_state()
    state["runs"] = int(state.get("runs", 0)) + 1
    state["last_updated"] = datetime.utcnow().isoformat()
    state.setdefault("projects", [])
    if PERMANENT_COMPANY_NAME not in state["projects"]:
        state["projects"].append(PERMANENT_COMPANY_NAME)

    print(f"\n⚡ Executing Ultimate Scale & Feature Architecture Cycle for 【 {PERMANENT_COMPANY_NAME} 】")
    prd_path = os.path.join(project_path, "PRODUCT_REQUIREMENTS.md")
    existing_prd = ""
    if os.path.exists(prd_path):
        try:
            with open(prd_path, "r", encoding="utf-8") as f:
                existing_prd = f.read()
        except Exception:
            existing_prd = ""

    current_code_context = ""
    for target_file in ["index.html", "app.js", "styles.css"]:
        f_path = os.path.join(project_path, target_file)
        if os.path.exists(f_path):
            try:
                with open(f_path, "r", encoding="utf-8") as f:
                    current_code_context += f"\n=== LIVE PRODUCTION FILE: {target_file} ===\n" + f.read() + "\n"
            except Exception:
                pass

    if not existing_prd:
        query = call_ollama(BRAIN_MODEL, "Output ONLY a 3-word web search query for a software gap.", "Find gap.")
        query = re.sub(r"[```\n]", "", query).strip()
        market_data = search_duckduckgo(query)
        prd = call_ollama(BRAIN_MODEL, f"Competitors:\n{market_data}\nDesign a premium closed-source database app.", "Create blueprint.")
    else:
        prd = call_ollama(BRAIN_MODEL, f"Active Blueprint:\n{existing_prd}\n\nLive Code:\n{current_code_context}\n\nDesign an advanced extension layer user panel section.", "Upgrade blueprint.")

    plan = build_project_plan(prd, current_code_context)
    try:
        with open(prd_path, "w", encoding="utf-8") as f:
            f.write(prd)
    except Exception:
        print("Warning: Could not write PRODUCT_REQUIREMENTS.md")

    try:
        plan_path = os.path.join(project_path, "EXECUTION_PLAN.md")
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(plan)
    except Exception:
        pass

    branding = call_ollama(DESIGN_MODEL, "Create premium Tailwind dark hex colors and visual copywriting headline hooks.", prd)

    for file_name in ["index.html", "app.js", "styles.css"]:
        print(f"  🛠️  Weaving Ultimate Kit modules into: {file_name}...")
        system_instructions = (
            f"You are a master engineer. Rewrite the complete file '{file_name}'. No placeholders.\n"
            f"INJECT FROM ULTIMATE KIT BLUEPRINTS:\n"
            f"- HTML/CSS UI styles: {ULTIMATE_KIT['LUXURY_GLASS_UI']}\n"
            f"- Supabase Realtime & Auth: {ULTIMATE_KIT['SUPABASE_REALTIME_AUTH']}\n"
            f"- Chartjs and ThreeJS WebGL 3D scripts: {ULTIMATE_KIT['DYNAMIC_CANVAS_3D']}\n"
            f"- Inline Vector Icon Vault blocks: {ULTIMATE_KIT['SVG_CORE_ASSET_VAULT']}\n\n"
            f"Integrate changes seamlessly with existing code framework:\n{current_code_context}\n"
            f"Output ONLY raw code matching the extension type."
        )
        raw_code = call_ollama(ENGINE_MODEL, system_instructions, f"Compile {file_name} for {prd}. Style parameters: {branding}")
        try:
            with open(os.path.join(project_path, file_name), "w", encoding="utf-8") as f:
                f.write(sanitize_and_heal_code(raw_code))
        except Exception:
            print(f"Warning: Could not write {file_name}")

    # Additional deliverables: useful project docs to help the agent feel stronger and more complete
    generate_additional_project_files(project_path, prd, branding)

    # Marketing tone and launch copy
    print("📢 [Creative Director] Writing automated social media marketing launch thread...")
    marketing_prompt = "Write a high-converting, viral 4-tweet launch thread for X (Twitter) promoting this new full-stack app. Include hooks, features, and hashtags."
    campaign_text = call_ollama(DESIGN_MODEL, marketing_prompt, f"Company: {PERMANENT_COMPANY_NAME}\nFeatures:\n{prd}")
    try:
        with open(os.path.join(project_path, "LAUNCH_CAMPAIGN.txt"), "w", encoding="utf-8") as f:
            f.write(campaign_text)
    except Exception:
        print("Warning: Could not write LAUNCH_CAMPAIGN.txt")

    # Git operations (safe and quiet)
    print("📦 [DevOps Automation] Versioning code packages inside local Git branches...")
    try:
        if not os.path.exists(os.path.join(project_path, ".git")):
            subprocess.run(["git", "init"], cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "add", "."], cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "commit", "-m", "Autonomous feature upgrade layer"], cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        print("Warning: Git operations failed or are unavailable.")

    # Deploy step: skip in low-power mode to avoid heavy network/compute
    if not LOW_POWER_MODE:
        try:
            vercel_logs = subprocess.run(["vercel", "--yes", "--prod"], cwd=project_path, stdout=subprocess.PIPE, text=True).stdout
            url_match = re.search(r'https?://[a-zA-Z0-9.-]+\\.vercel\\.app', vercel_logs)
            print(f"🌍 Live Asset URL Location: {url_match.group(0) if url_match else 'Pushed successfully to cluster profile'}")
        except Exception:
            print("Vercel deploy skipped or failed.")
    else:
        print("Vercel deploy skipped in LOW_POWER_MODE.")

    lesson = call_ollama(BRAIN_MODEL, "Identify any UI elements that feel standard or low-effort. Start response exactly with: 'DESIGN LESSON learned:'", prd)
    try:
        lesson_id = len([f for f in os.listdir(DESIGN_MEMORY_DIR) if f.endswith('.txt')]) + 1
        with open(os.path.join(DESIGN_MEMORY_DIR, f"lesson_{lesson_id}.txt"), "w", encoding="utf-8") as lf:
            lf.write(lesson)
        print(f"📝 Evolving Memory Lesson logged: 'lesson_{lesson_id}.txt'")
    except Exception:
        print("Warning: Could not write design memory lesson.")

    save_agent_state(state)
    return {
        "company": PERMANENT_COMPANY_NAME,
        "project_path": project_path,
        "product_requirements": prd_path,
        "plan": plan,
        "branding": branding,
        "low_power": LOW_POWER_MODE,
        "offline": OFFLINE_MODE,
    }


# Backwards-compatible wrapper: smart_founder imports this name
def build_and_deploy_fullstack_company():
    return run_continuous_company_growth()


def parse_args():
    parser = argparse.ArgumentParser(description="Nova Core Platform autonomous founder agent")
    parser.add_argument("--once", action="store_true", help="Run one cycle only")
    parser.add_argument("--loop", action="store_true", help="Run forever with a cooldown")
    parser.add_argument("--interval", type=int, default=20, help="Loop interval in seconds")
    parser.add_argument("--offline", action="store_true", help="Force offline stub mode")
    parser.add_argument("--low-power", action="store_true", help="Reduce heavy operations")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.offline:
        os.environ["OFFLINE_MODE"] = "1"
    if args.low_power:
        os.environ["LOW_POWER_MODE"] = "1"

    if args.loop:
        import time
        while True:
            try:
                build_and_deploy_fullstack_company()
                print(f"\n⏰ Cooldown active. Next build sequence starts in {args.interval} seconds...")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n🛑 Infinite Loop Engine paused safely. Enterprise state maintained.")
                break
    else:
        build_and_deploy_fullstack_company()
