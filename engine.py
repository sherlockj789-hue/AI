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

APP_BLUEPRINTS = {
    "saas_dashboard": {
        "name": "SaaS Dashboard",
        "value_prop": "Premium analytics, growth reporting, and executive visibility for modern software businesses.",
        "features": ["Live KPI cards", "workflow automation", "team activity feed", "conversion funnel tracking"],
        "color": "#06b6d4",
        "ui": "dark executive dashboard",
    },
    "ai_assistant": {
        "name": "AI Assistant App",
        "value_prop": "A private AI workspace for drafting, summarizing, brainstorming, and customer responses.",
        "features": ["AI workspace", "smart prompts", "knowledge base", "chat memory"],
        "color": "#8b5cf6",
        "ui": "glass productivity workspace",
    },
    "crm_suite": {
        "name": "CRM Suite",
        "value_prop": "A polished client journey manager for sales, support, and retention workflows.",
        "features": ["pipeline board", "lead score tracking", "automated follow-ups", "task reminders"],
        "color": "#22c55e",
        "ui": "sales command center",
    },
    "marketplace": {
        "name": "Marketplace",
        "value_prop": "A curated marketplace for digital products, services, and premium tools.",
        "features": ["featured listings", "seller dashboard", "search filters", "trust badges"],
        "color": "#f59e0b",
        "ui": "premium storefront",
    },
    "community_app": {
        "name": "Community App",
        "value_prop": "A high-engagement community platform that blends discussion, events, and members.",
        "features": ["member directory", "discussion board", "event calendar", "member goals"],
        "color": "#ec4899",
        "ui": "social engagement hub",
    },
}

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


def generate_additional_project_files(project_path: str, prd: str, branding: str, app_name: str):
    files = {
        "README.md": f"# {app_name}\n\n## Product vision\n{prd[:1200]}\n\n## Brand\n{branding[:800]}\n\n## Deliverables\n- Landing page\n- Product dashboard\n- User auth\n- Live analytics\n- Launch checklist\n",
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


def build_project_plan(prd: str, current_code_context: str, app_name: str):
    base_prompt = (
        "You are a product strategist. Turn the product brief into a sharp execution plan.\n"
        "Return a concise list of 5 winning features, each with a short rationale and a business impact.\n"
        "Format as bullets."
    )
    plan = call_ollama(BRAIN_MODEL, base_prompt, f"App type: {app_name}\nBrief:\n{prd}\n\nCode context:\n{current_code_context}")
    return plan


def build_app_variant(project_path: str, app_key: str, app_meta: dict, generation_seed: str):
    app_name = app_meta["name"]
    print(f"\n🚀 Building app variant: {app_name}")

    variant_dir = os.path.join(project_path, app_key)
    os.makedirs(variant_dir, exist_ok=True)

    product_brief = (
        f"App type: {app_name}\n"
        f"Value proposition: {app_meta['value_prop']}\n"
        f"Primary features: {', '.join(app_meta['features'])}\n"
        f"UI style: {app_meta['ui']}\n"
        f"Market angle: Create a premium and useful {app_name.lower()} that feels polished, modern, and conversion-driven."
    )

    # Create a basic app scaffold using generated snippets and template modules
    landing = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset=\"UTF-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
        <title>{app_name}</title>
      </head>
      <body>
        <div class=\"app-shell\">
          <nav class=\"topbar\">{app_name}</nav>
          <header class=\"hero\">
            <h1>{app_name}</h1>
            <p>{app_meta['value_prop']}</p>
            <button class=\"hyper-btn\">Launch</button>
          </header>
          <section class=\"grid\">
            {''.join(f'<div class=\"card\"><h3>{feature}</h3><p>{app_meta["value_prop"]}</p></div>' for feature in app_meta['features'])}
          </section>
        </div>
      </body>
    </html>
    """

    css = f"""
    body {{ background: #050816; color: #edf2ff; font-family: sans-serif; margin: 0; }}
    .app-shell {{ max-width: 1200px; margin: 0 auto; padding: 32px; }}
    .topbar {{ background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 16px 20px; border-radius: 16px; margin-bottom: 32px; }}
    .hero {{ padding: 40px 20px; border-radius: 24px; background: linear-gradient(135deg, rgba(6,182,212,0.18), rgba(139,92,246,0.18)); border: 1px solid rgba(255,255,255,0.08); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; margin-top: 30px; }}
    .card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 18px; }}
    .hyper-btn {{ background: linear-gradient(135deg, {app_meta['color']}, #6366f1); color: white; border: none; border-radius: 12px; padding: 12px 18px; cursor: pointer; }}
    """

    js = f"""
    async function initApp() {{
      console.log('Starting {app_name}');
      const cards = document.querySelectorAll('.card');
      cards.forEach((card, index) => {{
        card.style.transform = `translateY(${index * 2}px)`;
      }});
    }}
    initApp();
    """

    readme_path = os.path.join(variant_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# {app_name}\n\n{product_brief}\n")

    with open(os.path.join(variant_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(landing)
    with open(os.path.join(variant_dir, "styles.css"), "w", encoding="utf-8") as f:
        f.write(css)
    with open(os.path.join(variant_dir, "app.js"), "w", encoding="utf-8") as f:
        f.write(js)

    try:
        with open(os.path.join(variant_dir, "PRODUCT_REQUIREMENTS.md"), "w", encoding="utf-8") as f:
            f.write(product_brief)
    except Exception:
        pass

    return product_brief


def run_continuous_company_growth():
    state = load_agent_state()
    state["runs"] = int(state.get("runs", 0)) + 1
    state["last_updated"] = datetime.utcnow().isoformat()
    state.setdefault("projects", [])

    project_path = os.path.join(SAFE_SANDBOX_DIR, PERMANENT_COMPANY_NAME)
    os.makedirs(project_path, exist_ok=True)

    print(f"\n⚡ Executing Multi-App Founder Cycle for 【 {PERMANENT_COMPANY_NAME} 】")

    selected_apps = list(APP_BLUEPRINTS.keys())
    if LOW_POWER_MODE:
        selected_apps = selected_apps[:3]

    overall_results = []
    for idx, app_key in enumerate(selected_apps, start=1):
        app_meta = APP_BLUEPRINTS[app_key]
        app_name = app_meta["name"]
        if app_name not in state["projects"]:
            state["projects"].append(app_name)

        brief = build_app_variant(project_path, app_key, app_meta, str(idx))
        overall_results.append({"app": app_name, "brief": brief})

        plan = build_project_plan(brief, "", app_name)
        plan_path = os.path.join(project_path, f"{app_key}_EXECUTION_PLAN.md")
        try:
            with open(plan_path, "w", encoding="utf-8") as f:
                f.write(plan)
        except Exception:
            pass

    save_agent_state(state)
    return {"company": PERMANENT_COMPANY_NAME, "apps": overall_results, "low_power": LOW_POWER_MODE, "offline": OFFLINE_MODE}


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
