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

def fetch_endpoint_data(endpoint, params, progress_callback=None):
    """
    Fetch all data from the given API endpoint.
    
    endpoint: str
        The API endpoint name.
    params: dict
        Query parameters.
    progress_callback: callable, optional
        Function to update progress, accepts variable arguments.
    """
    try:
        num_pages = get_total_pages(endpoint, params)

        # Call progress_callback with 'start'
        if progress_callback:
            progress_callback('start', endpoint, num_pages)

        results = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_page = {executor.submit(fetch_page, endpoint, params, i): i for i in range(1, num_pages + 1)}
            for count, future in enumerate(as_completed(future_to_page), start=1):
                try:
                    page_data = future.result()
                    results.extend(page_data)

                    # Call progress_callback with 'progress'
                    if progress_callback:
                        progress_callback('progress', endpoint)

                except Exception as e:
                    logging.error(f"Błąd podczas pobierania strony {future_to_page[future]} z API ({endpoint}): {e}")
                    logging.error(traceback.format_exc())
                    # Call progress_callback with 'error'
                    if progress_callback:
                        progress_callback('error', endpoint, str(e))
                    raise  # Re-raise the exception to stop processing

        # Call progress_callback with 'complete'
        if progress_callback:
            progress_callback('complete', endpoint)

        return pd.DataFrame(results)

    except Exception as e:
        logging.error(f"Błąd podczas pobierania danych z API ({endpoint}): {e}")
        logging.error(traceback.format_exc())
        # Call progress_callback with 'error'
        if progress_callback:
            progress_callback('error', endpoint, str(e))
        raise
