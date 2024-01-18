import tkinter as tk
from tkinter import scrolledtext
import download_module, threading

def start():
    url = entry1.get()
    address = entry2.get()
    entry1.delete(0, tk.END)
    download_thread = threading.Thread(target=download_module.start_download, args=(url, address))
    download_thread.start()

def on_enter_pressed(events):
    start()

# 主窗口
window = tk.Tk()
window.title("Telegraph Downloader")
# 输入界面
input_frame = tk.Frame(window)
input_frame.pack(expand=True, fill="x")
label1 = tk.Label(input_frame, text="Telegraph URL:")
label1.grid(row=0, column=0, sticky="w")
entry1 = tk.Entry(input_frame, width=40)
entry1.grid(row=0, column=1, padx=10, sticky="we")
label2 = tk.Label(input_frame, text="Folder location:")
label2.grid(row=1, column=0, sticky="w")
entry2 = tk.Entry(input_frame, width=40)
entry2.grid(row=1, column=1, padx=10, sticky="we")
button = tk.Button(input_frame, text="Start Download", command=start)
button.grid(row=2, column=0, columnspan=2, pady=10)
entry1.bind('<Return>', on_enter_pressed)
entry2.bind('<Return>', on_enter_pressed)
# 主循环
window.mainloop()
