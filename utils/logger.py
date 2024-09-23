# File: utils/logger.py

import logging

def setup_logger():
    """
    Konfiguruje logger do zapisywania logów w pliku 'app.log'.
    """
    logging.basicConfig(
        filename='app.log',
        filemode='a',
        format='%(asctime)s:%(levelname)s:%(message)s',
        level=logging.DEBUG
    )
