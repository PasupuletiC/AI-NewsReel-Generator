# app_flask.py
from flask import Flask, render_template, jsonify, send_from_directory, url_for
import os
import pipeline_logic 
import config 

app = Flask(__name__)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_VIDEO_ABSPATH = os.path.join(PROJECT_ROOT, config.OUTPUT_VIDEO_FOLDER)
print(f"Flask App: Absolute path for serving videos from: {OUTPUT_VIDEO_ABSPATH}")
os.makedirs(OUTPUT_VIDEO_ABSPATH, exist_ok=True) 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_video', methods=['POST'])
def trigger_video_generation():
    print("Flask endpoint: /generate_video called")
    
    missing_configs = []
    if any(val.startswith("YOUR_") for val in [config.NEWS_API_KEY, config.PEXELS_API_KEY, config.GEMINI_API_KEY]):
        missing_configs.append("One or more API keys are default placeholders.")
    
    font_path = config.TEXT_FONT
    if not os.path.isabs(font_path): font_path = os.path.join(PROJECT_ROOT, font_path)
    if not os.path.isfile(font_path):
        missing_configs.append(f"Font file '{config.TEXT_FONT}' (resolved to '{font_path}') not found.")

    if missing_configs:
        return jsonify({"success": False, "error_message": f"Config Error(s): {'; '.join(missing_configs)}"}), 500

    results = pipeline_logic.run_video_generation_pipeline()
    
    if results.get("success") and results.get("video_path"):
        filename = os.path.basename(results["video_path"])
        # url_for creates a URL relative to the application's root for the specified endpoint
        results["video_url"] = url_for('serve_video_file', filename=filename) 
        results["actual_video_filename_for_download"] = filename
    
    print(f"Flask endpoint: Sending results to client: {results}")
    return jsonify(results)

@app.route(f'/{config.OUTPUT_VIDEO_FOLDER}/<path:filename>') 
def serve_video_file(filename):
    print(f"Flask: Serving video: '{filename}' from '{OUTPUT_VIDEO_ABSPATH}'")
    try:
        return send_from_directory(OUTPUT_VIDEO_ABSPATH, filename, as_attachment=False)
    except FileNotFoundError:
        print(f"Flask: Video file not found at {os.path.join(OUTPUT_VIDEO_ABSPATH, filename)}")
        return jsonify({"error": "Video file not found on server"}), 404

if __name__ == '__main__':
    pipeline_logic.create_necessary_folders() 
    app.run(debug=True, host='0.0.0.0', port=5000)