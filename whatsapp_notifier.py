import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
YOUR_WHATSAPP_NUMBER = os.getenv("YOUR_WHATSAPP_NUMBER")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp_message(message):
    client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=YOUR_WHATSAPP_NUMBER
    )