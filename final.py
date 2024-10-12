from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import logging
import random
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from urllib.parse import quote  # Import for URL encoding

# Configure logging
logging.basicConfig(filename='chatbot_den_haag.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Constants
COMPANY_NAME = 'Ezoncs Beauty Salon Den Haag 💇‍♀️✨'
COMPANY_ID = 10

# Menu options
OPTIONS = {
    '1': "About Us 🏠",
    '2': "Prices 💲",
    '3': "Online Booking 📅",
    '4': "Cancel Appointment ❌",
    '0': "Go Back to Main Menu 🔙"
}

# Predefined responses for common phrases
COMMON_RESPONSES = {
    'hello': [
        "Hello! How can I assist you today? 😊\ntype 'menu' to see the options.",
        "Hi there! How can I help you? 🤔\ntype 'menu' to see the options.",
        "Hey! What can I do for you? 🙌\ntype 'menu' to see the options.",
        "Greetings! How may I be of service? 👋\ntype 'menu' to see the options.",
        "Hello! What can I do for you today? 😃\ntype 'menu' to see the options."
    ],
    'bye': [
        "Goodbye! Have a great day! 👋\ntype 'menu' to see the options.",
        "See you later! 👋\ntype 'menu' to see the options.",
        "Bye! Take care! ✨\ntype 'menu' to see the options.",
        "Farewell! Wishing you the best! 🌟\ntype 'menu' to see the options.",
        "Catch you later! 😊\ntype 'menu' to see the options."
    ],
    'thanks': [
        "You're welcome! 😃\ntype 'menu' to see the options.",
        "Happy to help! 😊\ntype 'menu' to see the options.",
        "No problem at all! 👍\ntype 'menu' to see the options.",
        "You're welcome! If you need anything else, just ask! 🙏\ntype 'menu' to see the options.",
        "Glad I could assist! 😄\ntype 'menu' to see the options."
    ]
}

# Fetch details from external API with retry mechanism
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_details(option_id, date=None, email=None):
    if option_id == '4' and date and email:
        url = 'https://test.yourbookingplatform.com/Appointment/GetAppointmentsWRTToDateAndCustomer'
        params = {'date': date, 'email': email, 'company_id': COMPANY_ID}
    else:
        url = f'https://test.yourbookingplatform.com/Appointment/GetDataOfTBP?company_id={COMPANY_ID}&option_id={option_id}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error occurred: {e}")
        return None

# Main route for handling incoming messages
@app.route('/sms', methods=['POST'])
def sms_reply():
    incoming_msg = request.form.get('Body', '').strip().lower()
    from_number = request.form.get('From')
    response = MessagingResponse()
    msg = response.message()

    logging.info(f"Incoming message: {incoming_msg} from {from_number}")

    # Handle predefined common responses
    if incoming_msg in COMMON_RESPONSES:
        common_response = random.choice(COMMON_RESPONSES[incoming_msg])
        msg.body(common_response)

    # Display menu
    elif incoming_msg == 'menu' or incoming_msg == '0':  # Show menu for 'menu' or '0'
        menu_response = (
            "Welcome to Ezoncs Beauty Salon Den Haag 💇‍♀️✨\n"
            "Please select an option from the menu below:\n\n"
            "1️⃣: About Us 🏠\n"
            "2️⃣: Prices 💲\n"
            "3️⃣: Online Booking 📅\n"
            "4️⃣: Cancel Appointment ❌\n"
            "0️⃣: Go Back to Main Menu 🔙"
        )
        msg.body(menu_response)

    # Handle specific menu options
    elif incoming_msg in OPTIONS:
        option_id = incoming_msg
        if option_id == '4':
            msg.body("Please provide the date (YYYY-MM-DD) and email for your appointment.\nExample: 2024-10-12 example@mail.com")
            app.config['pending_option'] = '4'
        else:
            details = fetch_details(option_id)
            if details and details.get('success'):
                if option_id == '1':  # About Us
                    # Encode the URL to replace spaces with %20
                    company_link = quote(details.get('companyLink', 'Details unavailable.'), safe='/:')
                    about_us_response = f"{COMPANY_NAME} - About us 🏠:\n{company_link}\nClick here: {company_link}\n\nPress 0️⃣ to go back."
                    msg.body(about_us_response)
                elif option_id == '2':  # Prices
                    prices = details.get('prices', [])
                    prices_response = f"{COMPANY_NAME} - Prices 💲:\n\n"
                    for price in prices:
                        prices_response += f"💇‍♀️ *{price['ServiceName']}* ({price['ServiceCategory']}): _{price['Price']}_\n"
                    msg.body(prices_response + "\n\nPress 0️⃣ to go back.")
                elif option_id == '3':  # Online Booking
                    booking_link = quote(details.get('booking_link', 'URL not available'), safe='/:')
                    booking_response = f"{COMPANY_NAME} - Online booking 📅:\nClick here to book: {booking_link}\n\nPress 0️⃣ to go back."
                    msg.body(booking_response)
            else:
                msg.body(f"{COMPANY_NAME} - Details are currently unavailable.\n\nPress 0️⃣ to go back.")

    # Handle appointment cancellation (Pending option 4)
    elif app.config.get('pending_option') == '4' and ' ' in incoming_msg:
        date, email = incoming_msg.split(' ', 1)
        details = fetch_details('4', date=date, email=email)
        if details and details.get('success'):
            appointments = details.get('listofAppointments', [])
            if appointments:
                appointments_response = f"Appointments for {email} on {date}:\n"
                for appt in appointments:
                    appointments_response += f"ID: {appt['AppointmentID']}, Time: {appt['Time']}\n"
                appointments_response += "\nPlease provide the AppointmentID you want to cancel."
                msg.body(appointments_response)
                app.config['pending_option'] = 'cancel_appointment'
            else:
                msg.body("No appointments found. Please try again with a different date or email.\n\nPress 0️⃣ to go back to the main menu 🔙.")
        else:
            msg.body("Invalid format. Please provide the date and email in the format 'YYYY-MM-DD email'.")
    elif app.config.get('pending_option') == 'cancel_appointment':
        try:
            appointment_id = int(incoming_msg)
            url = 'https://test.yourbookingplatform.com/Appointment/CancelAppointment'
            params = {'AppointmentID': appointment_id}
            response = requests.get(url, params=params)
            response.raise_for_status()
            if response.json().get('success'):
                msg.body("Appointment has been successfully cancelled.\n\nPress 0️⃣ to go back to the main menu 🔙.")
            else:
                msg.body("Failed to cancel the appointment. Please try again later.\n\nPress 0️⃣ to go back to the main menu 🔙.")
        except ValueError:
            msg.body("Invalid AppointmentID. Please provide a valid number.")
    else:
        # Invalid selection
        msg.body(" Welcome to Ezoncs Beauty Salon Den Haag 💇‍♀️✨\n"
            "Please select an option from the menu below:\n\n"
            "1️⃣: About Us 🏠\n"
            "2️⃣: Prices 💲\n"
            "3️⃣: Online Booking 📅\n"
            "4️⃣: Cancel Appointment ❌\n"
            "0️⃣: Go Back to Main Menu 🔙")

    return str(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")
