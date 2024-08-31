from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import logging
import random
import requests

# Configure logging
logging.basicConfig(filename='chatbot_den_haag.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

COMPANY_NAME = 'Ezoncs Beauty Salon Den Haag'
COMPANY_ID = 10

OPTIONS = {
    '1': "About us 🏠",
    '2': "Prices 💲",
    '3': "Online booking 📅",
    '4': "Cancel appointment ❌"
}

DEFAULT_RESPONSES = {
    '1': f"{COMPANY_NAME} - About us 🏠: We provide exceptional beauty services.",
    '2': f"{COMPANY_NAME} - Prices 💲: Visit our website for detailed pricing information.",
    '3': f"{COMPANY_NAME} - Online booking 📅: You can book an appointment online at our website.",
    '4': f"{COMPANY_NAME} - Cancel appointment ❌: Please contact us to cancel your appointment."
}

COMMON_RESPONSES = {
    'hello': [
        "Hello! How can I assist you today? 😊",
        "Hi there! How can I help you? 🤔",
        "Hey! What can I do for you? 🙌",
        "Greetings! How may I be of service? 👋",
        "Hello! What can I do for you today? 😃"
    ],
    'hi': [
        "Hello! How can I assist you today? 😊",
        "Hi there! How can I help you? 🤔",
        "Hey! What can I do for you? 🙌",
        "Greetings! How may I be of service? 👋",
        "Hello! What can I do for you today? 😃"
    ],
    'bye': [
        "Goodbye! Have a great day! 👋",
        "See you later! 👋",
        "Bye! Take care! ✨",
        "Farewell! Wishing you the best! 🌟",
        "Catch you later! 😊"
    ],
    'thank you': [
        "You're welcome! 😃",
        "Happy to help! 😊",
        "No problem at all! 👍",
        "You're welcome! If you need anything else, just ask! 🙏",
        "Glad I could assist! 😄"
    ],
    'thanks': [
        "You're welcome! 😃",
        "Happy to help! 😊",
        "No problem at all! 👍",
        "You're welcome! If you need anything else, just ask! 🙏",
        "Glad I could assist! 😄"
    ],
    'how are you': [
        "I'm just a bot, but I'm here to help you! 🤖",
        "I'm doing great! How about you? 😄",
        "I'm here and ready to assist you! 💪",
        "I'm functioning well, thanks for asking! 😊",
        "I'm at your service! How can I assist? 🤗"
    ],
    'menu': [
        "Here's the menu! What would you like to do? 📜 1: About us 🏠, 2:Prices 💲, 3:Online booking 📅, 4:Cancel appointment ❌",
        "Here are your options. How can I assist you today? 📋 1: About us 🏠, 2:Prices 💲, 3:Online booking 📅, 4:Cancel appointment ❌",
        "Check out our menu below and choose an option! 🗒️ 1: About us 🏠, 2:Prices 💲, 3:Online booking 📅, 4:Cancel appointment ❌",
        "Explore the menu and let me know what you'd like! 📑 1: About us 🏠, 2:Prices 💲, 3:Online booking 📅, 4:Cancel appointment ❌",
        "The menu is ready for you! Choose an option. 📝 1: About us 🏠, 2:Prices 💲, 3:Online booking 📅, 4:Cancel appointment ❌"
    ],
    'back': [
        "Returning to the main menu. 🔙",
        "Going back to the main menu. 🏠",
        "Here is the main menu again. 🔄",
        "Navigating back to the main menu. 🏡",
        "Returning to the main menu options. 📋"
    ],
    'default': [
        "I'm not sure what you mean. Could you please clarify? 🤔",
        "Sorry, I didn't get that. Can you please choose an option from the menu? 🙄",
        "Oops! It looks like your message is unclear. Please try again. 😕",
        "I didn't understand that. Please select an option from the menu. 🤷",
        "That option is not available. Please choose from the menu. 🙁"
    ]
}

API_GET_ENDPOINT = "https://external-api.example.com/getDetails"  # Replace with your actual API GET endpoint
API_POST_ENDPOINT = "https://external-api.example.com/postDetails"  # Replace with your actual API POST endpoint

WELCOME_MENU = (
    f"Hello 👋\n"
    f"Welcome to {COMPANY_NAME}.\n\n"
    f"Please choose an option below:\n"
    f"1️⃣ About us 🏠\n"
    f"2️⃣ Prices 💲\n"
    f"3️⃣ Online booking 📅\n"
    f"4️⃣ Cancel appointment ❌\n"
    f"0️⃣ Back to main menu 🔙"
)

def get_company_details(company_id, option_id):
    try:
        response = requests.get(API_GET_ENDPOINT, params={
            'company_id': company_id,
            'option_id': option_id
        })
        response.raise_for_status()
        data = response.json()
        return data.get('details', DEFAULT_RESPONSES[option_id])
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch details: {e}")
        return DEFAULT_RESPONSES[option_id]

def post_company_details(company_id, company_name, option_id, option_name, details):
    try:
        response = requests.post(API_POST_ENDPOINT, json={
            'company_id': company_id,
            'company_name': company_name,
            'option_id': option_id,
            'option_name': option_name,
            'details': details
        })
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to post details: {e}")
        return False

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip().lower()
    session_id = request.values.get('WaId', 'default_session')
    logging.info(f"Incoming message: {incoming_msg} from session: {session_id}")

    resp = MessagingResponse()
    msg = resp.message()

    if incoming_msg in COMMON_RESPONSES:
        response = random.choice(COMMON_RESPONSES[incoming_msg])
        logging.info(f"Responding with common response: {response}")
        msg.body(response)
    elif incoming_msg == '0':
        logging.info("Returning to main menu.")
        msg.body(WELCOME_MENU)
    elif incoming_msg in OPTIONS:
        option_id = incoming_msg
        option_name = OPTIONS[option_id]
        details = get_company_details(COMPANY_ID, option_id)
        
        post_status = post_company_details(COMPANY_ID, COMPANY_NAME, option_id, option_name, details)
        if post_status:
            logging.info(f"Successfully posted details for option {option_id} to external API.")
        else:
            logging.error(f"Failed to post details for option {option_id} to external API.")
        
        response = f"{COMPANY_NAME} - {option_name}: {details}\n\nPress 0 to go back to the main menu 🔙."
        logging.info(f"Responding with details: {response}")
        msg.body(response)
    else:
        logging.info("Invalid selection, sending default response.")
        response = random.choice(COMMON_RESPONSES['default'])
        msg.body(response)

    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
