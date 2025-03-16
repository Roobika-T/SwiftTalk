from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

# Process variables
slack_process = None
telegram_process = None
whatsapp_process = None
gmail_process = None

# JSON file paths
JSON_FILES = {
    "slack": "slack.json",
    "telegram": "telegram.json",
    "whatsapp": "whatsapp.json",
    "gmail": "gmail.json"
}

def is_process_running(proc):
    return proc is not None and proc.poll() is None

def start_process(script_name):
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    if not os.path.exists(script_path):
        logger.error(f"{script_name} not found at {script_path}")
        return None
    try:
        proc = subprocess.Popen(
            ["python3", script_name],
            cwd=os.path.dirname(__file__),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        logger.info(f"Started {script_name} with PID {proc.pid}")
        return proc
    except Exception as e:
        logger.error(f"Failed to start {script_name}: {e}")
        return None

def stop_process(proc):
    if is_process_running(proc):
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            logger.warning(f"Force killed process with PID {proc.pid}")
        logger.info(f"Stopped process with PID {proc.pid}")
        return True
    return False

def read_json_file(file_path):
    """Read and return the contents of a JSON file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        else:
            logger.warning(f"File {file_path} not found")
            return {}
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return {}

# Slack Routes
@app.route('/start_slack', methods=['POST'])
def start_slack():
    global slack_process
    if is_process_running(slack_process):
        return jsonify({"status": "error", "message": "Slack monitoring is already running"}), 400
    slack_process = start_process("cfslack.py")
    if slack_process is None:
        return jsonify({"status": "error", "message": "Failed to start Slack monitoring"}), 500
    return jsonify({"status": "success", "message": "Slack monitoring started"}), 200

@app.route('/stop_slack', methods=['POST'])
def stop_slack():
    global slack_process
    if stop_process(slack_process):
        slack_process = None
        return jsonify({"status": "success", "message": "Slack monitoring stopped"}), 200
    return jsonify({"status": "error", "message": "Slack monitoring is not running"}), 400

@app.route('/slack.json', methods=['GET'])
def get_slack_json():
    data = read_json_file(JSON_FILES["slack"])
    return jsonify(data), 200

# Telegram Routes
@app.route('/start_telegram', methods=['POST'])
def start_telegram():
    global telegram_process
    if is_process_running(telegram_process):
        return jsonify({"status": "error", "message": "Telegram monitoring is already running"}), 400
    telegram_process = start_process("cftel.py")
    if telegram_process is None:
        return jsonify({"status": "error", "message": "Failed to start Telegram monitoring"}), 500
    return jsonify({"status": "success", "message": "Telegram monitoring started"}), 200

@app.route('/stop_telegram', methods=['POST'])
def stop_telegram():
    global telegram_process
    if stop_process(telegram_process):
        telegram_process = None
        return jsonify({"status": "success", "message": "Telegram monitoring stopped"}), 200
    return jsonify({"status": "error", "message": "Telegram monitoring is not running"}), 400

@app.route('/telegram.json', methods=['GET'])
def get_telegram_json():
    data = read_json_file(JSON_FILES["telegram"])
    return jsonify(data), 200

# WhatsApp Routes
@app.route('/start_whatsapp', methods=['POST'])
def start_whatsapp():
    global whatsapp_process
    if is_process_running(whatsapp_process):
        return jsonify({"status": "error", "message": "WhatsApp monitoring is already running"}), 400
    whatsapp_process = start_process("cfwhatsapp.py")
    if whatsapp_process is None:
        return jsonify({"status": "error", "message": "Failed to start WhatsApp monitoring"}), 500
    return jsonify({"status": "success", "message": "WhatsApp monitoring started"}), 200

@app.route('/stop_whatsapp', methods=['POST'])
def stop_whatsapp():
    global whatsapp_process
    if stop_process(whatsapp_process):
        whatsapp_process = None
        return jsonify({"status": "success", "message": "WhatsApp monitoring stopped"}), 200
    return jsonify({"status": "error", "message": "WhatsApp monitoring is not running"}), 400

@app.route('/whatsapp.json', methods=['GET'])
def get_whatsapp_json():
    data = read_json_file(JSON_FILES["whatsapp"])
    return jsonify(data), 200

# Gmail Routes
@app.route('/start_gmail', methods=['POST'])
def start_gmail():
    global gmail_process
    if is_process_running(gmail_process):
        return jsonify({"status": "error", "message": "Gmail monitoring is already running"}), 400
    gmail_process = start_process("fdgmail.py")
    if gmail_process is None:
        return jsonify({"status": "error", "message": "Failed to start Gmail monitoring"}), 500
    return jsonify({"status": "success", "message": "Gmail monitoring started"}), 200

@app.route('/stop_gmail', methods=['POST'])
def stop_gmail():
    global gmail_process
    if stop_process(gmail_process):
        gmail_process = None
        return jsonify({"status": "success", "message": "Gmail monitoring stopped"}), 200
    return jsonify({"status": "error", "message": "Gmail monitoring is not running"}), 400

@app.route('/gmail.json', methods=['GET'])
def get_gmail_json():
    data = read_json_file(JSON_FILES["gmail"])
    return jsonify(data), 200

# Health Check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
    except Exception as e:
        logger.error(f"Failed to start Flask app: {e}")
    finally:
        logger.info("Shutting down Flask app...")
        for proc in [slack_process, telegram_process, whatsapp_process, gmail_process]:
            if is_process_running(proc):
                stop_process(proc)