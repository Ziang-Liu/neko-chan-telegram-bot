import requests, re, os, zipfile, concurrent.futures, logging
from bs4 import BeautifulSoup
from env import *

# logger format
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# import from env (used by docker)
try:
    download_threads = int(DOWNLOAD_THREADS)
except (ValueError, TypeError):
    download_threads = 8 # 默认多线程为 8
send_url = GET_HEADER_TEST_URL
docker_download_location = DOWNLOAD_PATH

def get_default_folder():
    current_directory = os.path.dirname(__file__)
    new_folder_path = os.path.join(current_directory, "download")
    os.makedirs(new_folder_path, exist_ok=True)
    return new_folder_path

def get_pictures(url, file_path) -> str:
    if not os.path.exists(file_path): # 图片没有下载的情况下写入图片
        requested_url = requests.get(url)
        with open(file_path, 'wb') as f:
            for chunk in requested_url.iter_content(chunk_size=128):
                f.write(chunk)
    else:
        return

def get_pictures_urls(text) -> str:
    urls = []  # 存放url路径
    start_tag = 'img src="'  # 图片头
    end_quote = '"' # 图片尾
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

def zip_folder(path, output = None) -> str:
    file_list = os.listdir(path)
    output = output or os.path.basename(path) + '.zip' # 压缩包的文件名
    if os.path.exists(output):
        return
    
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as output_zip:
        for root, _, files in os.walk(path):
            relative_root = '' if root == path else root.replace(path, '') + os.sep
            for filename in files:
                if ".jpg" in filename: # 避免zip被嵌套压缩
                    output_zip.write(os.path.join(root, filename), relative_root + filename)
        for image in file_list: # 删掉除压缩包之外的图片
            if ".jpg" in image:
                image_path = os.path.join(path,image)
                os.remove(image_path)
        output_zip.close()

def start_download_zip(url = None, address = docker_download_location) -> str:
    # 获得headers
    agent_response = requests.head(send_url)
    user_agent = agent_response.request.headers['User-Agent']
    headers = {'User-Agent': user_agent}
    # 链接有效性
    if "telegra.ph" not in url:
        logger.warning('Detect wrong telegraph links %s', url)
        return
    # 获取图片url
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
    # 路径有效性
    if not os.path.isdir(address):
        logger.warning('Invalid path: %s', address)
        return
    # 创建文件夹
    os.chdir(address)
    target_path = os.path.join(address, converted_title)
    if not os.path.exists(target_path): # 创建新路径
        os.mkdir(target_path)
        logger.info('Directory created: %s',target_path)
    else:
        logger.info('Directory already exists, skip %s',target_path)
    os.chdir(target_path)
    # 多线程下载
    with concurrent.futures.ThreadPoolExecutor(max_workers = download_threads) as executor:  # 限制并发线程数量
        future_to_url = {executor.submit(get_pictures, 'https://telegra.ph' + url, f'img{i}.jpg'): url for i, url in enumerate(image_urls)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
    # 打包
    zip_folder(target_path) 
    logger.info('Successfully download %s', manga_title)

def start_download_epub(url = None, console = None, address = get_default_folder()):
    '''
    logics wait to append
    '''