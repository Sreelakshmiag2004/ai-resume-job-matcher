from dotenv import load_dotenv
import os
from twilio.rest import Client
load_dotenv()
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
msg = client.messages.create(
    from_=os.getenv('TWILIO_WHATSAPP_FROM'),
    body='🧪 Production test - .env working!',
    to=os.getenv('TWILIO_WHATSAPP_TO')
)
print('✅ Production WhatsApp works!')
