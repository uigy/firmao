# File: utils/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define API credentials and base URL
API_LOGIN = os.getenv('API_LOGIN')
API_PASSWORD = os.getenv('API_PASSWORD')

BASE_URL = 'https://system.firmao.pl/klifenergykielce/svc/v1/'
