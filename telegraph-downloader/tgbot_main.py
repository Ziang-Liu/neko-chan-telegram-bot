import asyncio, os, queue
from logger import logger
from download_module import start_download  # 导入下载模块中的 start_download 函数

async def run_subprocess():
    while True:
        try:
            os.chdir(os.path.dirname(__file__))  # 切换工作目录到当前文件所在目录
            process = await asyncio.create_subprocess_exec('python', 'tgbot_service.py')  # 创建子进程
            await process.communicate()  # 等待子进程执行完毕
        except Exception as e:
            logger.error('MAIN: Subprocess Error:', e)

# 读取链接并进行下载
async def read_and_download_link(queue_links, filename, isepub=False):
    while True:
        os.chdir(os.path.dirname(__file__))  # 切换工作目录到当前文件所在目录
        if os.path.exists(filename):
            with open(filename, "r", encoding='utf-8') as file:
                for link in file:
                    queue_links.put(link.strip())  # 将链接加入队列
            logger.info(f'MAIN: Read {filename} and add links to the queue.')

        if not queue_links.empty():
            try:
                os.remove(filename)
            except:
                pass
            link = queue_links.get()
            logger.info(f'MAIN: {link} is added to task.')
            download_task = start_download(link, isepub=isepub)
            if download_task:
                await download_task

        
        await asyncio.sleep(1)  # 暂停1秒

async def main():
    komga_queue_link = queue.Queue()  # 创建 Komga 链接队列
    komga_task = asyncio.create_task(read_and_download_link(komga_queue_link, 'komga_link'))  # 创建 Komga 链接的异步任务
    
    #epub_queue_link = queue.Queue()  # 创建 EPUB 链接队列
    #epub_task = asyncio.create_task(read_and_download_link(epub_queue_link, 'epub_link', isepub=True))  # 创建 EPUB 链接的异步任务
    logger.info('MAIN: Start file monitoring service.')

    subprocess_task = asyncio.create_task(run_subprocess())  # 创建子进程的异步任务
    logger.info('MAIN: Start bot service.')

    while True:
        try:
            done, pending = await asyncio.wait({subprocess_task, komga_task}, return_when=asyncio.FIRST_COMPLETED)

            if subprocess_task in done:
                logger.error('MAIN: subprocess_task has exited. Restarting...')
                subprocess_task.cancel()
                await subprocess_task
                subprocess_task = asyncio.create_task(run_subprocess())

            if komga_task in done:
                logger.info('MAIN: komga_task has completed.')
                if subprocess_task in pending:
                    logger.error('MAIN: subprocess_task is still running. It will continue.')
                else:
                    logger.error('MAIN: subprocess_task has exited. Restarting...')
                    subprocess_task.cancel()
                    await subprocess_task
                    subprocess_task = asyncio.create_task(run_subprocess())

        except asyncio.CancelledError:
            logger.error('MAIN: Task has been cancelled.')
            return

if __name__ == "__main__":
    asyncio.run(main())
