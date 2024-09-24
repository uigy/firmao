import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkthemes import ThemedTk
import threading
import queue
from datetime import datetime, timedelta

from api.fetching import get_total_pages, fetch_endpoint_data
from utils.logger import setup_logger
import pandas as pd
import logging

# Import DateEntry from tkcalendar
from tkcalendar import DateEntry

# Initialize logger
setup_logger()

def debug_dataframe(df, name="DataFrame"):
    """
    Function to display DataFrame structure and sample data.
    """
    print(f"\n--- Debugging {name} ---")
    print("DataFrame structure:")
    print(df.info())
    print("\nSample data:")
    print(df.head())
    print("--- End Debugging ---\n")

class MainWindow:
    def __init__(self):
        self.window = ThemedTk(theme="arc")
        self.window.title("Firmao Data Downloader")
        self.window.geometry("600x400")
        self.window.resizable(False, False)

        # Create a thread-safe queue for progress updates
        self.progress_queue = queue.Queue()

        # Initialize dataframes
        self.df_transactions = pd.DataFrame()
        self.df_products = pd.DataFrame()
        self.df_customers = pd.DataFrame()

        # Create UI elements
        self.create_widgets()

        # Set default dates
        self.set_default_dates()

        # Start the main loop
        self.window.mainloop()

    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a label frame for date selection
        date_frame = ttk.LabelFrame(main_frame, text="Select Date Range", padding="10")
        date_frame.pack(fill=tk.X, padx=10, pady=10)

        # Start date using DateEntry
        start_date_label = ttk.Label(date_frame, text="Start Date:")
        start_date_label.grid(column=0, row=0, padx=5, pady=5, sticky="e")
        self.start_date_entry = DateEntry(
            date_frame,
            date_pattern='yyyy-mm-dd',
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            selectmode='day'
        )
        self.start_date_entry.grid(column=1, row=0, padx=5, pady=5)
        # Removed the line causing the AttributeError

        # End date using DateEntry
        end_date_label = ttk.Label(date_frame, text="End Date:")
        end_date_label.grid(column=0, row=1, padx=5, pady=5, sticky="e")
        self.end_date_entry = DateEntry(
            date_frame,
            date_pattern='yyyy-mm-dd',
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            selectmode='day'
        )
        self.end_date_entry.grid(column=1, row=1, padx=5, pady=5)
        # Removed the line causing the AttributeError

        # Fetch data button
        self.fetch_button = ttk.Button(main_frame, text="Fetch Data", command=self.fetch_data)
        self.fetch_button.pack(pady=10)

        # Save data button
        self.save_button = ttk.Button(main_frame, text="Save Data to CSV", command=self.save_data_to_csv)
        self.save_button.pack(pady=5)
        self.save_button.config(state='disabled')

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=20, pady=20)

    def set_default_dates(self):
        today = datetime.today()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

        self.start_date_entry.set_date(first_day_of_previous_month)
        self.end_date_entry.set_date(last_day_of_previous_month)

    def fetch_data(self):
        try:
            # Parse the input dates from DateEntry widgets
            start_date = self.start_date_entry.get_date()
            end_date = self.end_date_entry.get_date()

            # Validate date range
            if start_date > end_date:
                messagebox.showerror("Error", "Start date cannot be later than end date.")
                return

            # Disable the fetch button to prevent multiple clicks
            self.fetch_button.config(state='disabled')
            self.save_button.config(state='disabled')

            # Reset the progress bar
            self.progress_var.set(0)
            self.progress_bar['value'] = 0

            # Start the data fetching in a separate thread
            thread = threading.Thread(target=self.fetch_data_thread, args=(start_date, end_date))
            thread.daemon = True  # Ensure thread exits when main program exits
            thread.start()

            # Start checking the queue for progress updates
            self.window.after(100, self.process_queue)

        except Exception as e:
            logging.error(f"Error during data fetch initialization: {e}")
            messagebox.showerror("Error", f"An error occurred during data fetch initialization: {e}")
            self.fetch_button.config(state='normal')
            self.save_button.config(state='disabled')

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

            # Initialize dataframes
            self.df_transactions = pd.DataFrame()
            self.df_products = pd.DataFrame()
            self.df_customers = pd.DataFrame()

            total_steps = 0

            # Calculate total number of pages across all endpoints
            for endpoint in endpoints:
                num_pages = get_total_pages(endpoint['name'], endpoint['params'])
                total_steps += num_pages

            # Update progress bar maximum
            self.progress_queue.put(('set_maximum', total_steps))

            # Fetch data for each endpoint
            for endpoint in endpoints:
                data_df = fetch_endpoint_data(endpoint['name'], endpoint['params'], self.api_progress_callback)
                if endpoint['name'] == 'transactions':
                    self.df_transactions = data_df
                elif endpoint['name'] == 'products':
                    self.df_products = data_df
                elif endpoint['name'] == 'customers':
                    self.df_customers = data_df

            # Finalize progress
            self.progress_queue.put(('done', None))

            logging.debug("Data fetching complete")

        except Exception as e:
            logging.error(f"Error in data fetching thread: {e}")
            self.progress_queue.put(('error', f"Error during data fetching: {e}"))

    def api_progress_callback(self, status, *args):
        """
        Callback function to communicate progress from API functions to the main thread.
        """
        if status == 'progress':
            # Increment progress
            self.progress_queue.put(('increment', None))

    def process_queue(self):
        """
        Process messages from the progress_queue and update the progress bar accordingly.
        """
        try:
            while not self.progress_queue.empty():
                message = self.progress_queue.get_nowait()
                if message[0] == 'set_maximum':
                    total_steps = message[1]
                    self.progress_bar['maximum'] = total_steps
                    self.progress_var.set(0)
                elif message[0] == 'increment':
                    self.progress_var.set(self.progress_var.get() + 1)
                elif message[0] == 'done':
                    # Re-enable buttons
                    self.fetch_button.config(state='normal')
                    self.save_button.config(state='normal')

                    # Inform the user about the fetched data
                    summary = ""
                    if not self.df_transactions.empty:
                        record_count = len(self.df_transactions)
                        summary += f"Transactions: {record_count} records fetched.\n"
                        logging.info(f"{record_count} transaction records fetched.")
                    else:
                        summary += "No transaction data fetched.\n"
                        logging.info("No transaction data fetched.")

                    if not self.df_products.empty:
                        product_count = len(self.df_products)
                        summary += f"Products: {product_count} records fetched.\n"
                        logging.info(f"{product_count} product records fetched.")
                    else:
                        summary += "No product data fetched.\n"
                        logging.info("No product data fetched.")

                    if not self.df_customers.empty:
                        customer_count = len(self.df_customers)
                        summary += f"Customers: {customer_count} records fetched.\n"
                        logging.info(f"{customer_count} customer records fetched.")
                    else:
                        summary += "No customer data fetched.\n"
                        logging.info("No customer data fetched.")

                    messagebox.showinfo("Data Fetch Complete", summary)
                elif message[0] == 'error':
                    error_message = message[1]
                    messagebox.showerror("Error", f"An error occurred during data fetching: {error_message}")
                    logging.error(f"Error during data fetching: {error_message}")
                    # Re-enable the fetch button
                    self.fetch_button.config(state='normal')
                    self.save_button.config(state='disabled')

            # Continue checking the queue
            self.window.after(100, self.process_queue)

        except Exception as e:
            logging.error(f"Error processing queue: {e}")
            self.window.after(100, self.process_queue)

    def save_data_to_csv(self):
        """
        Saves the fetched data to CSV files.
        """
        try:
            # Select directory to save files
            directory = filedialog.askdirectory()
            if not directory:
                return

            # Save df_transactions
            if not self.df_transactions.empty:
                transactions_file = f"{directory}/transactions.csv"
                self.df_transactions.to_csv(transactions_file, index=False)
                logging.info(f"Transaction data saved to {transactions_file}")
            else:
                messagebox.showwarning("Warning", "No transaction data to save.")
                logging.warning("No transaction data to save.")

            # Save df_products
            if not self.df_products.empty:
                products_file = f"{directory}/products.csv"
                self.df_products.to_csv(products_file, index=False)
                logging.info(f"Product data saved to {products_file}")
            else:
                messagebox.showwarning("Warning", "No product data to save.")
                logging.warning("No product data to save.")

            # Save df_customers
            if not self.df_customers.empty:
                customers_file = f"{directory}/customers.csv"
                self.df_customers.to_csv(customers_file, index=False)
                logging.info(f"Customer data saved to {customers_file}")
            else:
                messagebox.showwarning("Warning", "No customer data to save.")
                logging.warning("No customer data to save.")

            messagebox.showinfo("Success", f"Data has been saved in the folder: {directory}")

        except Exception as e:
            logging.error(f"Error saving data to CSV: {e}")
            messagebox.showerror("Error", f"An error occurred while saving data: {e}")

if __name__ == "__main__":
    MainWindow()
