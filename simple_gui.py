import tkinter as tk
from tkinter import scrolledtext
import download_module  # 引入下载模块
import threading

def start_download():
    url = entry.get()
    entry.delete(0, tk.END)
    download_thread = threading.Thread(target=download_module.start_download, args=(url, console))
    download_thread.start()

# 主窗口
window = tk.Tk()
window.title("Telegraph Downloader")
# 输入界面
input_frame = tk.Frame(window)
input_frame.pack(expand=True, fill="x")
label = tk.Label(input_frame, text="Enter the URL:")
label.pack(side="left")
entry = tk.Entry(input_frame, width=40)
entry.pack(side="left", padx=10, expand=True, fill="x")
button = tk.Button(input_frame, text="Start Download", command=start_download)
button.pack(side="left", padx=10)
# 控制台输出界面
console = scrolledtext.ScrolledText(window, width=40, height=20)
console.pack(expand=True, fill="both")

window.mainloop()
