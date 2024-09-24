import tkinter as tk
from tkcalendar import DateEntry
from tkinter import ttk

def select_date(parent):
    """
    Opens a dialog with a calendar and returns the selected date as a string in YYYY-MM-DD format.
    """
    selected_date = tk.StringVar()

    dialog = tk.Toplevel(parent)
    dialog.title("Select Date")
    dialog.grab_set()  # Make the dialog modal

    ttk.Label(dialog, text="Please select a date:").pack(padx=10, pady=10)
    cal = DateEntry(dialog, date_pattern='yyyy-mm-dd', width=12, background='darkblue',
                    foreground='white', borderwidth=2)
    cal.pack(padx=10, pady=10)

    def on_ok():
        selected = cal.get_date()
        selected_date.set(selected.strftime('%Y-%m-%d'))
        dialog.destroy()

    ttk.Button(dialog, text="OK", command=on_ok).pack(pady=5)

    dialog.wait_window()  # Wait until the dialog is closed
    return selected_date.get()
