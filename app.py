from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import logging
import random
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# Configure logging
logging.basicConfig(filename='chatbot_den_haag.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

COMPANY_NAME = 'Ezoncs Beauty Salon Den Haag'
COMPANY_ID = 10

OPTIONS = {
    '1': "About us 🏠",
    '2': "Prices 💲",
    '3': "Online booking 📅",
    '4': "Cancel appointment ❌"
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
    ]
}

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_details(option_id, date=None, email=None):
    if option_id == '4':
        url = 'https://test.yourbookingplatform.com/Appointment/GetAppointmentsWRTToDateAndCustomer'
        data = {
            'date': date,
            'email': email,
            'company_id': COMPANY_ID
        }
    else:
        url = 'https://test.yourbookingplatform.com/Appointment/GetDataOfTBP'
        data = {
            'company_id': COMPANY_ID,
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
    return None

@app.route('/sms', methods=['POST'])
def sms_reply():
    incoming_msg = request.form.get('Body', '').strip().lower()
    from_number = request.form.get('From')
    response = MessagingResponse()
    msg = response.message()

    logging.info(f"Incoming message: {incoming_msg} from {from_number}")

    pending_option = app.config.get('pending_option')

    if incoming_msg in COMMON_RESPONSES:
        common_response = random.choice(COMMON_RESPONSES[incoming_msg])
        msg.body(common_response)
        logging.info(f"Responding with common response: {common_response}")
    elif incoming_msg == 'menu':
        menu_response = "The menu is ready for you! Choose an option. 📝 1: About us 🏠, 2: Prices 💲, 3: Online booking 📅, 4: Cancel appointment ❌"
        msg.body(menu_response)
        logging.info(f"Responding with menu response: {menu_response}")
    elif incoming_msg in OPTIONS:
        option_id = incoming_msg
        if option_id == '4':
            msg.body("Please provide the date (YYYY-MM-DD) and email for your appointment.")
            app.config['pending_option'] = '4'
        else:
            details = fetch_details(option_id)
            if details:
                if details.get('success'):
                    if option_id == '1':
                        about_us_response = f"{COMPANY_NAME} - About us 🏠: {details.get('companyLink', 'About us details are currently unavailable. Please try again later.')}\n\nPress 0 to go back to the main menu 🔙."
                        msg.body(about_us_response)
                    elif option_id == '2':
                        prices = details.get('prices', [])
                        if prices:
                            prices_response = f"{COMPANY_NAME} - Prices 💲:\n"
                            for price in prices:
                                prices_response += f"{price['ServiceName']} ({price['ServiceCategory']}): {price['Price']}\n"
                        else:
                            prices_response = f"{COMPANY_NAME} - Prices 💲: Price details are currently unavailable. Please try again later."
                        prices_response += "\nPress 0 to go back to the main menu 🔙."
                        msg.body(prices_response)
                    elif option_id == '3':
                        booking_response = f"{COMPANY_NAME} - Online booking 📅: {details.get('booking_link', 'Online booking details are currently unavailable. Please try again later.')}\n\nPress 0 to go back to the main menu 🔙."
                        msg.body(booking_response)
                    logging.info(f"Responding with details: {msg.body}")
                else:
                    error_response = f"{COMPANY_NAME} - Details are currently unavailable. Please try again later.\n\nPress 0 to go back to the main menu 🔙."
                    msg.body(error_response)
                    logging.info(f"Responding with error details: {error_response}")
            else:
                error_response = f"{COMPANY_NAME} - Details are currently unavailable. Please try again later.\n\nPress 0 to go back to the main menu 🔙."
                msg.body(error_response)
                logging.info(f"Responding with error details: {error_response}")
    elif pending_option == '4':
        if ' ' in incoming_msg:
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
                    msg.body("No appointments found. Please try again with a different date or email.\n\nPress 0 to go back to the main menu 🔙.")
                    app.config['pending_option'] = None
            else:
                msg.body("Failed to fetch appointments. Please try again later.\n\nPress 0 to go back to the main menu 🔙.")
                app.config['pending_option'] = None
        else:
            msg.body("Invalid format. Please provide the date and email in the format 'YYYY-MM-DD email'.")
    elif pending_option == 'cancel_appointment':
        try:
            appointment_id = int(incoming_msg)
            url = 'https://test.yourbookingplatform.com/Appointment/CancelAppointment'
            data = {'AppointmentID': appointment_id}
            try:
                response = requests.post(url, json=data, proxies={"http": None, "https": None})
                response.raise_for_status()
                response_json = response.json()
                if response_json.get('success'):
                    cancel_response = "Appointment has been successfully cancelled."
                    msg.body(cancel_response + "\n\nPress 0 to go back to the main menu 🔙.")
                    logging.info(f"Responding with cancellation success: {cancel_response}")
                else:
                    msg.body("Failed to cancel the appointment. Please try again later.\n\nPress 0 to go back to the main menu 🔙.")
                    logging.error(f"Cancellation failed: {response_json}")
            except requests.exceptions.RequestException as req_err:
                logging.error(f"Request error occurred: {req_err}")
                msg.body("Failed to process your request. Please try again later.\n\nPress 0 to go back to the main menu 🔙.")
        except ValueError:
            msg.body("Invalid AppointmentID. Please provide a valid number.")
    elif pending_option == 'return_menu':
        if incoming_msg == '0':
            main_menu_response = "Returning to main menu. Choose an option. 📝 1: About us 🏠, 2: Prices 💲, 3: Online booking 📅, 4: Cancel appointment ❌"
            msg.body(main_menu_response)
            logging.info(f"{main_menu_response}")
            app.config['pending_option'] = None
        else:
            msg.body("Invalid selection. Please press 0 to go back to the main menu.")
    elif incoming_msg == '0':
        main_menu_response = "Returning to main menu. Choose an option. 📝 1: About us 🏠, 2: Prices 💲, 3: Online booking 📅, 4: Cancel appointment ❌"
        msg.body(main_menu_response)
        logging.info(f"{main_menu_response}")
        app.config['pending_option'] = None
    else:
        invalid_selection_response = "Invalid selection, please try again or type 'menu' to see the options."
        msg.body(invalid_selection_response)
        logging.info(f"Invalid selection, sending default response.")

    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
