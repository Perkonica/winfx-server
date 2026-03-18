from flask import Flask, request, Response, jsonify
from threading import Lock
import os

app = Flask(__name__)

# ===============================
# GLOBAL STATE
# ===============================
watermark_text = "Hello, {roblox_user}\nSuccessfully loaded at {game_name_roblox}"
watermark_triggered = False
formatted_watermark = ""  # Store the formatted watermark from Roblox
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

@app.route("/api/get-watermark", methods=["GET"])
def get_watermark():
    """Roblox script calls this to get the current watermark"""
    auth = request.headers.get("X-Auth")
    if auth != SECRET_KEY:
        return Response("Forbidden", status=403)
    
    global watermark_text, watermark_triggered
    with lock:
        # Only return watermark if button3 was pressed
        if not watermark_triggered:
            return Response("", status=204)
        
        # Reset the trigger after sending
        watermark_triggered = False
        return Response(watermark_text, mimetype="text/plain")

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

@app.route("/api/get-formatted", methods=["GET"])
def get_formatted():
    """Windows Forms calls this to get the formatted watermark"""
    auth = request.headers.get("X-Auth")
    if auth != SECRET_KEY:
        return Response("Forbidden", status=403)
    
    global formatted_watermark
    with lock:
        if not formatted_watermark:
            return Response("", status=204)
        
        text = formatted_watermark
        formatted_watermark = ""  # Clear after reading
        return Response(text, mimetype="text/plain")

@app.route("/api/watermark", methods=["POST"])
def set_watermark():
    """Windows Forms app calls this to update the watermark and trigger it"""
    auth = request.headers.get("X-Auth")
    if auth != SECRET_KEY:
        return "Forbidden", 403
    
    global watermark_text, watermark_triggered
    
    # Try to get from JSON first
    if request.is_json:
        data = request.get_json()
        new_text = data.get("watermark")
    else:
        # Fallback to form data
        new_text = request.form.get("watermark") or request.form.get("text")
    
    if not new_text:
        return "No watermark text provided", 400
    
    with lock:
        watermark_text = new_text
        watermark_triggered = True
    
    return {
        "success": True,
        "message": "Watermark updated and triggered!",
        "watermark": watermark_text
    }, 200

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {"status": "Server is running", "watermark_set": bool(watermark_text)}, 200

# ===============================
# RUN SERVER
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"Server starting on port {port}...")
    print(f"Endpoints:")
    print(f"  POST http://localhost:{port}/api/watermark - Set watermark (from Windows Forms)")
    print(f"  GET  http://localhost:{port}/api/get-watermark - Get watermark (from Roblox)")
    print(f"  POST http://localhost:{port}/api/send-formatted - Send formatted (from Roblox)")
    print(f"  GET  http://localhost:{port}/api/get-formatted - Get formatted (from Windows Forms)")
    app.run(host="0.0.0.0", port=port, debug=True)
