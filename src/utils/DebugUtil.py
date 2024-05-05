import threading
import tkinter as tk
from tkinter.ttk import *

from src.service.TelegraphService import Telegraph


def start():
    downloader1 = Telegraph()
    downloader1.url = entry1.get()
    entry1.delete(0, tk.END)
    epub_check = epub_var.get()

    if epub_check:
        download_thread = threading.Thread(target = downloader1.pack_to_epub())
    else:
        download_thread = threading.Thread(target = downloader1.sync_to_library())

    download_thread.start()


window = tk.Tk()
window.title("debug")
window.resizable(False, False)

input_frame = tk.Frame(window, padx = 10, pady = 10)
input_frame.pack(fill = "both", expand = True)

label1 = tk.Label(input_frame, text = "Telegraph URL:")
label1.grid(row = 0, column = 0, sticky = "w")
entry1 = tk.Entry(input_frame, width = 40)
entry1.grid(row = 0, column = 1, padx = 10, sticky = "we")

epub_var = tk.BooleanVar()
epub_checkbox = Checkbutton(input_frame, text = "Convert to EPUB", variable = epub_var)
epub_checkbox.grid(row = 2, columnspan = 3)

button = tk.Button(input_frame, text = "Start Download", command = start)
button.grid(row = 3, columnspan = 3, pady = 10)

window.mainloop()
