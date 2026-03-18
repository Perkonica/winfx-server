from flask import Flask, request, Response, jsonify
from threading import Lock
import os

app = Flask(__name__)

# ===============================
# GLOBAL STATE
# ===============================
global_text = ""
watermark_template = "Hello, {roblox_user}\nSuccessfully loaded at {game_name_roblox}"
watermark_triggered = False
formatted_watermark = ""
lock = Lock()

# ===============================
# AUTH SECRET
# ===============================
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "WINFX_91fA3cX9KQ72mP"
)

# ===============================
# ROUTES
# ===============================

# ORIGINAL ROUTES (keeping for backwards compatibility)
@app.route("/", methods=["GET"])
def get_text():
    auth = request.headers.get("X-Auth")
    if auth != SECRET_KEY:
        return Response("Forbidden", status=403)
    
    global formatted_watermark
    with lock:
        if not formatted_watermark:
            return Response("", status=204)
        text = formatted_watermark
        formatted_watermark = ""  # clear after sending
        return Response(text, mimetype="text/plain")

@app.route("/set", methods=["POST"])
def set_text():
    auth = request.headers.get("X-Auth")
    if auth != SECRET_KEY:
        return "Forbidden", 403
    
    global watermark_template, watermark_triggered
    new_text = request.form.get("text")
    if not new_text:
        return "No text provided", 400
    
    with lock:
        watermark_template = new_text
        watermark_triggered = True
    
    return "OK", 200

# NEW ROUTES FOR WATERMARK SYSTEM
@app.route("/api/get-watermark", methods=["GET"])
def get_watermark():
    """Roblox script calls this to get the watermark when triggered"""
    auth = request.headers.get("X-Auth")
    if auth != SECRET_KEY:
        return Response("Forbidden", status=403)
    
    global watermark_template, watermark_triggered
    with lock:
        if not watermark_triggered:
            return Response("", status=204)
        
        watermark_triggered = False
        return Response(watermark_template, mimetype="text/plain")

@app.route("/api/send-formatted", methods=["POST"])
def receive_formatted():
    """Roblox sends the formatted watermark back here"""
    auth = request.headers.get("X-Auth")
    if auth != SECRET_KEY:
        return "Forbidden", 403
    
    global formatted_watermark
    
    data = request.get_json()
    if not data or "formatted" not in data:
        return "No formatted text provided", 400
    
    with lock:
        formatted_watermark = data["formatted"]
    
    print(f"Received formatted watermark:\n{formatted_watermark}")
    
    return {"success": True}, 200

@app.route("/api/health", methods=["GET"])
def health():
    """Health check"""
    return {"status": "ok", "watermark_triggered": watermark_triggered}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
