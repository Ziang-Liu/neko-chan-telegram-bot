import requests, re, os, zipfile, concurrent.futures
import tkinter as tk
from bs4 import BeautifulSoup
from dotenv import load_dotenv

#env_var
load_dotenv()
download_threads = int(os.getenv('DOWNLOAD_THREADS'))
send_url = os.getenv('GET_HEADER_TEST_URL')

def get_default_folder():
    current_directory = os.path.dirname(__file__)
    new_folder_path = os.path.join(current_directory, "Download")
    os.makedirs(new_folder_path, exist_ok=True)
    return new_folder_path

def get_pictures(url, file_path):
    
    if not os.path.exists(file_path): #图片没有下载的情况下写入图片
        requested_url = requests.get(url)
        with open(file_path, 'wb') as f:
            for chunk in requested_url.iter_content(chunk_size=128):
                f.write(chunk)
    else:
        return

def get_pictures_urls(text):
    
    urls = []  # 存放提取的url
    start_tag = 'img src="'  # 发现图片的起始标记
    end_quote = '"'
    start = 0
    while True:
        start = text.find(start_tag, start)
        if start == -1:
            break 
        start += len(start_tag)
        end = text.find(end_quote, start)
        if end == -1:
            break
        urls.append(text[start:end])
        start = end
    return urls

def zip_folder(path, output = None):
    
    file_list = os.listdir(path)
    output = output or os.path.basename(path) + '.zip'
    
    if os.path.exists(output):
        return

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as output_zip:
        for root, _, files in os.walk(path):
            relative_root = '' if root == path else root.replace(path, '') + os.sep
            for filename in files:
                if ".jpg" in filename: #避免zip被嵌套压缩
                    output_zip.write(os.path.join(root, filename), relative_root + filename)
        for image in file_list: #删掉压缩包之外的图片
            if ".jpg" in image:
                image_path = os.path.join(path,image)
                os.remove(image_path)
        
        output_zip.close()

def start_download_zip(url = None, console = None, address = get_default_folder()):
    
    #获得headers
    agent_response = requests.head(send_url)
    user_agent = agent_response.request.headers['User-Agent']
    headers = {'User-Agent': user_agent}
    
    #链接有效性
    if "telegra.ph" not in url:
        if console is not None:
            console.insert(tk.END, "***Wrong Link***\n")
        return
    
    #获取图片url
    requested_url = requests.get(url, headers=headers)
    image_urls = get_pictures_urls(requested_url.text)
    
    #获取title
    soup = BeautifulSoup(requested_url.text, 'html.parser')
    manga_title = soup.find("title")
    converted_title = re.sub(
        r'<title>|</title>|\*|\||\?|– Telegraph| |/|:', 
        lambda x: {'<title>': '', '</title>': '', '*': '', '|': '', '?': '', '– Telegraph': '', ' ': '', '/': '∕', ':': '∶'}[x.group()],
        str(manga_title)
        )
    
    #路径有效性
    if not os.path.isdir(address):
        console.insert(tk.END, "***Wrong Path***\n")
        return
    #创建文件夹
    os.chdir(address)
    target_path = os.path.join(address, converted_title)
    if not os.path.exists(target_path):
        os.mkdir(target_path)
        if console is not None:
            console.insert(tk.END, "Directory created: " + target_path + "\n")
    else:
        if console is not None:
            console.insert(tk.END, "Directory already exists: " + target_path + "\n")
    os.chdir(target_path)
    #下载
    if console is not None:
        console.insert(tk.END, "***Start downloading...***\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers = download_threads) as executor:  # 限制并发线程数量
        future_to_url = {executor.submit(get_pictures, 'https://telegra.ph' + url, f'img{i}.jpg'): url for i, url in enumerate(image_urls)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as exc:
                if console is not None:
                    print(f"Downloading {url} generated an exception: {exc}")
    #压缩打包
    zip_folder(target_path) 
    if console is not None:
        console.insert(tk.END, "***Download Complete!***\n")

def start_download_epub(url = None, console = None, address = get_default_folder()):
    '''
    logic
    '''