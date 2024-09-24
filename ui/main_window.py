# File: ui/main_window.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from ttkthemes import ThemedTk
import threading
import queue
from datetime import datetime, timedelta

from api.fetching import get_total_pages, fetch_endpoint_data
from ui.date_picker import select_date
from utils.logger import setup_logger
from analysis.report_generation import generate_sales_report
from analysis.product_analysis import analyze_product
from analysis.sales_analysis import daily_sales_report, sales_report_range

import pandas as pd
import logging

# Initialize logger
setup_logger()

def debug_dataframe(df, name="DataFrame"):
    """
    Funkcja do wyświetlania struktury i przykładowych danych DataFrame.
    """
    print(f"\n--- Debugging {name} ---")
    print("Struktura DataFrame:")
    print(df.info())
    print("\nPrzykładowe dane:")
    print(df.head())
    print("--- End Debugging ---\n")

class MainWindow:
    def __init__(self, root):
        self.window = root
        self.window.title("Zaawansowane Raportowanie Danych z Firmao")
        self.window.geometry("800x600")  # Zwiększenie rozmiaru okna dla nowych funkcji

        # Create a thread-safe queue for progress updates
        self.progress_queue = queue.Queue()

        # Labels and date entry fields
        self.create_date_fields()

        # Buttons
        self.create_buttons()

        # Progress bar
        self.create_progress_bar()

        # Set default dates
        self.set_default_dates()

        # Initialize dataframes
        self.df_transactions = pd.DataFrame()
        self.df_products = pd.DataFrame()
        self.df_customers = pd.DataFrame()

    def create_date_fields(self):
        # Data początkowa
        start_date_label = ttk.Label(self.window, text="Data początkowa:")
        start_date_label.grid(column=0, row=0, padx=10, pady=10, sticky="w")
        self.start_date_entry = ttk.Entry(self.window, width=20)
        self.start_date_entry.grid(column=1, row=0, padx=10, pady=10, sticky="w")
        ttk.Button(self.window, text="Wybierz", command=lambda: select_date(self.window, self.start_date_entry)).grid(column=2, row=0, padx=5)

        # Data końcowa
        end_date_label = ttk.Label(self.window, text="Data końcowa:")
        end_date_label.grid(column=0, row=1, padx=10, pady=10, sticky="w")
        self.end_date_entry = ttk.Entry(self.window, width=20)
        self.end_date_entry.grid(column=1, row=1, padx=10, pady=10, sticky="w")
        ttk.Button(self.window, text="Wybierz", command=lambda: select_date(self.window, self.end_date_entry)).grid(column=2, row=1, padx=5)

    def create_buttons(self):
        # Pobierz dane
        self.fetch_button = ttk.Button(self.window, text="Pobierz dane", command=self.fetch_data)
        self.fetch_button.grid(column=0, row=2, columnspan=3, pady=10)

        # Analizuj dane
        self.analyze_button = ttk.Button(self.window, text="Analizuj dane", command=self.analyze_data)
        self.analyze_button.grid(column=0, row=3, columnspan=3, pady=10)

        # Generuj Raport
        self.report_button = ttk.Button(self.window, text="Generuj Raport", command=self.generate_report)
        self.report_button.grid(column=0, row=4, columnspan=3, pady=10)

        # Dodane funkcje
        # Generuj Raport Codzienny
        self.daily_report_button = ttk.Button(self.window, text="Generuj Raport Codzienny", command=self.generate_daily_report)
        self.daily_report_button.grid(column=0, row=5, columnspan=3, pady=10)

        # Generuj Raport dla Zakresu Dat
        self.range_report_button = ttk.Button(self.window, text="Generuj Raport dla Zakresu Dat", command=self.generate_range_report)
        self.range_report_button.grid(column=0, row=6, columnspan=3, pady=10)

        # Analizuj Produkt
        self.product_analysis_button = ttk.Button(self.window, text="Analizuj Produkt", command=self.analyze_specific_product)
        self.product_analysis_button.grid(column=0, row=7, columnspan=3, pady=10)

    def create_progress_bar(self):
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.window, variable=self.progress_var, maximum=0, length=700)
        self.progress_bar.grid(column=0, row=8, columnspan=3, padx=10, pady=20)

    def set_default_dates(self):
        today = datetime.today()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

        self.start_date_entry.insert(0, first_day_of_previous_month.strftime('%Y-%m-%d'))
        self.end_date_entry.insert(0, last_day_of_previous_month.strftime('%Y-%m-%d'))

    def fetch_data(self):
        try:
            # Parse the input dates
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()

            # Parse the input dates
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.")
                return

            # Validate date range
            if start_date > end_date:
                messagebox.showerror("Błąd", "Data początkowa nie może być późniejsza niż data końcowa.")
                return

            # Disable the fetch button to prevent multiple clicks
            self.fetch_button.config(state='disabled')
            self.analyze_button.config(state='disabled')
            self.report_button.config(state='disabled')
            self.daily_report_button.config(state='disabled')
            self.range_report_button.config(state='disabled')
            self.product_analysis_button.config(state='disabled')

            # Reset the progress bar
            self.progress_var.set(0)
            self.progress_bar['value'] = 0

            # Start the data fetching in a separate thread
            thread = threading.Thread(target=self.fetch_data_thread, args=(start_date, end_date))
            thread.start()

            # Start checking the queue for progress updates
            self.window.after(100, self.process_queue)

        except Exception as e:
            logging.error(f"Błąd podczas inicjowania pobierania danych: {e}")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas inicjowania pobierania danych: {e}")
            self.fetch_button.config(state='normal')
            self.analyze_button.config(state='normal')
            self.report_button.config(state='normal')
            self.daily_report_button.config(state='normal')
            self.range_report_button.config(state='normal')
            self.product_analysis_button.config(state='normal')

    def fetch_data_thread(self, start_date, end_date):
        """
        Thread function to fetch data and communicate progress via queue.
        """
        logging.debug("Data fetching thread started")
        try:
            # Define endpoints and their parameters
            endpoints = [
                {
                    'name': 'transactions',
                    'params': {
                        'start': 0,
                        'limit': 100,
                        'sort': 'entryDate',
                        'dir': 'ASC',
                        'dateFrom': start_date.strftime('%Y-%m-%d'),
                        'dateTo': end_date.strftime('%Y-%m-%d'),
                        'dataFormat': 'MEDIUM'
                    }
                },
                {
                    'name': 'products',
                    'params': {
                        'start': 0,
                        'limit': 100,
                        'sort': 'name',
                        'dir': 'ASC',
                        'dataFormat': 'MEDIUM'
                    }
                },
                {
                    'name': 'customers',
                    'params': {
                        'start': 0,
                        'limit': 100,
                        'sort': 'name',
                        'dir': 'ASC',
                        'dataFormat': 'MEDIUM'
                    }
                }
            ]

            # Calculate total number of pages across all endpoints
            total_pages = 0
            for endpoint in endpoints:
                num_pages = get_total_pages(endpoint['name'], endpoint['params'])
                total_pages += num_pages

            # Set progress bar maximum
            self.progress_queue.put(('set_maximum', total_pages))
            logging.debug(f"Progress bar maximum set to {total_pages} total pages.")

            # Initialize dataframes
            df_transactions = pd.DataFrame()
            df_products = pd.DataFrame()
            df_customers = pd.DataFrame()

            # Fetch data for each endpoint
            for endpoint in endpoints:
                if endpoint['name'] == 'transactions':
                    df_transactions = fetch_endpoint_data(endpoint['name'], endpoint['params'], self.api_progress_callback)
                elif endpoint['name'] == 'products':
                    df_products = fetch_endpoint_data(endpoint['name'], endpoint['params'], self.api_progress_callback)
                elif endpoint['name'] == 'customers':
                    df_customers = fetch_endpoint_data(endpoint['name'], endpoint['params'], self.api_progress_callback)

            # Finalize progress
            self.progress_queue.put(('done', (df_transactions, df_products, df_customers)))
            logging.debug("Data fetching complete")

            # Debugowanie DataFrame
            debug_dataframe(df_transactions, "df_transactions")
            debug_dataframe(df_products, "df_products")
            debug_dataframe(df_customers, "df_customers")

        except Exception as e:
            self.progress_queue.put(('error', str(e)))
            logging.error(f"Error in data fetching thread: {e}")

    def api_progress_callback(self, progress):
        """
        Callback function to communicate progress from API functions to the main thread.
        """
        self.progress_queue.put(('page_progress', progress))

    def process_queue(self):
        """
        Process messages from the progress_queue and update the progress bar accordingly.
        """
        try:
            while not self.progress_queue.empty():
                message = self.progress_queue.get_nowait()
                logging.debug(f"Processing message: {message}")  # Debug log

                if message[0] == 'set_maximum':
                    total_pages = message[1]
                    self.progress_bar.config(maximum=total_pages)
                    self.progress_var.set(0)
                    logging.debug(f"Progress bar maximum set to {total_pages} total pages.")

                elif message[0] == 'page_progress':
                    self.progress_var.set(self.progress_var.get() + 1)
                    logging.debug(f"Progress updated to {self.progress_var.get()} / {self.progress_bar['maximum']}")

                elif message[0] == 'done':
                    self.df_transactions, self.df_products, self.df_customers = message[1]
                    # Re-enable the buttons
                    self.fetch_button.config(state='normal')
                    self.analyze_button.config(state='normal')
                    self.report_button.config(state='normal')
                    self.daily_report_button.config(state='normal')
                    self.range_report_button.config(state='normal')
                    self.product_analysis_button.config(state='normal')

                    # Inform the user about the fetched data
                    if self.df_transactions.empty:
                        messagebox.showinfo("Informacja", "Brak danych transakcji do pobrania w wybranym zakresie dat.")
                        logging.info("Brak danych transakcji do pobrania.")
                    else:
                        # Informacja o liczbie pobranych rekordów
                        record_count = len(self.df_transactions)
                        messagebox.showinfo("Sukces", f"Pobrano {record_count} rekordów transakcji.")
                        logging.info(f"Pobrano {record_count} rekordów transakcji.")

                    # Informacja o pobranych produktach i klientach
                    if not self.df_products.empty:
                        messagebox.showinfo("Sukces", f"Pobrano {len(self.df_products)} produktów.")
                        logging.info(f"Pobrano {len(self.df_products)} produktów.")
                    else:
                        messagebox.showwarning("Uwaga", "Brak danych produktów do pobrania.")
                        logging.warning("Brak danych produktów do pobrania.")

                    if not self.df_customers.empty:
                        messagebox.showinfo("Sukces", f"Pobrano {len(self.df_customers)} klientów.")
                        logging.info(f"Pobrano {len(self.df_customers)} klientów.")
                    else:
                        messagebox.showwarning("Uwaga", "Brak danych klientów do pobrania.")
                        logging.warning("Brak danych klientów do pobrania.")

                elif message[0] == 'error':
                    error_message = message[1]
                    messagebox.showerror("Błąd", f"Wystąpił błąd podczas pobierania danych: {error_message}")
                    logging.error(f"Błąd podczas pobierania danych: {error_message}")
                    # Re-enable the buttons
                    self.fetch_button.config(state='normal')
                    self.analyze_button.config(state='normal')
                    self.report_button.config(state='normal')
                    self.daily_report_button.config(state='normal')
                    self.range_report_button.config(state='normal')
                    self.product_analysis_button.config(state='normal')
                    logging.debug(f"Error occurred: {error_message}")

            # Continue checking the queue
            self.window.after(100, self.process_queue)

        except Exception as e:
            logging.error(f"Błąd podczas przetwarzania kolejki: {e}")
            logging.debug(f"Error in process_queue: {e}")
            self.window.after(100, self.process_queue)

    def analyze_data(self):
        # Implement your data analysis logic here
        messagebox.showinfo("Informacja", "Funkcja analizy danych nie jest jeszcze zaimplementowana.")
        logging.info("Analiza danych została wywołana, ale nie zaimplementowana.")

    def generate_report(self):
        # Implement your report generation logic here
        messagebox.showinfo("Informacja", "Funkcja generowania raportu nie jest jeszcze zaimplementowana.")
        logging.info("Generowanie raportu zostało wywołane, ale nie zaimplementowane.")

    def generate_daily_report(self):
        """
        Funkcja do generowania raportu sprzedaży dla dnia.
        """
        try:
            report_date_str = simpledialog.askstring("Raport Codzienny", "Wprowadź datę (YYYY-MM-DD):")
            if not report_date_str:
                return

            try:
                report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.")
                return

            # Sprawdzenie, czy 'entryDate' istnieje i jest typu datetime
            if 'entryDate' not in self.df_transactions.columns:
                messagebox.showerror("Błąd", "Dane transakcji nie zawierają kolumny 'entryDate'.")
                logging.error("Dane transakcji nie zawierają kolumny 'entryDate'.")
                return

            if self.df_transactions['entryDate'].dtype != 'datetime64[ns]':
                self.df_transactions['entryDate'] = pd.to_datetime(self.df_transactions['entryDate'], errors='coerce')

            # Usunięcie wierszy z brakującymi datami
            self.df_transactions = self.df_transactions.dropna(subset=['entryDate'])

            # Debugowanie DataFrame
            debug_dataframe(self.df_transactions, "df_transactions")

            # Generowanie raportu
            report = daily_sales_report(self.df_transactions, report_date)
            if report is None:
                messagebox.showerror("Błąd", "Nie udało się wygenerować raportu.")
                return

            # Tworzenie DataFrame z raportu
            report_df = pd.DataFrame([report])

            # Wybór lokalizacji do zapisania raportu
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return

            # Zapisywanie raportu do Excela
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                report_df.to_excel(writer, sheet_name='Raport Codzienny', index=False)

            messagebox.showinfo("Sukces", f"Raport codzienny został zapisany: {file_path}")
            logging.info(f"Raport codzienny został zapisany: {file_path}")

        except Exception as e:
            logging.error(f"Błąd podczas generowania raportu codziennego: {e}")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas generowania raportu: {e}")

    def generate_range_report(self):
        """
        Funkcja do generowania raportu sprzedaży dla zakresu dat.
        """
        try:
            start_date_str = simpledialog.askstring("Raport Zakres Dat", "Wprowadź datę początkową (YYYY-MM-DD):")
            if not start_date_str:
                return

            end_date_str = simpledialog.askstring("Raport Zakres Dat", "Wprowadź datę końcową (YYYY-MM-DD):")
            if not end_date_str:
                return

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.")
                return

            if start_date > end_date:
                messagebox.showerror("Błąd", "Data początkowa nie może być późniejsza niż data końcowa.")
                return

            # Generowanie raportu
            report = sales_report_range(self.df_transactions, start_date, end_date)
            if report is None:
                messagebox.showerror("Błąd", "Nie udało się wygenerować raportu.")
                return

            # Tworzenie DataFrame z raportu
            report_df = pd.DataFrame([report])

            # Wybór lokalizacji do zapisania raportu
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return

            # Zapisywanie raportu do Excela
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                report_df.to_excel(writer, sheet_name='Raport Zakres Dat', index=False)

            messagebox.showinfo("Sukces", f"Raport dla zakresu dat został zapisany: {file_path}")
            logging.info(f"Raport dla zakresu dat został zapisany: {file_path}")

        except Exception as e:
            logging.error(f"Błąd podczas generowania raportu dla zakresu dat: {e}")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas generowania raportu: {e}")

    def analyze_specific_product(self):
        """
        Funkcja do analizy konkretnego produktu.
        """
        try:
            product_name = simpledialog.askstring("Analiza Produktu", "Wprowadź nazwę produktu:")
            if not product_name:
                return

            # Analiza produktu
            analysis = analyze_product(self.df_transactions, self.df_products, product_name)
            if analysis is None:
                messagebox.showerror("Błąd", f"Nie udało się przeanalizować produktu '{product_name}'.")
                return

            # Tworzenie DataFrame z analizy
            analysis_df = pd.DataFrame([analysis])

            # Wybór lokalizacji do zapisania analizy
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return

            # Zapisywanie analizy do Excela
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                analysis_df.to_excel(writer, sheet_name='Analiza Produktu', index=False)

            messagebox.showinfo("Sukces", f"Analiza produktu '{product_name}' została zapisana: {file_path}")
            logging.info(f"Analiza produktu '{product_name}' została zapisana: {file_path}")

        except Exception as e:
            logging.error(f"Błąd podczas analizy produktu: {e}")
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas analizy produktu: {e}")
