import os
from flask import Flask, render_template, request, jsonify, send_from_directory
import google.generativeai as genai

app = Flask(__name__)

# --- Config Gemini ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Stable models in order of preference
MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]

def ask_gemini(prompt):
    if not GOOGLE_API_KEY:
        return "⚠️ AI Key not set in Render. Add GOOGLE_API_KEY in Environment."
    
    last_error = ""
    for model_name in MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_error = str(e)
            print(f"Failed with {model_name}: {e}")
            continue
    
    # If all fail
    if "503" in last_error or "UNAVAILABLE" in last_error:
        return "⚡ AI is busy right now (high demand). Please try again in 10 seconds."
    return "AI is temporarily busy. Please try again."

# --- 24/7 Routes for UptimeRobot ---
@app.route('/health')
def health():
    return "ok", 200

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'logo.png')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ai', methods=['POST'])
def ai_chat():
    data = request.get_json()
    user_msg = data.get('message', '') if data else ''
    assistant_type = data.get('assistant', 'General Assistant')
    
    if not user_msg:
        return jsonify({"reply": "Send a message."})
    
    full_prompt = f"You are {assistant_type} for Dmerick Hub. User: {user_msg}"
    reply = ask_gemini(full_prompt)
    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)	
