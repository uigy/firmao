# File: main.py

import tkinter as tk
from ttkthemes import ThemedTk
from ui.main_window import MainWindow

def main():
    # Creating the main window with the "azure" theme
    window = ThemedTk(theme="azure")
    app = MainWindow(window)
    window.mainloop()

if __name__ == "__main__":
    main()
