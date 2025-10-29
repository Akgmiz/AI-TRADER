import os, requests, time, traceback
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configure via environment variables
RENDER_API_TOKEN = os.getenv("RENDER_API_TOKEN", "")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID", "")
ALLOWED_KEYS = os.getenv("ALLOWED_KEYS", "")  # optional comma-separated keys for simple auth

def get_build_logs():
    if not RENDER_API_TOKEN or not RENDER_SERVICE_ID:
        raise RuntimeError("RENDER_API_TOKEN and RENDER_SERVICE_ID must be set as environment variables.")
    headers = {"Authorization": f"Bearer {RENDER_API_TOKEN}", "Accept": "application/json"}
    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/logs"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def simple_auth_ok(req):
    if not ALLOWED_KEYS:
        return True
    key = req.headers.get("X-API-KEY", "")
    allowed = [k.strip() for k in ALLOWED_KEYS.split(",") if k.strip()]
    return key in allowed

@app.route("/logs", methods=["GET"])
def fetch_logs():
    try:
        if not simple_auth_ok(request):
            return jsonify({"status": "error", "error": "unauthorized"}), 401
        logs = get_build_logs()
        return jsonify({"status": "ok", "logs": logs})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "trace": traceback.format_exc()}), 500

@app.route("/debug", methods=["POST"])
def debug_with_ai():
    """
    Accepts: { "logs": "<string>" } OR will fetch logs from Render if none provided.
    Returns: a JSON diagnosis and suggested_fix.
    """
    try:
        if not simple_auth_ok(request):
            return jsonify({"status": "error", "error": "unauthorized"}), 401

        payload = request.json or {}
        build_output = payload.get("logs", None)
        if not build_output:
            # fetch from Render API
            build_output = get_build_logs()

        # Heuristic analysis (can be replaced by an AI-backed model call)
        diagnostics = []
        lower = build_output.lower()
        if "module not founderror" in lower or "modulenotfounderror" in lower:
            diagnostics.append("ModuleNotFoundError detected — missing Python package. Add the missing package to requirements.txt and redeploy.")
        if "syntaxerror" in lower:
            diagnostics.append("SyntaxError detected — check indentation, parentheses or invalid syntax in the mentioned file and line number.")
        if "pip install" in lower and ("failed" in lower or "error" in lower):
            diagnostics.append("pip install failure — try pinning dependency versions or increasing build resources. Check wheels vs source build.")
        if "permission denied" in lower:
            diagnostics.append("Permission denied — check file permissions and user running the build step.")
        if "out of memory" in lower or "oom" in lower:
            diagnostics.append("Out of memory — build is exceeding memory limits; try smaller build or increase plan.")
        if not diagnostics:
            diagnostics.append("No obvious pattern detected. Consider sharing a larger snippet of the build log or running the build locally for step-by-step debugging.")

        # Simple suggested fixes based on first diagnostic
        suggested_fixes = []
        for d in diagnostics:
            if "missing python package" in d.lower() or "modulenotfounderror" in d.lower():
                suggested_fixes.append("Add the missing package to requirements.txt; ensure correct package name/version; then redeploy.")
            elif "syntaxerror" in d.lower():
                suggested_fixes.append("Open the file and inspect the indicated line number for syntax issues; run `python -m pyflakes <file>` or `python -m py_compile <file>` locally.")
            elif "pip install failure" in d.lower():
                suggested_fixes.append("Pin dependency versions in requirements.txt, try `pip wheel` for heavy packages, or add system dependencies in your Render build script.")
            elif "out of memory" in d.lower():
                suggested_fixes.append("Use smaller build, split heavy dependencies, or upgrade Render plan. Add swap in build stage if possible.")
            else:
                suggested_fixes.append("Inspect logs, confirm environment variables, and retry the build.")

        response = {
            "status": "ok",
            "diagnostics": diagnostics,
            "suggested_fixes": suggested_fixes,
            "note": "This is a heuristic assistant. For deeper analysis, connect an LLM and forward the logs for natural-language diagnosis."
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "trace": traceback.format_exc()}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok","service":"render-mcp-debug-agent"})

@app.route("/ready", methods=["GET"])
def ready():
    # quick readiness probe
    try:
        # if env configured return ready
        return jsonify({"ready": bool(RENDER_API_TOKEN and RENDER_SERVICE_ID)})
    except Exception:
        return jsonify({"ready": False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","7070")))

