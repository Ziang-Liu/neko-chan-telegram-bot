import asyncio, os, queue
from logger import logger
from download_module import start_download  # 导入下载模块中的 start_download 函数

async def run_subprocess():
    os.chdir(os.path.dirname(__file__))  # 切换工作目录到当前文件所在目录
    process = await asyncio.create_subprocess_exec('python', 'tgbot_service.py')  # 创建子进程
    await process.communicate()  # 等待子进程执行完毕

# 读取链接并进行下载
async def read_and_download_link(queue_links, filename, isepub=False):
    while True:
        os.chdir(os.path.dirname(__file__))  # 切换工作目录到当前文件所在目录
        if os.path.exists(filename):
            with open(filename, "r", encoding='utf-8') as file:
                for link in file:
                    queue_links.put(link.strip())  # 将链接加入队列
            logger.info(f'Main: Read {filename} and added links to the queue')

        if not queue_links.empty():
            try:
                os.remove(filename)  # 删除临时文件
            except:
                pass
            link = queue_links.get()  # 获取队列链接
            download_task = start_download(link, isepub=isepub)
            if download_task:
                await download_task  # 等待下载任务完成
                logger.info(f'Main: Downloaded: {link}')
        
        await asyncio.sleep(1)  # 暂停1秒

async def main():
    komga_queue_link = queue.Queue()  # 创建 Komga 链接队列
    komga_task = asyncio.create_task(read_and_download_link(komga_queue_link, 'komga_link'))  # 创建 Komga 链接的异步任务

    #epub_queue_link = queue.Queue()  # 创建 EPUB 链接队列
    #epub_task = asyncio.create_task(read_and_download_link(epub_queue_link, 'epub_link', isepub=True))  # 创建 EPUB 链接的异步任务

    subprocess_task = asyncio.create_task(run_subprocess())  # 创建子进程的异步任务

    try:
        await asyncio.gather(  # 并发运行多个异步任务
            subprocess_task,
            komga_task,
            #epub_task
        )
    except asyncio.CancelledError:
        subprocess_task.cancel()
        komga_task.cancel()
        #epub_task.cancel()
        await subprocess_task
        await komga_task
        #await epub_task

if __name__ == "__main__":
    asyncio.run(main())
