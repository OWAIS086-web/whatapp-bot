import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

COMPANY_ID = 10
OPTION_ID = 3
URL = 'https://test.yourbookingplatform.com/Appointment/GetDataOfTBP'

def test_connection():
    data = {
        'company_id': COMPANY_ID,
        'option_id': OPTION_ID
    }
    try:
        response = requests.post(URL, json=data)
        response.raise_for_status()
        response_json = response.json()
        logging.info(f"API response status: {response.status_code}, response data: {response_json}")
        return response_json
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        logging.error(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logging.error(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred: {req_err}")

if __name__ == '__main__':
    test_connection()
