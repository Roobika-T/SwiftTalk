import os
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

'''
Expeted response
{
  "status": "success",
  "messages": [
    {
      "channel_id": "C08EM9D3ZFC",
      "message": "Need help with project ASAP",
      "timestamp": "1677654321.123456",
      "summary": "User requests urgent project assistance.",
      "response": "I'm here to help with your project!",
      "processed_at": "2025-02-26 10:30:45"
    }
  ]
}
'''

SLACK_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "C08F8QQV2U9"
client = WebClient(token=SLACK_TOKEN)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# Global list to store Slack message data
slack_messages = []

def fetch_latest_message(channel_id, last_timestamp):
    try:
        response = client.conversations_history(channel=channel_id, limit=1)
        if response["messages"]:
            latest_msg = response["messages"][0]
            msg_text = latest_msg.get("text", "")
            msg_ts = latest_msg.get("ts", "")
            if msg_ts > last_timestamp:
                return msg_text, msg_ts
    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")
    return None, last_timestamp

def generate_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I couldn't generate a response."

def summarize_message(message):
    try:
        prompt = f"Summarize the following message in one or two sentences: {message}"
        summary = model.generate_content(prompt)
        return summary.text
    except Exception as e:
        print(f"Error summarizing message: {e}")
        return "Sorry, I couldn't summarize the message."

def send_reply(channel_id, thread_ts, response_text):
    try:
        client.chat_postMessage(channel=channel_id, text=response_text, thread_ts=thread_ts)
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

def monitor_slack_channel():
    last_timestamp = "0"
    while True:
        msg_text, msg_ts = fetch_latest_message(CHANNEL_ID, last_timestamp)
        if msg_text and msg_ts > last_timestamp:
            response_text = generate_response(msg_text)
            summary = summarize_message(msg_text)
            message_data = {
                "channel_id": CHANNEL_ID,
                "message": msg_text,
                "timestamp": msg_ts,
                "summary": summary,
                "response": response_text,
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            slack_messages.append(message_data)
            send_reply(CHANNEL_ID, msg_ts, response_text)
            last_timestamp = msg_ts
        time.sleep(5)

if __name__ == "__main__":
    monitor_slack_channel()