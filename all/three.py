from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import logging
import random

# Configure logging
logging.basicConfig(filename='chatbot3.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

WELCOME_MENU = (
    "Hello 👋\n"
    "Welcome to Evolve Clinic Den Haag.\n"
    "1️⃣ About us\n"
    "2️⃣ Prices\n"
    "3️⃣ Online booking 📅\n"
    "4️⃣ Cancel appointment ❌\n"
    "🔙 Back to main menu"
)

COMPANY_DATA = {
    '1': "Evolve Clinic Den Haag - About us: We provide exceptional beauty services.",
    '2': "Evolve Clinic Den Haag - Prices: Visit our website for detailed pricing information.",
    '3': "Evolve Clinic Den Haag - Online booking: You can book an appointment online at our website.",
    '4': "Evolve Clinic Den Haag - Cancel appointment: Please contact us to cancel your appointment."
}

COMMON_RESPONSES = {
    'hello': ["Hello! How can I assist you today?", "Hi there! How can I help you?", "Hey! What can I do for you?"],
    'hi': ["Hello! How can I assist you today?", "Hi there! How can I help you?", "Hey! What can I do for you?"],
    'bye': ["Goodbye! Have a great day!", "See you later!", "Bye! Take care!"],
    'thank you': ["You're welcome!", "Happy to help!", "No problem at all!"],
    'thanks': ["You're welcome!", "Happy to help!", "No problem at all!"],
    'how are you': ["I'm just a bot, but I'm here to help you!", "I'm doing great! How about you?", "I'm here and ready to assist you!"]
}

@app.route('/bot3', methods=['POST'])
def bot3():
    incoming_msg = request.values.get('Body', '').strip().lower()
    session_id = request.values.get('WaId', 'default_session')
    logging.info(f"Incoming message: {incoming_msg} from session: {session_id}")

    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg in COMMON_RESPONSES:
        response = random.choice(COMMON_RESPONSES[incoming_msg])
        logging.info(f"Responding with common response: {response}")
        msg.body(response)
    elif incoming_msg in COMPANY_DATA:
        response = COMPANY_DATA[incoming_msg]
        logging.info(f"Responding with company data: {response}")
        msg.body(response)
    else:
        logging.info("Invalid selection, sending welcome menu.")
        msg.body(WELCOME_MENU)

    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
