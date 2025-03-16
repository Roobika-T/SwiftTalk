from telethon import TelegramClient, events
import asyncio
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

api_id = '28676963'
api_hash = '9ea34b616d10589a291092ac21533d37'
phone = '+919025329231'

GEMINI_API_KEY = 'AIzaSyA0FrHdKW4_zQuv347HaLS4GVFlulQ-mxc'
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

client = TelegramClient('session_name', api_id, api_hash)

# Global stores
telegram_messages = []
response_cache = {}  # Cache for API responses
last_api_call_time = 0
MIN_API_INTERVAL = 5  # Increased to 5 seconds between API calls to avoid quota issues

# Retry logic for Gemini API calls with fallback
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60), retry=retry_if_exception_type(Exception))
def call_gemini_api(prompt):
    global last_api_call_time
    current_time = time.time()
    time_since_last = current_time - last_api_call_time
    if time_since_last < MIN_API_INTERVAL:
        time.sleep(MIN_API_INTERVAL - time_since_last)
    response = model.generate_content(prompt)
    last_api_call_time = time.time()
    return response.text.strip()

def categorize_priority(message):
    try:
        if message in response_cache.get('priority', {}):
            logger.info(f"Using cached priority for message: {message[:20]}...")
            return response_cache['priority'][message]
        
        prompt = f"Analyze this message and categorize it as 'Urgent', 'Follow-up', or 'Low Priority':\n{message}"
        category = call_gemini_api(prompt)
        category = category if category in ['Urgent', 'Follow-up', 'Low Priority'] else 'Low Priority'
        response_cache.setdefault('priority', {})[message] = category
        logger.info(f"Categorized message '{message[:20]}...' as {category}")
        return category
    except Exception as e:
        logger.error(f"Failed to categorize priority for '{message[:20]}...': {e}")
        return "Low Priority"

def summarize_thread(messages, current_message):
    try:
        relevant_msgs = [msg.text for msg in messages if msg.text and len(msg.text.split()) < 10 and "uuu" not in msg.text]
        if not relevant_msgs:
            return "No relevant thread to summarize."
        thread_key = "\n".join(relevant_msgs[-3:])
        if thread_key in response_cache.get('summary', {}):
            logger.info(f"Using cached summary for thread related to '{current_message[:20]}...'")
            return response_cache['summary'][thread_key]
        
        prompt = f"Summarize this conversation in one sentence, focusing on context relevant to '{current_message}':\n{thread_key}"
        summary = call_gemini_api(prompt)
        response_cache.setdefault('summary', {})[thread_key] = summary
        logger.info(f"Thread summary for '{current_message[:20]}...': {summary}")
        return summary
    except Exception as e:
        logger.error(f"Failed to summarize thread for '{current_message[:20]}...': {e}")
        return "Could not summarize the conversation."

def suggest_response(message):
    try:
        if message in response_cache.get('response', {}):
            logger.info(f"Using cached response for message: {message[:20]}...")
            return response_cache['response'][message]
        
        prompt = f"Based on this message, suggest a concise, appropriate response:\n{message}"
        response = call_gemini_api(prompt)
        response_cache.setdefault('response', {})[message] = response
        logger.info(f"Suggested response for '{message[:20]}...': {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to suggest response for '{message[:20]}...': {e}")
        return "Hi, thanks for your message!"

def save_to_json(message_data):
    """Append message_data to telegram.json"""
    filename = "telegram.json"
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
        else:
            data = {"messages": []}
        
        data["messages"].append(message_data)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        logger.info(f"Message data appended to {filename}")
    except Exception as e:
        logger.error(f"Error saving to {filename}: {e}")

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.is_private and not event.out:
        sender = await event.get_sender()
        incoming_msg = event.text
        sender_name = sender.username or sender.first_name or "Unknown"

        logger.info(f"Received message from {sender_name}: {incoming_msg}")

        priority = categorize_priority(incoming_msg)
        messages = await client.get_messages(event.chat_id, limit=5)
        summary = summarize_thread(messages, incoming_msg)
        suggested_response = suggest_response(incoming_msg)

        message_data = {
            "sender": sender_name,
            "sender_id": sender.id,
            "message": incoming_msg,
            "priority": priority,
            "thread_summary": summary,
            "suggested_response": suggested_response,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        telegram_messages.append(message_data)
        save_to_json(message_data)
        logger.info(f"Processed message: {message_data}")

        try:
            if priority == 'Urgent':
                await event.respond(f"Urgent: {suggested_response}")
            elif priority == 'Follow-up':
                await event.respond(f"I'll follow up soon: {suggested_response}")
            else:
                await event.respond(suggested_response)
            logger.info(f"Sent response to {sender_name}: {suggested_response}")
        except Exception as e:
            logger.error(f"Failed to send response to {sender_name}: {e}")
            await event.respond("Hi, there was an issue processing your message. I'll get back to you soon!")

async def start_telegram_client():
    try:
        logger.info("Connecting to Telegram...")
        await client.connect()

        if not await client.is_user_authorized():
            logger.info(f"First-time login required for {phone}")
            await client.send_code_request(phone)
            code = input("Enter the code you received: ")
            try:
                await client.sign_in(phone, code)
            except Exception as e:
                logger.error(f"Login failed: {e}")
                return

        logger.info("Telegram client started. Listening for messages...")
        await client.run_until_disconnected()

    except Exception as e:
        logger.error(f"Error in Telegram client: {e}")
    finally:
        await client.disconnect()
        logger.info("Telegram client disconnected")

if __name__ == '__main__':
    try:
        logger.info("Running Telegram client standalone...")
        asyncio.run(start_telegram_client())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")