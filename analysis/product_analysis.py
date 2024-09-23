# File: analysis/product_analysis.py

import pandas as pd
import logging

def analyze_product(df_transactions, df_products, product_name):
    """
    Analizuje wybrany produkt i zwraca statystyki sprzedaży.
    """
    try:
        # Znajdowanie produktu po nazwie
        product = df_products[df_products['name'].str.lower() == product_name.lower()]
        if product.empty:
            logging.warning(f"Produkt o nazwie '{product_name}' nie został znaleziony.")
            return None
        
        product_id = product.iloc[0]['id']
        
        # Filtracja transakcji dla danego produktu
        product_transactions = df_transactions[df_transactions['product_id'] == product_id]
        
        if product_transactions.empty:
            logging.info(f"Brak transakcji dla produktu '{product_name}'.")
            return {
                'Product Name': product_name,
                'Total Sales': 0,
                'Total Transactions': 0,
                'Average Sale': 0
            }
        
        total_sales = product_transactions['amount'].sum()
        total_transactions = product_transactions['transaction_id'].count()
        average_sale = product_transactions['amount'].mean()
        
        logging.info(f"Analiza produktu '{product_name}': Sprzedaż całkowita={total_sales}, Transakcje={total_transactions}, Średnia sprzedaż={average_sale:.2f}")
        
        return {
            'Product Name': product_name,
            'Total Sales': total_sales,
            'Total Transactions': total_transactions,
            'Average Sale': round(average_sale, 2)
        }
    except Exception as e:
        logging.error(f"Błąd podczas analizy produktu '{product_name}': {e}")
        return None
