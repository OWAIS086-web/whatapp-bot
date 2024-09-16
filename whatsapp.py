from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import logging
import random
import re
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime

# Configure logging
logging.basicConfig(filename='log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    "Hello 👋! Welcome to our service. How can I assist you today?\n\n"
    "Please select the company you want to interact with:\n"
    "1️⃣ Ezoncs Beauty Salon Den Haag\n"
    "2️⃣ Ezoncs Beauty Salon Rotterdam\n"
    "3️⃣ Evolve Clinic Den Haag\n"
    "4️⃣ Ezoncs Beauty Salon Amsterdam\n"
    "5️⃣ Ezoncs Utrecht\n"
    "6️⃣ Evolve Rotterdam\n\n"
    "🆘 Type 'Help' for assistance."
)

COMPANY_MENUS = {key: (
    f"{COMPANY_DETAILS[key]['name']} Menu:\n"
    "1️⃣ About us 🏠\n"
    "2️⃣ Prices 💲\n"
    "3️⃣ Online booking 📅\n"
    "4️⃣ Cancel appointment ❌\n"
    "🔙 Back to main menu"
) for key in COMPANY_DETAILS.keys()}

DEFAULT_RESPONSES = {
    '1': "ℹ️ **About us**: We provide exceptional beauty services. 🌟 Feel free to ask more!",
    '2': "💲 **Prices**: Visit our website for detailed pricing information. 🖥️ Let me know if you need specifics!",
    '3': "📅 **Online booking**: You can book an appointment online at our website. 📲 Would you like assistance with booking?",
    '4': "❌ **Cancel appointment**: Please contact us directly to cancel your appointment. 📞"
}

COMMON_RESPONSES = {
    'hello': ["Hello! How can I assist you today? 😊", "Hi there! How can I help you? 👋", "Hey! What can I do for you? 🤔"],
    'hi': ["Hello! How can I assist you today? 😊", "Hi there! How can I help you? 👋", "Hey! What can I do for you? 🤔"],
    'thank you': ["You're welcome! 😊", "Happy to help! 😃", "No problem at all! 👍"],
    'thanks': ["You're welcome! 😊", "Happy to help! 😃", "No problem at all! 👍"],
    'how are you': ["I'm just a bot, but I'm here to help you! 🤖", "I'm doing great! How about you? 😄", "I'm here and ready to assist you! 😊"],
    'help': ["Here’s how I can assist you:\n"
             "1️⃣ Type 'menu' or 'start' to see the main menu.\n"
             "2️⃣ Select a company to see their menu.\n"
             "3️⃣ Choose an option to get more information.\n"
             "4️⃣ Type 'Help' to see this message again.\n"
             "5️⃣ Type 'Bye' to end the chat.\n\n"
             "If you have specific questions, just ask! 😄"],
    'feedback': ["We’d love to hear your feedback! 📝 Please let us know how we did."]
}

FEEDBACK_RESPONSES = [
    "We’d love to hear your feedback! 📝 Please let us know how we did.",
    "Your feedback is important to us! 🗣️ Please share your thoughts.",
    "Help us improve by providing your feedback! 🙌"
]

FAQ_RESPONSES = {
    'working hours': "🕒 Our working hours are from 9 AM to 6 PM, Monday to Friday.",
    'location': "📍 We are located at [Insert Address Here].",
    'contact': "📞 You can reach us at [Insert Phone Number Here] or email us at [Insert Email Here].",
    'services': "💇 We offer a variety of beauty services including haircuts, facials, and more. Let us know what you need!"
}

DAILY_TIPS = [
    "💡 Tip: Drink plenty of water to stay hydrated and keep your skin glowing!",
    "💡 Tip: Regular exercise can help maintain your overall health and well-being.",
    "💡 Tip: Always remove your makeup before going to bed to prevent skin issues."
]

PREFERENCES = {
    '1': 'Receive daily tips',
    '2': 'Receive appointment reminders',
    '3': 'Receive promotional offers'
}

# User session management
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
        response.raise_for_status()
        response_json = response.json()
        logging.debug(f"Received response: {response_json}")
        return response_json
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error occurred: {e}")
    return {"error": "Unable to fetch data at this time. Please try again later."}

def generate_smart_response(message):
    if re.search(r'\bprice(?:s)?\b', message):
        return "💲 Our prices vary depending on the service. You can visit our website for detailed pricing information or let me know which specific service you’re interested in. 🖥️"
    elif re.search(r'\bbook(?:ing)?|appointment\b', message):
        return "📅 You can book an appointment online through our website. Would you like me to guide you through the process? 📝"
    else:
        return None

