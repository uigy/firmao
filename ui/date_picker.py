# File: ui/date_picker.py

import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar

def select_date(parent, entry_field):
    """Opens a calendar to select a date and inserts it into the given entry field."""
    def on_date_select():
        selected_date = cal.selection_get()
        entry_field.delete(0, tk.END)
        entry_field.insert(0, selected_date.strftime('%Y-%m-%d'))
        top.destroy()

    top = tk.Toplevel(parent)
    top.grab_set()
    cal = Calendar(top, selectmode='day', date_pattern='yyyy-mm-dd')
    cal.pack(padx=10, pady=10)

    ttk.Button(top, text="Wybierz", command=on_date_select).pack(pady=5)
