from slack_sdk import WebClient
from dotenv import load_dotenv
import os
load_dotenv()
SLACK_TOKEN = os.getenv("BOT_TOKEN")
client = WebClient(token=SLACK_TOKEN)

def list_channels():
    try:
        response = client.conversations_list()
        channels = response['channels']
        print("Channels associated with the Bot token",end="\n")
        for channel in channels:
            print(f"Channel Name: {channel['name']}, Channel ID: {channel['id']}")
    except Exception as e:
        print(f"Error listing channels: {str(e)}")

if __name__ == '__main__':
    list_channels()
