import os
from flask import Flask, request, jsonify, send_from_directory
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
from agent.api_manager import LangGraphAPIManager

app = Flask(__name__, static_folder="web", static_url_path="")
if CORS_AVAILABLE:
    CORS(app)

# Initialize API manager
api_manager = LangGraphAPIManager()

@app.get("/")
def index():
    return send_from_directory("web", "index.html")

@app.post("/api/chat")
def api_chat():
    global api_manager
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id")
    model_provider = data.get("model_provider")
    
    if not message:
        return jsonify({"error": "message is required"}), 400
    
    try:
        # Update provider if specified
        if model_provider and model_provider != api_manager.provider:
            api_manager = LangGraphAPIManager(provider=model_provider)
        
        response = api_manager.process_message(message, session_id)
        return jsonify(response.model_dump())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/sessions/<session_id>/state")
def get_session_state(session_id):
    """Get current session state"""
    state = api_manager.get_session_state(session_id)
    return jsonify(api_manager.serialize_state(state))

@app.post("/api/sessions/<session_id>/reset")
def reset_session(session_id):
    """Reset a session"""
    if session_id in api_manager.active_sessions:
        del api_manager.active_sessions[session_id]
    return jsonify({"status": "reset"})

@app.get("/api/pv-curves/<path:filename>")
def serve_pv_curve(filename):
    """Serve generated PV curve images"""
    return send_from_directory("generated", filename)

@app.get("/api/available-grids")
def get_available_grids():
    """Get list of available grid systems"""
    return jsonify({
        "grids": ["ieee14", "ieee24", "ieee30", "ieee39", "ieee57", "ieee118", "ieee300"]
    })

@app.get("/api/graphs")
def get_graphs():
    """Get list of generated graphs"""
    import glob
    import re
    from datetime import datetime
    
    graphs = []
    pattern = os.path.join("generated", "pv_curve_*.png")
    
    for filepath in glob.glob(pattern):
        filename = os.path.basename(filepath)
        
        # Parse filename: pv_curve_ieee39_20240101_120000.png
        match = re.match(r'pv_curve_([^_]+)_(\d{8}_\d{6})\.png', filename)
        if match:
            grid = match.group(1)
            timestamp_str = match.group(2)
            
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_time = timestamp_str
            
            graphs.append({
                "filename": filename,
                "title": f"PV Curve - {grid.upper()}",
                "grid": grid.upper(),
                "bus": "Unknown",  # Could be parsed from metadata if available
                "timestamp": formatted_time,
                "filepath": filepath
            })
    
    # Sort by most recent first
    graphs.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(graphs)

@app.delete("/api/graphs")
def clear_graphs():
    """Clear all generated graphs"""
    import glob
    
    pattern = os.path.join("generated", "pv_curve_*.png")
    deleted_count = 0
    
    for filepath in glob.glob(pattern):
        try:
            os.remove(filepath)
            deleted_count += 1
        except OSError:
            pass
    
    return jsonify({"deleted": deleted_count})

@app.post("/api/model")
def set_model():
    """Set the AI model provider"""
    global api_manager
    data = request.get_json(silent=True) or {}
    provider = data.get("provider", "ollama")
    
    if provider not in ["ollama", "openai"]:
        return jsonify({"error": "Invalid provider"}), 400
    
    try:
        # Reinitialize API manager with new provider
        api_manager = LangGraphAPIManager(provider=provider)
        return jsonify({"status": "success", "provider": provider})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/model/status")
def get_model_status():
    """Get current model status"""
    return jsonify({
        "provider": api_manager.provider,
        "status": "connected"  # Simplified status
    })

@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting PV Curve API Server on port {port}")
    print("Access the web interface at: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=port, debug=True)