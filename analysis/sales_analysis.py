# File: analysis/sales_analysis.py

import pandas as pd
import logging

def daily_sales_report(df_transactions, report_date):
    """
    Generuje raport sprzedaży dla danego dnia.
    """
    try:
        # Upewnij się, że 'entryDate' jest typu datetime
        if df_transactions['entryDate'].dtype != 'datetime64[ns]':
            df_transactions['entryDate'] = pd.to_datetime(df_transactions['entryDate'], errors='coerce')
        
        # Filtrowanie transakcji dla danego dnia
        daily_transactions = df_transactions[
            (df_transactions['entryDate'].notna()) &
            (df_transactions['entryDate'].dt.date == report_date)
        ]
        
        if daily_transactions.empty:
            logging.info(f"Brak transakcji w dniu {report_date}.")
            return {
                'Date': report_date,
                'Total Sales': 0,
                'Total Transactions': 0
            }
        
        total_sales = daily_transactions['amount'].sum()
        total_transactions = daily_transactions['transaction_id'].count()
        
        logging.info(f"Raport sprzedaży dla dnia {report_date}: Sprzedaż całkowita={total_sales}, Transakcje={total_transactions}")
        
        return {
            'Date': report_date,
            'Total Sales': total_sales,
            'Total Transactions': total_transactions
        }
    except Exception as e:
        logging.error(f"Błąd podczas generowania raportu sprzedaży dla dnia {report_date}: {e}")
        return None

def sales_report_range(df_transactions, start_date, end_date):
    """
    Generuje raport sprzedaży dla zakresu dat.
    """
    try:
        # Upewnij się, że 'entryDate' jest typu datetime
        if df_transactions['entryDate'].dtype != 'datetime64[ns]':
            df_transactions['entryDate'] = pd.to_datetime(df_transactions['entryDate'], errors='coerce')
        
        # Filtrowanie transakcji dla zakresu dat
        range_transactions = df_transactions[
            (df_transactions['entryDate'].notna()) &
            (df_transactions['entryDate'].dt.date >= start_date) &
            (df_transactions['entryDate'].dt.date <= end_date)
        ]
        
        if range_transactions.empty:
            logging.info(f"Brak transakcji w zakresie dat {start_date} - {end_date}.")
            return {
                'Start Date': start_date,
                'End Date': end_date,
                'Total Sales': 0,
                'Total Transactions': 0
            }
        
        total_sales = range_transactions['amount'].sum()
        total_transactions = range_transactions['transaction_id'].count()
        
        logging.info(f"Raport sprzedaży dla zakresu dat {start_date} - {end_date}: Sprzedaż całkowita={total_sales}, Transakcje={total_transactions}")
        
        return {
            'Start Date': start_date,
            'End Date': end_date,
            'Total Sales': total_sales,
            'Total Transactions': total_transactions
        }
    except Exception as e:
        logging.error(f"Błąd podczas generowania raportu sprzedaży dla zakresu dat {start_date} - {end_date}: {e}")
        return None
