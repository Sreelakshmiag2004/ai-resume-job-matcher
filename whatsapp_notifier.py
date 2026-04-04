import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load .env ONCE when module loads
load_dotenv()

def send_whatsapp_message(message):
    """Send WhatsApp message with full error checking"""
    
    # Debug: Print what we found
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN") 
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    to_number = os.getenv("TWILIO_WHATSAPP_TO")
    
    print(f"[DEBUG] SID: {'SET' if account_sid else 'MISSING'}")
    print(f"[DEBUG] FROM: {from_number}")
    print(f"[DEBUG] TO: {to_number}")
    
    if not all([account_sid, auth_token, from_number, to_number]):
        print("❌ MISSING .env variables!")
        print("Create .env with:")
        print("TWILIO_ACCOUNT_SID=your_account_sid_here")
        print("TWILIO_AUTH_TOKEN=your_auth_token_here")
        print("TWILIO_WHATSAPP_FROM=whatsapp:+1234567890")
        print("TWILIO_WHATSAPP_TO=whatsapp:+1234567890")
        return False

    try:
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        print(f"📱 WhatsApp sent! SID: {msg.sid}")
        return True
    except Exception as e:
        print(f"❌ WhatsApp error: {e}")
        return False