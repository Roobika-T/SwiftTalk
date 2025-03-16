from flask import Flask, jsonify, request
import asyncio
import time
import threading
from typing import Dict, Any
from xvfbwrapper import Xvfb

# Initialize virtual display at startup
vdisplay = Xvfb()
vdisplay.start()

# Now it's safe to import modules that require a display
from cfslack import monitor_slack_channel
from cftel import main as telegram_main
from cfwhatsapp import check_and_reply
from fdgmail import check_mail, check_reminders

app = Flask(__name__)

services_status = {
    "slack": {"running": False, "thread": None},
    "telegram": {"running": False, "thread": None},
    "whatsapp": {"running": False, "thread": None},
    "gmail": {"running": False, "thread": None}
}

def run_async_task(func):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(func())

def run_slack_monitoring():
    while services_status["slack"]["running"]:
        try:
            monitor_slack_channel()
            time.sleep(5)
        except Exception as e:
            print(f"Slack monitoring error: {e}")
            time.sleep(10)

def run_telegram_monitoring():
    while services_status["telegram"]["running"]:
        try:
            asyncio.run(telegram_main())
            time.sleep(5)
        except Exception as e:
            print(f"Telegram monitoring error: {e}")
            time.sleep(10)

def run_whatsapp_monitoring():
    # Virtual display is already running from startup
    while services_status["whatsapp"]["running"]:
        try:
            check_and_reply()
            time.sleep(5)
        except Exception as e:
            print(f"Whatsapp monitoring error: {e}")
            time.sleep(10)

def run_gmail_monitoring():
    INTERVAL = 60
    while services_status["gmail"]["running"]:
        try:
            check_mail()
            check_reminders()
            time.sleep(INTERVAL)
        except Exception as e:
            print(f"Gmail monitoring error: {e}")
            time.sleep(INTERVAL)

@app.route('/api/slack/start', methods=['POST'])
def start_slack():
    if not services_status["slack"]["running"]:
        services_status["slack"]["running"] = True
        thread = threading.Thread(target=run_slack_monitoring)
        services_status["slack"]["thread"] = thread
        thread.start()
        return jsonify({"status": "success", "message": "Slack monitoring started"})
    return jsonify({"status": "error", "message": "Slack monitoring already running"})

@app.route('/api/telegram/start', methods=['POST'])
def start_telegram():
    if not services_status["telegram"]["running"]:
        services_status["telegram"]["running"] = True
        thread = threading.Thread(target=run_telegram_monitoring)
        services_status["telegram"]["thread"] = thread
        thread.start()
        return jsonify({"status": "success", "message": "Telegram monitoring started"})
    return jsonify({"status": "error", "message": "Telegram monitoring already running"})

@app.route('/api/whatsapp/start', methods=['POST'])
def start_whatsapp():
    if not services_status["whatsapp"]["running"]:
        services_status["whatsapp"]["running"] = True
        thread = threading.Thread(target=run_whatsapp_monitoring)
        services_status["whatsapp"]["thread"] = thread
        thread.start()
        return jsonify({"status": "success", "message": "WhatsApp monitoring started"})
    return jsonify({"status": "error", "message": "WhatsApp monitoring already running"})

@app.route('/api/gmail/start', methods=['POST'])
def start_gmail():
    if not services_status["gmail"]["running"]:
        services_status["gmail"]["running"] = True
        thread = threading.Thread(target=run_gmail_monitoring)
        services_status["gmail"]["thread"] = thread
        thread.start()
        return jsonify({"status": "success", "message": "Gmail monitoring started"})
    return jsonify({"status": "error", "message": "Gmail monitoring already running"})

@app.route('/api/<service>/stop', methods=['POST'])
def stop_service(service):
    if service not in services_status:
        return jsonify({"status": "error", "message": "Invalid service"}), 404
    
    if services_status[service]["running"]:
        services_status[service]["running"] = False
        if services_status[service]["thread"]:
            services_status[service]["thread"].join()
        services_status[service]["thread"] = None
        return jsonify({"status": "success", "message": f"{service.capitalize()} monitoring stopped"})
    return jsonify({"status": "error", "message": f"{service.capitalize()} monitoring not running"})

@app.route('/api/status', methods=['GET'])
def get_status():
    status = {service: {"running": info["running"]} 
             for service, info in services_status.items()}
    return jsonify({"status": "success", "services": status})

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        # Cleanup
        for service in services_status:
            services_status[service]["running"] = False
        for service in services_status:
            if services_status[service]["thread"]:
                services_status[service]["thread"].join()
        if vdisplay:
            vdisplay.stop()
            print("Virtual display stopped")