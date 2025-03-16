from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import json  # Add this for JSON handling
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import backoff

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("whatsapp_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = 'AIzaSyA0FrHdKW4_zQuv347HaLS4GVFlulQ-mxc'
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# Configure Chrome options
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--user-data-dir=/Users/roobikatura/chrome-profile')
options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Store processed messages and cached API responses
processed_messages = set()
whatsapp_messages = []
response_cache = {}

def init_driver():
    """Initialize and return the WebDriver"""
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(60)
        driver.get("https://web.whatsapp.com")
        logger.info("Waiting for WhatsApp to load and QR code to be scanned...")
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//div[@id="app"]//div[contains(@class, "two")]'))
        )
        logger.info("WhatsApp loaded successfully")
        return driver
    except Exception as e:
        logger.error(f"Error during WebDriver setup or WhatsApp loading: {e}")
        return None

@backoff.on_exception(backoff.expo, Exception, max_tries=5, giveup=lambda e: not str(e).startswith("429"))
def call_gemini_api(prompt):
    """Call Gemini API with retry logic for 429 errors"""
    response = model.generate_content(prompt)
    return response.text.strip()

def categorize_priority(messages):
    """Categorize message priority using Gemini AI with caching"""
    try:
        message_thread = "\n".join(messages)
        if message_thread in response_cache.get('priority', {}):
            logger.info(f"Using cached priority for thread: {message_thread}")
            return response_cache['priority'][message_thread]

        prompt = f"Analyze this conversation thread and categorize it as 'Urgent', 'Follow-up', or 'Low Priority':\n{message_thread}"
        category = call_gemini_api(prompt)
        category = category if category in ['Urgent', 'Follow-up', 'Low Priority'] else 'Low Priority'
        response_cache.setdefault('priority', {})[message_thread] = category
        logger.info(f"Priority categorized as: {category}")
        return category
    except Exception as e:
        logger.error(f"Error categorizing priority (likely quota exceeded): {e}")
        return 'Low Priority'

def summarize_thread(messages):
    """Summarize conversation thread using Gemini AI with caching"""
    try:
        if not messages:
            return "No messages to summarize."
        
        thread_key = "\n".join(messages)
        if thread_key in response_cache.get('summary', {}):
            logger.info(f"Using cached summary for thread: {thread_key}")
            return response_cache['summary'][thread_key]

        prompt = f"Summarize this conversation in one sentence:\n{thread_key}"
        summary = call_gemini_api(prompt)
        response_cache.setdefault('summary', {})[thread_key] = summary
        logger.info(f"Thread summary: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error summarizing thread (likely quota exceeded): {e}")
        return "Could not summarize the conversation."

def suggest_response(messages, priority):
    """Generate response suggestion using Gemini AI with caching, respecting priority"""
    try:
        message_thread = "\n".join(messages)
        cache_key = f"{message_thread}_{priority}"
        if cache_key in response_cache.get('response', {}):
            logger.info(f"Using cached response for thread: {message_thread} with priority {priority}")
            return response_cache['response'][cache_key]

        prompt = f"Based on this conversation thread and its '{priority}' priority, suggest a concise, appropriate response:\n{message_thread}"
        response = call_gemini_api(prompt)
        response_cache.setdefault('response', {})[cache_key] = response
        logger.info(f"Suggested response for {priority}: {response}")
        return response
    except Exception as e:
        logger.error(f"Error suggesting response (likely quota exceeded): {e}")
        return "Hi, thanks for your message!"

def send_whatsapp_message(driver, phone_number, message):
    """Send WhatsApp message using input fields directly"""
    try:
        input_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
        )
        input_box.clear()
        input_box.send_keys(message)
        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="send"]'))
        )
        send_button.click()
        logger.info(f"Message sent to {phone_number}: {message}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message to {phone_number}: {e}")
        return False

def extract_phone_number(driver, contact_name):
    """Extract phone number from contact profile"""
    try:
        header = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//header[contains(@class, "x1n2onr6")]//div[@title="Profile details"]'))
        )
        header.click()
        time.sleep(2)

        xpaths = [
            '//span[@class="x1jchvi3 x1fcty0u x40yjcy"]',
            '//div[contains(@class, "x1evy7pa")]/span/span[contains(@class, "x1jchvi3")]',
            '//span[contains(@class, "x1jchvi3") and contains(@class, "x1fcty0u") and contains(@class, "x40yjcy")]',
            '//div[contains(@class, "x1gslohp")]//span[contains(@class, "selectable-text")]//span',
        ]
        
        phone_number = "Unknown"
        for xpath in xpaths:
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                phone_number = element.text
                if phone_number and "+91" in phone_number:
                    break
            except Exception:
                continue

        try:
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Close"]'))
            )
            close_button.click()
            time.sleep(1)
        except:
            from selenium.webdriver.common.keys import Keys
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        
        return phone_number
    except Exception as e:
        logger.error(f"Could not extract phone number for {contact_name}: {e}")
        return "Unknown"

