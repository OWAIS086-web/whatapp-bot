from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import logging
import random

# Configure logging
logging.basicConfig(filename='chatbot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        '2': "Ezoncs Beauty Salon Den Haag - Prices: Visit our website for detailed pricing information.",
        '3': "Ezoncs Beauty Salon Den Haag - Online booking: You can book an appointment online at our website.",
        '4': "Ezoncs Beauty Salon Den Haag - Cancel appointment: Please contact us to cancel your appointment."
    },
    14: {
        '1': "Ezoncs Beauty Salon Rotterdam - About us: We provide exceptional beauty services.",
        '2': "Ezoncs Beauty Salon Rotterdam - Prices: Visit our website for detailed pricing information.",
        '3': "Ezoncs Beauty Salon Rotterdam - Online booking: You can book an appointment online at our website.",
        '4': "Ezoncs Beauty Salon Rotterdam - Cancel appointment: Please contact us to cancel your appointment."
    },
    17: {
        '1': "Evolve Clinic Den Haag - About us: We provide exceptional beauty services.",
        '2': "Evolve Clinic Den Haag - Prices: Visit our website for detailed pricing information.",
        '3': "Evolve Clinic Den Haag - Online booking: You can book an appointment online at our website.",
        '4': "Evolve Clinic Den Haag - Cancel appointment: Please contact us to cancel your appointment."
    },
    19: {
        '1': "Ezoncs Beauty Salon Amsterdam - About us: We provide exceptional beauty services.",
        '2': "Ezoncs Beauty Salon Amsterdam - Prices: Visit our website for detailed pricing information.",
        '3': "Ezoncs Beauty Salon Amsterdam - Online booking: You can book an appointment online at our website.",
        '4': "Ezoncs Beauty Salon Amsterdam - Cancel appointment: Please contact us to cancel your appointment."
    },
    20: {
        '1': "Ezoncs Utrecht - About us: We provide exceptional beauty services.",
        '2': "Ezoncs Utrecht - Prices: Visit our website for detailed pricing information.",
        '3': "Ezoncs Utrecht - Online booking: You can book an appointment online at our website.",
        '4': "Ezoncs Utrecht - Cancel appointment: Please contact us to cancel your appointment."
    },
    21: {
        '1': "Evolve Rotterdam - About us: We provide exceptional beauty services.",
        '2': "Evolve Rotterdam - Prices: Visit our website for detailed pricing information.",
        '3': "Evolve Rotterdam - Online booking: You can book an appointment online at our website.",
        '4': "Evolve Rotterdam - Cancel appointment: Please contact us to cancel your appointment."
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

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip().lower()
    session_id = request.values.get('WaId', 'default_session')
    logging.info(f"Incoming message: {incoming_msg} from session: {session_id}")

    resp = MessagingResponse()
    msg = resp.message()

    session_data = get_session_data(session_id)
    logging.info(f"Session data: {session_data}")

    if incoming_msg in COMMON_RESPONSES:
        response = random.choice(COMMON_RESPONSES[incoming_msg])
        logging.info(f"Responding with common response: {response}")
        msg.body(response)
    elif incoming_msg == 'main menu':
        session_data.pop('company_selected', None)
        save_session_data(session_id, session_data)
        logging.info("Returning to main menu.")
        msg.body(WELCOME_MENU)
    elif session_data.get('company_selected'):
        handle_company_menu_selection(incoming_msg, session_data, msg)
    else:
        if incoming_msg in COMPANY_DETAILS:
            session_data['company_selected'] = incoming_msg
            save_session_data(session_id, session_data)
            response = COMPANY_MENUS[incoming_msg]
            logging.info(f"Company selected: {incoming_msg}, responding with menu: {response}")
            msg.body(response)
        else:
            logging.info("Invalid company selection, sending welcome menu.")
            msg.body(WELCOME_MENU)

    return str(resp)

def handle_company_menu_selection(incoming_msg, session_data, msg):
    company_selected = session_data['company_selected']
    company_name = COMPANY_DETAILS[company_selected]['name']
    if incoming_msg == 'back':
        response = COMPANY_MENUS[company_selected]
        logging.info(f"Returning to company menu: {response}")
        msg.body(response)
    elif incoming_msg in ['1', '2', '3', '4']:
        option_name = {'1': 'About us', '2': 'Prices', '3': 'Online booking', '4': 'Cancel appointment'}[incoming_msg]
        response = fetch_company_details(COMPANY_DETAILS[company_selected]['id'], incoming_msg, company_name, option_name)
        logging.info(f"Responding with company response: {response}")
        msg.body(response)
    else:
        response = "Invalid option. Please use the menu options provided:\n" + COMPANY_MENUS[company_selected]
        logging.info("Invalid menu selection, responding with menu.")
        msg.body(response)

def fetch_company_details(company_id, option, company_name, option_name):
    message = COMPANY_DATA[company_id].get(option, DEFAULT_RESPONSES[option])
    return f"{company_name} - {option_name}: {message}"

@app.route('/company_details', methods=['POST'])
def company_details():
    content = request.json
    company_id = content.get('id')
    option = content.get('option')
    detail = content.get('detail')

    if company_id in COMPANY_DATA and option in ['1', '2', '3', '4']:
        COMPANY_DATA[company_id][option] = detail
        response = {"message": f"Detail updated for company ID {company_id}, option {option}."}
    else:
        response = {"message": "Invalid company ID or option."}

    return jsonify(response)

def get_session_data(session_id):
    if not hasattr(get_session_data, 'sessions'):
        get_session_data.sessions = {}
    return get_session_data.sessions.setdefault(session_id, {})

def save_session_data(session_id, data):
    get_session_data.sessions[session_id] = data

if __name__ == '__main__':
    app.run(debug=True)

#curl -X POST -d "Body=hello" https://awais086086.pythonanywhere.com/sms
""""  https://test.yourbookingplatform.com/Appointment/GetAppointmentsWRTToDateAndCustomer
string date,string email,int company_id """