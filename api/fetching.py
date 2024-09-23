# File: api/fetching.py

import math
import requests
import pandas as pd
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from api.auth import AUTH
from utils.config import BASE_URL

MAX_WORKERS = 10  # Maksymalna liczba równoległych wątków

def get_total_pages(endpoint, params):
    """
    Fetch the total number of pages for a given endpoint.
    """
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, auth=AUTH, params=params)
        if response.status_code != 200:
            logging.error(f"Błąd API ({endpoint}): {response.status_code}, {response.text}")
            raise Exception(f"Błąd API ({endpoint}): {response.status_code}, {response.text}")
        data = response.json()
        total_size = data.get('totalSize', 0)
        limit = params.get('limit', 100)
        num_pages = math.ceil(total_size / limit)
        return num_pages
    except Exception as e:
        logging.error(f"Błąd podczas pobierania liczby stron z API ({endpoint}): {e}")
        logging.error(traceback.format_exc())
        raise

def fetch_page(endpoint, params, page_number):
    """
    Fetch a single page of data from the API.
    """
    try:
        url = f"{BASE_URL}{endpoint}"
        params_copy = params.copy()
        params_copy['start'] = (page_number - 1) * params_copy['limit']
        response = requests.get(url, auth=AUTH, params=params_copy)
        if response.status_code != 200:
            logging.error(f"Błąd API ({endpoint}) na stronie {page_number}: {response.status_code}, {response.text}")
            raise Exception(f"Błąd API ({endpoint}) na stronie {page_number}: {response.status_code}, {response.text}")
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        logging.error(f"Błąd podczas pobierania strony {page_number} z API ({endpoint}): {e}")
        logging.error(traceback.format_exc())
        raise

def fetch_endpoint_data(endpoint, params, progress_callback):
    """
    Fetch all data from a specific API endpoint with given parameters using concurrent requests.
    """
    try:
        # Fetch the first page to get total pages
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, auth=AUTH, params=params)
        if response.status_code != 200:
            logging.error(f"Błąd API ({endpoint}): {response.status_code}, {response.text}")
            raise Exception(f"Błąd API ({endpoint}): {response.status_code}, {response.text}")
        data = response.json()
        all_data = data.get('data', [])

        total_size = data.get('totalSize', 0)
        limit = params.get('limit', 100)
        num_pages = math.ceil(total_size / limit)

        progress_callback('start', endpoint, num_pages)

        # Add progress update for the first page
        progress_callback('progress', endpoint)

        if num_pages > 1:
            # Prepare parameters for additional pages
            pages = list(range(2, num_pages + 1))

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Submit all page fetch tasks
                future_to_page = {executor.submit(fetch_page, endpoint, params, page): page for page in pages}

                for future in as_completed(future_to_page):
                    page = future_to_page[future]
                    try:
                        page_data = future.result()
                        all_data.extend(page_data)
                        progress_callback('progress', endpoint)
                    except Exception as e:
                        logging.error(f"Błąd podczas przetwarzania strony {page} z API ({endpoint}): {e}")
                        progress_callback('error', str(e))
                        raise

        progress_callback('complete', endpoint)
        df = pd.DataFrame(all_data)

        # Debugowanie surowych danych
        logging.debug(f"Surowe dane z endpointu '{endpoint}':")
        logging.debug(df.head())

        # Konwersja kolumny 'entryDate' do typu datetime, jeśli istnieje
        if 'entryDate' in df.columns:
            df['entryDate'] = pd.to_datetime(df['entryDate'], errors='coerce')
        elif 'EntryDate' in df.columns:
            df['EntryDate'] = pd.to_datetime(df['EntryDate'], errors='coerce')
            df.rename(columns={'EntryDate': 'entryDate'}, inplace=True)
            logging.info("Kolumna 'EntryDate' została przemianowana na 'entryDate'.")
        else:
            logging.error(f"Brak kolumny 'entryDate' w danych z endpointu '{endpoint}'.")
            raise KeyError("'entryDate'")

        return df
    except Exception as e:
        logging.error(f"Błąd podczas pobierania danych z API ({endpoint}): {e}")
        logging.error(traceback.format_exc())
        progress_callback('error', str(e))
        raise
