import requests, re, os, zipfile, threading
import tkinter as tk
from bs4 import BeautifulSoup
        
def get_pictures(url, file_path):
    if not os.path.exists(file_path):
        requested_url = requests.get(url)
        with open(file_path, 'wb') as f:
            for chunk in requested_url.iter_content(chunk_size=128):
                f.write(chunk)
        #print(f"'{file_path}'ok",end='|')
    else:
        return
        #print(f"skip'{file_path}'",end='|')
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
    if not os.path.exists(output): #如果存在zip就跳过
        output_zip = zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(path):
            relative_root = '' if root == path else root.replace(path, '') + os.sep
            for filename in files:
                if ".jpg" in filename:
                    output_zip.write(os.path.join(root, filename), relative_root + filename)
        output_zip.close()
        #print(f"\ncreate zip file '{output}'")
    else:
        return
        #print(f"\n{output} exists")
    #删除单独的图片
    for image in file_list:
        if ".jpg" in image:
            image_path = os.path.join(path,image)
            os.remove(image_path)

def start_download(url, console):
    #获取请求头
    send_url = "https://www.baidu.com"
    agent_response = requests.head(send_url) #发送head请求返回agent
    user_agent = agent_response.request.headers['User-Agent']
    headers = {'User-Agent': user_agent} #这里的agent显示的是python/版本号
    #获取图片url
    requested_url = requests.get(url,headers=headers)
    image_urls = get_pictures_urls(requested_url.text)
    #获取本子名字
    soup = BeautifulSoup(requested_url.text,'html.parser')
    manga_title = soup.find("title")
    converted_title = re.sub(r'<title>|</title>|\*|\||\?|– Telegraph| |/|:', lambda x: {'<title>': '', '</title>': '', '*': '', '|': '', '?': '', '– Telegraph': '', ' ': '', '/': '∕', ':': '∶'}[x.group()], str(manga_title)) #正则规范本子标题
    #创建并进入本子目录
    script_path = os.path.abspath(__file__) #获取python文件的当前路径
    folder_path = os.path.dirname(script_path)
    target_path = folder_path + '\\' + converted_title
    if not os.path.exists(target_path): #判断是否创建过目录
        os.mkdir(target_path)
        os.chdir(target_path)
        console.insert(tk.END, "Directory created: " + target_path + "\n")
    else:
        os.chdir(target_path)
        console.insert(tk.END, "Directory already exists: " + target_path + "\n")
    #下载图片
    console.insert(tk.END, "Start downloading...\n")
    threads = []
    for i in range(len(image_urls)):
        url='https://telegra.ph'+image_urls[i]
        path="img"+str(i)+'.jpg'
        t = threading.Thread(target=get_pictures, args=(url, path)) #引入多线程
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    #压缩文件夹再删除原目录文件
    zip_folder(target_path)
    console.insert(tk.END, "Download Complete!\n")