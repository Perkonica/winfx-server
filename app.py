from flask import Flask, request, Response, jsonify
from threading import Lock
import os

app = Flask(__name__)

# ===============================
# GLOBAL STATE
# ===============================
watermark_text = "Hello, {roblox_user}\nSuccessfully loaded at {game_name_roblox}"
watermark_triggered = False  # New flag to track if button3 was pressed
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
            return Response("", status=204)  # No content - watermark not triggered yet
        
        # Reset the trigger after sending
        watermark_triggered = False
        return Response(watermark_text, mimetype="text/plain")

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
        watermark_triggered = True  # Set the trigger flag
    
    return {
        "success": True,
        "message": "Watermark updated and triggered!",
        "watermark": watermark_text
    }, 200

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {"status": "Server is running", "watermark_set": bool(watermark_text)}, 200

# Legacy routes for backward compatibility
@app.route("/", methods=["GET"])
def get_text():
    """Legacy GET route"""
    auth = request.headers.get("X-Auth")
    if auth != SECRET_KEY:
        return Response("Forbidden", status=403)
    
    global watermark_text, watermark_triggered
    with lock:
        if not watermark_triggered or not watermark_text:
            return Response("", status=204)
        watermark_triggered = False
        return Response(watermark_text, mimetype="text/plain")

@app.route("/set", methods=["POST"])
def set_text():
    """Legacy SET route"""
    auth = request.headers.get("X-Auth")
    if auth != SECRET_KEY:
        return "Forbidden", 403
    
    global watermark_text, watermark_triggered
    new_text = request.form.get("text")
    if not new_text:
        return "No text provided", 400
    
    with lock:
        watermark_text = new_text
        watermark_triggered = True
    
    return "OK", 200

# ===============================
# RUN SERVER
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)
