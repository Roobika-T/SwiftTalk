import imaplib
import smtplib
import email
from email.message import EmailMessage
import time
from dotenv import load_dotenv
import os
import google.generativeai as genai
from datetime import datetime, timezone, timedelta
import re
import json

load_dotenv()

EMAIL_ADDRESS = os.getenv('SENDER_EMAIL')
EMAIL_PASSWORD = os.getenv('SENDER_PASS')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

IMAP_SERVER = 'imap.gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
INTERVAL = 0
TIME_WINDOW = 30

genai.configure(api_key=GEMINI_API_KEY)

BLOCKED_SENDERS = ["no-reply@", "noreply@", "newsletter@", "marketing@", "promotions@", "donotreply@", "sales@", "info@"]
SPAM_KEYWORDS = ["discount", "offer", "promotion", "subscribe", "deal", "win", "sale", "buy now"]

email_threads = {}
processed_messages = []
important_emails = {}

def is_valid_sender(sender_email):
    sender_email = sender_email.lower()
    return not any(blocked in sender_email for blocked in BLOCKED_SENDERS)

def is_recent_email(email_date):
    try:
        email_dt = email.utils.parsedate_to_datetime(email_date).replace(tzinfo=timezone.utc)
        time_diff = (datetime.now(timezone.utc) - email_dt).total_seconds() / 60
        print(f"Email timestamp: {email_dt}, Time difference: {time_diff:.2f} minutes")
        return time_diff <= TIME_WINDOW
    except Exception as e:
        print(f"Error parsing email date '{email_date}': {e}")
        return False

def categorize_email(subject, body):
    text = (subject + body).lower()
    if "urgent" in text:
        return "Urgent"
    elif "follow up" in text:
        return "Follow-up"
    return "Low Priority"

def summarize_email(body):
    if len(body.split()) > 50:
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            summary = model.generate_content(f"Summarize this: {body}").text.strip()
            return summary
        except Exception as e:
            print(f"Summary generation failed: {e}")
    return body

def summarize_thread(messages):
    if len(messages) < 3:
        return "No thread summary yet."
    try:
        combined_text = "\n\n".join(messages)
        model = genai.GenerativeModel('gemini-1.5-pro')
        return model.generate_content(f"Summarize this thread: {combined_text}").text.strip()
    except Exception as e:
        print(f"Thread summary failed: {e}")
        return "Summary unavailable."

def suggest_responses(body):
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        responses = model.generate_content(f"Suggest 3 quick responses for: {body}").text.strip().split('\n')
        return responses[:3]
    except Exception as e:
        print(f"Response suggestion failed: {e}")
        return ["Thank you for your email.", "I'll get back to you soon.", "Processing your request."]

def generate_response(body):
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        return model.generate_content(f"Generate a professional response to: {body}").text.strip()
    except Exception as e:
        print(f"AI response failed: {e}")
        return "Thank you for your email. This is an automated response - I'll reply with more details soon."

def send_reply(to_email, subject, response_text):
    msg = EmailMessage()
    msg['Subject'] = f"Re: {subject}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(response_text)
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Reply sent to {to_email}")
    except Exception as e:
        print(f"Failed to send reply to {to_email}: {e}")

def save_to_json(message_data):
    """Append message_data to gmail.json"""
    filename = "gmail.json"
    try:
        # Read existing data if file exists
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
        else:
            data = {"emails": []}  # Initialize structure if file doesn't exist
        
        # Append new message_data
        data["emails"].append(message_data)
        
        # Write back to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Message data appended to {filename}")
    except Exception as e:
        print(f"Error saving to {filename}: {e}")

def check_mail():
    print(f"\n[{datetime.now()}] Starting email check...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        print("IMAP connection established")
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("Logged in successfully")
        mail.select('inbox')
        print("Inbox selected")

        status, messages = mail.search(None, 'UNSEEN')
        print(f"Search status: {status}, Found {len(messages[0].split())} unseen emails")
        email_ids = messages[0].split()

        if not email_ids:
            print("No new unread emails found.")
            mail.logout()
            return

        for email_id in email_ids:
            print(f"Processing email ID: {email_id}")
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            print(f"Fetch status: {status}")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    sender = msg['From']
                    subject = msg['Subject'] or "No Subject"
                    email_date = msg['Date']

                    sender_email = re.search(r'<(.+?)>', sender)
                    sender_email = sender_email.group(1) if sender_email else sender
                    print(f"Sender: {sender_email}, Subject: {subject}, Date: {email_date}")

                    # Filter out spam and old emails
                    if not is_valid_sender(sender_email):
                        print(f"Skipping {sender_email} - blocked sender")
                        continue
                    if not is_recent_email(email_date):
                        print(f"Skipping {sender_email} - email too old")
                        continue
                    if any(keyword in (subject + "").lower() for keyword in SPAM_KEYWORDS):
                        print(f"Skipping {sender_email} - contains spam keywords")
                        continue

                    # Extract email body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")
                    print(f"Body extracted (first 100 chars): {body[:100]}...")

                    # Track thread
                    normalized_subject = subject.lower().strip()
                    if normalized_subject not in email_threads:
                        email_threads[normalized_subject] = []
                    email_threads[normalized_subject].append(body)

                    # Process email
                    category = categorize_email(subject, body)
                    summarized_body = summarize_email(body)
                    thread_summary = summarize_thread(email_threads[normalized_subject])
                    quick_responses = suggest_responses(summarized_body)
                    ai_response = generate_response(summarized_body)

                    # Store message data
                    message_data = {
                        "status": "success",
                        "message": {
                            "sender": sender_email,
                            "subject": subject,
                            "body": summarized_body,
                            "original_body": body[:200],
                            "priority": category,
                            "thread_summary": thread_summary,
                            "suggested_responses": quick_responses,
                            "response_sent": ai_response,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "received_at": email_date
                        }
                    }
                    processed_messages.append(message_data)
                    
                    # Save to gmail.json
                    save_to_json(message_data)

                    # Log the incoming message
                    print("\n=== New Incoming Message ===")
                    print(f"From: {sender_email}")
                    print(f"Subject: {subject}")
                    print(f"Priority: {category}")
                    print(f"Received: {email_date}")
                    print(f"Body Preview: {body[:100]}...")
                    print(f"AI Response: {ai_response}")
                    print("=====================\n")

                    # Send reply and track important emails
                    send_reply(sender_email, subject, ai_response)
                    if category == "Urgent":
                        important_emails[sender_email] = datetime.now(timezone.utc)

        mail.logout()
        print("IMAP connection closed")

    except Exception as e:
        print(f"Error in check_mail: {e}")

def check_reminders():
    now = datetime.now(timezone.utc)
    for sender_email, timestamp in list(important_emails.items()):
        if now - timestamp > timedelta(hours=1):
            send_reply(sender_email, "Follow-up Reminder", 
                      "Reminder: Please follow up on your previous email.")
            print(f"Sent reminder to {sender_email}")
            del important_emails[sender_email]

if __name__ == '__main__':
    print("Starting email monitoring service...")
    while True:
        try:
            check_mail()
            check_reminders()
            print(f"Waiting {INTERVAL} seconds until next check...")
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            print("\nShutting down email service...")
            with open('processed_emails.json', 'w') as f:
                json.dump(processed_messages, f, indent=2)
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(INTERVAL)