def get_daily_tip():
    return random.choice(DAILY_TIPS)

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').strip().lower()
    from_number = request.values.get('From', '')
    session_id = from_number
    session_data = get_session_data(session_id)
    response = MessagingResponse()
    msg = response.message()

    logging.info(f"Incoming message: {incoming_msg}")

    # Handle user preferences
    if incoming_msg.startswith('preferences'):
        if 'preferences' in session_data:
            preferences = session_data['preferences']
            msg.body(f"Your current preferences are: {', '.join(PREFERENCES[p] for p in preferences)}")
        else:
            msg.body("You haven't set any preferences yet. Type 'set preferences' to choose your preferences.")
        return str(response)

    if incoming_msg == 'set preferences':
        msg.body("Please select your preferences by typing the corresponding number:\n"
                 "1️⃣ Receive daily tips\n"
                 "2️⃣ Receive appointment reminders\n"
                 "3️⃣ Receive promotional offers")
        session_data['awaiting_preference_response'] = True
        save_session_data(session_id, session_data)
        return str(response)

    if 'awaiting_preference_response' in session_data:
        if incoming_msg in PREFERENCES:
            preferences = session_data.get('preferences', set())
            preferences.add(incoming_msg)
            session_data['preferences'] = preferences
            msg.body(f"Preference '{PREFERENCES[incoming_msg]}' added. Type 'preferences' to see your current preferences or 'set preferences' to add more.")
            session_data.pop('awaiting_preference_response', None)
            save_session_data(session_id, session_data)
        else:
            msg.body("❗ Invalid preference option. Please choose a valid option or type 'set preferences' to try again.")
        return str(response)

    # Handle FAQ responses
    if incoming_msg in FAQ_RESPONSES:
        msg.body(FAQ_RESPONSES[incoming_msg])
        return str(response)

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

    if incoming_msg == 'help':
        msg.body(COMMON_RESPONSES['help'][0])
        return str(response)

    if incoming_msg == 'feedback':
        msg.body(random.choice(FEEDBACK_RESPONSES))
        return str(response)

    if incoming_msg == 'poll':
        # Provide poll options here
        msg.body("🗳️ **Poll**: What feature would you like to see next?\n1️⃣ New Services\n2️⃣ Special Offers\n3️⃣ Loyalty Programs")
        session_data['awaiting_poll_response'] = True
        save_session_data(session_id, session_data)
        return str(response)

    if incoming_msg == 'reminder':
        # Provide reminder options here
        msg.body("🔔 **Reminder**: Would you like to set a reminder for your upcoming appointments?\n1️⃣ Yes\n2️⃣ No")
        session_data['awaiting_reminder_response'] = True
        save_session_data(session_id, session_data)
        return str(response)

    if incoming_msg == 'bye':
        msg.body("Goodbye! Before you go, would you like to:\n1️⃣ Provide Feedback\n2️⃣ Participate in a Poll\n3️⃣ Set a Reminder\n\nReply with the number of your choice or 'No' to exit.")
        session_data['awaiting_post_exit_response'] = True
        save_session_data(session_id, session_data)
        return str(response)

    # Handle feedback, poll, and reminder choices after "bye"
    if 'awaiting_post_exit_response' in session_data:
        if incoming_msg == '1':
            msg.body(random.choice(FEEDBACK_RESPONSES))
            session_data.pop('awaiting_post_exit_response', None)
            save_session_data(session_id, session_data)
            return str(response)
        elif incoming_msg == '2':
            msg.body("🗳️ **Poll**: What feature would you like to see next?\n1️⃣ New Services\n2️⃣ Special Offers\n3️⃣ Loyalty Programs")
            session_data.pop('awaiting_post_exit_response', None)
            save_session_data(session_id, session_data)
            return str(response)
        elif incoming_msg == '3':
            msg.body("🔔 **Reminder**: Would you like to set a reminder for your upcoming appointments?\n1️⃣ Yes\n2️⃣ No")
            session_data.pop('awaiting_post_exit_response', None)
            save_session_data(session_id, session_data)
            return str(response)
        elif incoming_msg == 'no':
            msg.body("Thank you for using our service. Have a great day! 🌟")
            session_data.clear()
            save_session_data(session_id, session_data)
            return str(response)

    # Handle reminder responses
    if 'awaiting_reminder_response' in session_data:
        if incoming_msg == '1':
            msg.body("🔔 **Reminder**: You will receive reminders for your upcoming appointments.")
            session_data['preferences'] = session_data.get('preferences', set()) | {'2'}
            session_data.pop('awaiting_reminder_response', None)
            save_session_data(session_id, session_data)
            return str(response)
        elif incoming_msg == '2':
            msg.body("You will not receive appointment reminders.")
            session_data['preferences'] = session_data.get('preferences', set()) - {'2'}
            session_data.pop('awaiting_reminder_response', None)
            save_session_data(session_id, session_data)
            return str(response)

    # Handle poll responses
    if 'awaiting_poll_response' in session_data:
        # Handle poll options here
        msg.body("Thank you for participating in the poll!")
        session_data.pop('awaiting_poll_response', None)
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
            msg.body("❗ Invalid option. Please select a valid company number or type 'menu' to see the options again. 🔄")
        return str(response)

    if 'company_id' in session_data:
        company_id = session_data['company_id']
        if incoming_msg == '🔙':
            msg.body(WELCOME_MENU)
            session_data.clear()  # Clear session to start fresh
            save_session_data(session_id, session_data)
            return str(response)

        if incoming_msg == '0':
            # Return to company-specific menu
            company_menu = COMPANY_MENUS.get(next((key for key, value in COMPANY_DETAILS.items() if value['id'] == company_id), None))
            if company_menu:
                msg.body(company_menu)
            else:
                msg.body("⚠️ Error: Company menu not found. Please select your company again. 🔄")
            return str(response)

        if incoming_msg in ['1', '2', '3', '4']:
            response_data = fetch_company_details(company_id, incoming_msg)
            if response_data and 'error' not in response_data:
                if incoming_msg == '1':
                    msg.body(DEFAULT_RESPONSES['1'])
                elif incoming_msg == '2':
                    msg.body(DEFAULT_RESPONSES['2'])
                elif incoming_msg == '3':
                    msg.body(DEFAULT_RESPONSES['3'])
                elif incoming_msg == '4':
                    msg.body(DEFAULT_RESPONSES['4'])
            else:
                msg.body("⚠️ Error fetching details. Please try again later. 🔄")
            return str(response)

    msg.body("❓ Sorry, I didn’t understand that. Type 'Help' for assistance. 🤔")
    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
