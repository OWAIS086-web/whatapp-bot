from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import logging
import random
import re
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# Configure logging
logging.basicConfig(filename='chatbot_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Constants
COMPANY_DETAILS = {
    '1': {'name': 'Ezoncs Beauty Salon Den Haag', 'id': 10},
    '2': {'name': 'Ezoncs Beauty Salon Rotterdam', 'id': 14},
    '3': {'name': 'Evolve Clinic Den Haag', 'id': 17},
    '4': {'name': 'Ezoncs Beauty Salon Amsterdam', 'id': 19},
    '5': {'name': 'Ezoncs Utrecht', 'id': 20},
    '6': {'name': 'Evolve Rotterdam', 'id': 21}
}

WELCOME_MENU = (
    "Hello 👋\n"
    "Please select the company you want to interact with:\n"
    "1️⃣ Ezoncs Beauty Salon Den Haag\n"
    "2️⃣ Ezoncs Beauty Salon Rotterdam\n"
    "3️⃣ Evolve Clinic Den Haag\n"
    "4️⃣ Ezoncs Beauty Salon Amsterdam\n"
    "5️⃣ Ezoncs Utrecht\n"
    "6️⃣ Evolve Rotterdam"
)

COMPANY_MENUS = {key: (
    f"{COMPANY_DETAILS[key]['name']} Menu:\n"
    "1️⃣ About us\n"
    "2️⃣ Prices\n"
    "3️⃣ Online booking 📅\n"
    "4️⃣ Cancel appointment ❌\n"
    "🔙 Back to main menu"
) for key in COMPANY_DETAILS.keys()}

# Initialize company details data
COMPANY_DATA = {
    10: {
        '1': "Ezoncs Beauty Salon Den Haag - About us: We provide exceptional beauty services.",
        '2': "Ezoncs Beauty Salon Den Haag - Prices: Visit our website for detailed pricing information: https://ezoncs-beauty-denhaag.com/prices",
        '3': "Ezoncs Beauty Salon Den Haag - Online booking: You can book an appointment online at our website: https://ezoncs-beauty-denhaag.com/book",
        '4': "Ezoncs Beauty Salon Den Haag - Cancel appointment: Please contact us to cancel your appointment: https://ezoncs-beauty-denhaag.com/contact"
    },
    14: {
        '1': "Ezoncs Beauty Salon Rotterdam - About us: We provide exceptional beauty services.",
        '2': "Ezoncs Beauty Salon Rotterdam - Prices: Visit our website for detailed pricing information: https://ezoncs-beauty-rotterdam.com/prices",
        '3': "Ezoncs Beauty Salon Rotterdam - Online booking: You can book an appointment online at our website: https://ezoncs-beauty-rotterdam.com/book",
        '4': "Ezoncs Beauty Salon Rotterdam - Cancel appointment: Please contact us to cancel your appointment: https://ezoncs-beauty-rotterdam.com/contact"
    },
    17: {
        '1': "Evolve Clinic Den Haag - About us: We provide exceptional beauty services.",
        '2': "Evolve Clinic Den Haag - Prices: Visit our website for detailed pricing information: https://evolve-denhaag.com/prices",
        '3': "Evolve Clinic Den Haag - Online booking: You can book an appointment online at our website: https://evolve-denhaag.com/book",
        '4': "Evolve Clinic Den Haag - Cancel appointment: Please contact us to cancel your appointment: https://evolve-denhaag.com/contact"
    },
    19: {
        '1': "Ezoncs Beauty Salon Amsterdam - About us: We provide exceptional beauty services.",
        '2': "Ezoncs Beauty Salon Amsterdam - Prices: Visit our website for detailed pricing information: https://ezoncs-beauty-amsterdam.com/prices",
        '3': "Ezoncs Beauty Salon Amsterdam - Online booking: You can book an appointment online at our website: https://ezoncs-beauty-amsterdam.com/book",
        '4': "Ezoncs Beauty Salon Amsterdam - Cancel appointment: Please contact us to cancel your appointment: https://ezoncs-beauty-amsterdam.com/contact"
    },
    20: {
        '1': "Ezoncs Utrecht - About us: We provide exceptional beauty services.",
        '2': "Ezoncs Utrecht - Prices: Visit our website for detailed pricing information: https://ezoncs-utrecht.com/prices",
        '3': "Ezoncs Utrecht - Online booking: You can book an appointment online at our website: https://ezoncs-utrecht.com/book",
        '4': "Ezoncs Utrecht - Cancel appointment: Please contact us to cancel your appointment: https://ezoncs-utrecht.com/contact"
    },
    21: {
        '1': "Evolve Rotterdam - About us: We provide exceptional beauty services.",
        '2': "Evolve Rotterdam - Prices: Visit our website for detailed pricing information: https://evolve-rotterdam.com/prices",
        '3': "Evolve Rotterdam - Online booking: You can book an appointment online at our website: https://evolve-rotterdam.com/book",
        '4': "Evolve Rotterdam - Cancel appointment: Please contact us to cancel your appointment: https://evolve-rotterdam.com/contact"
    }
}

DEFAULT_RESPONSES = {
    '1': "ℹ️ About us: We provide exceptional beauty services.",
    '2': "💲 Prices: Visit our website for detailed pricing information.",
    '3': "📅 Online booking: You can book an appointment online at our website.",
    '4': "❌ Cancel appointment: Please contact us to cancel your appointment."
}

COMMON_RESPONSES = {
    'hello': ["Hello! How can I assist you today?", "Hi there! How can I help you?", "Hey! What can I do for you?"],
    'hi': ["Hello! How can I assist you today?", "Hi there! How can I help you?", "Hey! What can I do for you?"],
    'bye': ["Goodbye! Have a great day!", "See you later!", "Bye! Take care!"],
    'thank you': ["You're welcome!", "Happy to help!", "No problem at all!"],
    'thanks': ["You're welcome!", "Happy to help!", "No problem at all!"],
    'how are you': ["I'm just a bot, but I'm here to help you!", "I'm doing great! How about you?", "I'm here and ready to assist you!"]
}

# Session management functions
def get_session_data(session_id):
    if not hasattr(get_session_data, 'sessions'):
        get_session_data.sessions = {}
    return get_session_data.sessions.setdefault(session_id, {})

def save_session_data(session_id, data):
    get_session_data.sessions[session_id] = data

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_company_details(company_id, option_id, date=None, email=None):
    if option_id == '4':
        url = 'https://test.yourbookingplatform.com/Appointment/GetAppointmentsWRTToDateAndCustomer'
        data = {
            'date': date,
            'email': email,
            'company_id': company_id
        }
    else:
        url = 'https://test.yourbookingplatform.com/Appointment/GetDataOfTBP'
        data = {
            'company_id': company_id,
            'option_id': option_id
        }

    try:
        logging.debug(f"Sending POST request to {url} with data: {data}")
        response = requests.post(url, json=data, proxies={"http": None, "https": None})
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        response_json = response.json()
        logging.debug(f"Received response: {response_json}")
        return response_json
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error occurred: {e}")
    return {"error": "Unable to fetch data at this time. Please try again later."}

def generate_smart_response(message):
    # Basic pattern matching for smart responses
    if re.search(r'\bprice(?:s)?\b', message):
        return "Our prices vary depending on the service. You can visit our website for detailed pricing information or let me know which specific service you’re interested in."
    elif re.search(r'\bbook(?:ing)?|appointment\b', message):
        return "You can book an appointment online through our website. Would you like me to guide you through the process?"
    else:
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').strip().lower()
    from_number = request.values.get('From', '')
    session_id = from_number
    session_data = get_session_data(session_id)
    response = MessagingResponse()
    msg = response.message()

    logging.info(f"Incoming message: {incoming_msg}")

    # Handle smart responses
    smart_response = generate_smart_response(incoming_msg)
    if smart_response:
        msg.body(smart_response)
        return str(response)

    # Check if the message matches any common response keywords
    for keyword, responses in COMMON_RESPONSES.items():
        if keyword in incoming_msg:
            msg.body(random.choice(responses))
            return str(response)

    # Main menu logic
    if incoming_msg in ['menu', 'start', 'main menu']:
        msg.body(WELCOME_MENU)
        session_data.clear()  # Clear the session to start fresh
        save_session_data(session_id, session_data)
        return str(response)

    if not session_data:
        # User selects a company
        if incoming_msg in COMPANY_DETAILS:
            session_data['company_id'] = COMPANY_DETAILS[incoming_msg]['id']
            session_data['company_name'] = COMPANY_DETAILS[incoming_msg]['name']
            msg.body(COMPANY_MENUS[incoming_msg])
            save_session_data(session_id, session_data)
        else:
            msg.body("Invalid option. Please select a valid company number or type 'menu' to see the options again.")
        return str(response)

    if 'company_id' in session_data:
        company_id = session_data['company_id']
        company_menu = COMPANY_MENUS.get(str(company_id), WELCOME_MENU)
        if incoming_msg == '🔙':
            msg.body(WELCOME_MENU)
            session_data.clear()
            save_session_data(session_id, session_data)
            return str(response)

        if incoming_msg in ['1', '2', '3', '4']:
            response_data = COMPANY_DATA[company_id].get(incoming_msg, "Sorry, I couldn't find that information.")
            msg.body(response_data)
        else:
            msg.body(f"Invalid option. {company_menu}")
        return str(response)

    # If no valid input was recognized, guide the user back to the main menu
    msg.body("I didn't understand that. Please type 'menu' to see the options.")
    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