def save_to_json(message_data):
    """Append message_data to whatsapp.json"""
    filename = "whatsapp.json"
    try:
        # Read existing data if file exists
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
        else:
            data = {"conversations": []}  # Initialize structure if file doesn't exist
        
        # Append new message_data
        data["conversations"].append(message_data)
        
        # Write back to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        logger.info(f"Message data appended to {filename}")
    except Exception as e:
        logger.error(f"Error saving to {filename}: {e}")

def check_and_reply(driver):
    """Check for unread messages and reply to them"""
    try:
        unread_chat_xpaths = [
            '//div[contains(@class, "_ak8l")]//div[contains(@class, "_ahlk") and .//span[contains(@aria-label, "unread message")]]',
            '//div[contains(@class, "message-in") and .//span[contains(@aria-label, "unread")]]',
            '//span[contains(@aria-label, "unread message")]//ancestor::div[contains(@class, "_ak8l")]'
        ]
        
        unread_chats = []
        for xpath in unread_chat_xpaths:
            try:
                chats = driver.find_elements(By.XPATH, xpath)
                if chats:
                    unread_chats = chats
                    break
            except:
                continue
        
        if not unread_chats:
            logger.info("No unread messages detected.")
            return

        for chat in unread_chats:
            try:
                chat_element = chat.find_element(By.XPATH, './ancestor::div[contains(@class, "_ak8l")]')
                contact_name_xpaths = [
                    './/span[@dir="auto"]',
                    './/div[contains(@class, "copyable-text")]',
                    './/span[contains(@class, "selectable-text")]'
                ]
                
                contact_name = "Unknown Contact"
                for xpath in contact_name_xpaths:
                    try:
                        name_element = chat_element.find_element(By.XPATH, xpath)
                        if name_element and name_element.text:
                            contact_name = name_element.text
                            break
                    except:
                        continue
                
                logger.info(f"Processing chat: {contact_name}")
                chat_element.click()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "_amjy") or contains(@class, "copyable-text")]'))
                )
                time.sleep(2)

                phone_number = extract_phone_number(driver, contact_name)
                message_xpaths = [
                    '//div[contains(@class, "message-in")]//div[contains(@class, "copyable-text")]//span[@dir="ltr"]',
                    '//div[contains(@class, "_acqt")]//div[contains(@class, "copyable-text")]//span',
                    '//div[contains(@class, "message-in")]//span[contains(@class, "selectable-text")]',
                ]
                
                last_five_messages = []
                for xpath in message_xpaths:
                    try:
                        messages = driver.find_elements(By.XPATH, xpath)
                        message_texts = [msg.text for msg in messages if msg.text]
                        if message_texts:
                            last_five_messages = message_texts[-min(5, len(message_texts)):]
                            break
                    except:
                        continue
                
                if not last_five_messages:
                    logger.info(f"Skipping {contact_name}: No messages available.")
                    continue
                
                last_message = last_five_messages[-1]
                message_id = f"{contact_name}_{last_message}_{time.time()}"
                if message_id in processed_messages:
                    continue

                logger.info("\n=== New Incoming Message ===")
                logger.info(f"Contact Name: {contact_name}")
                logger.info(f"Phone Number: {phone_number}")
                logger.info(f"Last Message: {last_message}")
                logger.info(f"Last Five Messages: {last_five_messages}")

                # Analyze the full thread
                priority = categorize_priority(last_five_messages)
                summary = summarize_thread(last_five_messages) if len(last_five_messages) > 1 else "No thread to summarize."
                suggested_response = suggest_response(last_five_messages, priority)
                
                # Ensure response reflects priority
                if priority == 'Urgent':
                    response_text = f"Urgent: {suggested_response}"
                elif priority == 'Follow-up':
                    response_text = f"I'll follow up soon: {suggested_response}"
                else:
                    response_text = suggested_response

                logger.info(f"Priority: {priority}")
                logger.info(f"Thread Summary: {summary}")
                logger.info(f"Suggested Response (raw): {suggested_response}")
                logger.info(f"Response to Send: {response_text}")
                logger.info("=====================\n")

                message_data = {
                    "status": "success",
                    "messages": [{
                        "contact_name": contact_name,
                        "phone_number": phone_number,
                        "message": last_message,
                        "thread": last_five_messages,
                        "priority": priority,
                        "thread_summary": summary,
                        "suggested_response": suggested_response,
                        "response_sent": response_text,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    }]
                }
                whatsapp_messages.append(message_data)
                
                # Save to whatsapp.json
                save_to_json(message_data)

                if send_whatsapp_message(driver, phone_number, response_text):
                    processed_messages.add(message_id)
            except Exception as e:
                logger.error(f"Error processing chat {contact_name}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error in check_and_reply: {e}")

def main():
    """Main function to run the WhatsApp automation"""
    driver = init_driver()
    if not driver:
        logger.error("Failed to initialize WebDriver. Exiting.")
        return
    
    try:
        while True:
            check_and_reply(driver)
            logger.info("Checking for new messages in 10 seconds...")
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Script stopped by user.")
    finally:
        driver.quit()
        logger.info("Driver closed. Program terminated.")

if __name__ == "__main__":
    main()