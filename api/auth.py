# File: api/auth.py

from requests.auth import HTTPBasicAuth
from utils.config import API_LOGIN, API_PASSWORD

AUTH = HTTPBasicAuth(API_LOGIN, API_PASSWORD)
