import ctypes
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter.ttk import *

from src.telegraphlib.download import TelegraphDownloader


def start():
    downloader = TelegraphDownloader()
    downloader.url = entry1.get()
    downloader.download_path = entry2.get()
    # change to your own proxy
    downloader.proxy = {"http": "host:port", "https": "host:port"}
    entry1.delete(0, tk.END)
    epub_check = epub_var.get()

    if epub_check:
        download_thread = threading.Thread(target = downloader.pack_epub)
    else:
        download_thread = threading.Thread(target = downloader.pack_zip)

    download_thread.start()


def on_enter_pressed(events):
    start()


def select_folder():
    folder_path = filedialog.askdirectory()
    entry2.delete(0, tk.END)
    entry2.insert(0, folder_path)


window = tk.Tk()
window.title("Telegraph Downloader")
window.resizable(False, False)

try:
    # For Windows platform only
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    window.tk.call('tk', 'scaling', ScaleFactor / 75)
except Exception:
    pass

input_frame = tk.Frame(window, padx = 10, pady = 10)
input_frame.pack(fill = "both", expand = True)

label1 = tk.Label(input_frame, text = "Telegraph URL:")
label1.grid(row = 0, column = 0, sticky = "w")
entry1 = tk.Entry(input_frame, width = 40)
entry1.grid(row = 0, column = 1, padx = 10, sticky = "we")

label2 = tk.Label(input_frame, text = "Folder location:")
label2.grid(row = 1, column = 0, sticky = "w")
entry2 = tk.Entry(input_frame, width = 40)
entry2.grid(row = 1, column = 1, padx = 10, sticky = "we")

browse_button = tk.Button(input_frame, text = "Browse", command = select_folder)
browse_button.grid(row = 1, column = 2)

epub_var = tk.BooleanVar()
epub_checkbox = Checkbutton(input_frame, text = "Generate ePub", variable = epub_var)
epub_checkbox.grid(row = 2, columnspan = 3)

button = tk.Button(input_frame, text = "Start Download", command = start)
button.grid(row = 3, columnspan = 3, pady = 10)

entry1.bind('<Return>', on_enter_pressed)
entry2.bind('<Return>', on_enter_pressed)

window.mainloop()
