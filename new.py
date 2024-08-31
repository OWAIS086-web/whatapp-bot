import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# API URLs
BASE_URL = "https://test.yourbookingplatform.com"
PRICING_API = f"{BASE_URL}/Pricing/GetPrice"
APPOINTMENT_API = f"{BASE_URL}/Appointment/Create"
CANCEL_APPOINTMENT_API = f"{BASE_URL}/Appointment/Cancel"

# Example data
pricing_payload = {
    'service_id': 123,
    'company_id': 1,
}

appointment_payload = {
    'customer_id': 456,
    'company_id': 1,
    'service_id': 123,
    'appointment_time': '2024-09-01T10:00:00',
}

cancel_appointment_payload = {
    'appointment_id': 789,
    'reason': 'User requested cancellation',
}

def test_pricing_api():
    try:
        response = requests.post(PRICING_API, json=pricing_payload)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Pricing API Response: {data}")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")

def test_appointment_api():
    try:
        response = requests.post(APPOINTMENT_API, json=appointment_payload)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Appointment API Response: {data}")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")

def test_cancel_appointment_api():
    try:
        response = requests.post(CANCEL_APPOINTMENT_API, json=cancel_appointment_payload)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Cancel Appointment API Response: {data}")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")

if __name__ == "__main__":
    logging.info("Testing Pricing API...")
    test_pricing_api()

    logging.info("Testing Appointment API...")
    test_appointment_api()

    logging.info("Testing Cancel Appointment API...")
    test_cancel_appointment_api()
