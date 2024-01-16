import asyncio, os, queue
from download_module import start_download_zip

async def run_subprocess():
    process = await asyncio.create_subprocess_exec('python', 'tgbot_service.py')
    await process.communicate()

async def read_links(queue_links):
    while True:
        if os.path.exists('links'):
            with open('links', "r", encoding='utf-8') as file:
                for link in file:
                    queue_links.put(link.strip())
            os.remove('links')
        await asyncio.sleep(1)  # 每隔1秒检查一次文件

async def check_and_download(queue_links):
    while True:
        if not queue_links.empty():
            link = queue_links.get()
            download_task = start_download_zip(link)
            if download_task:  # 确保返回有效异步对象
                await download_task

        await asyncio.sleep(1)  # 每隔1秒检查一次队列

async def main():
    queue_links = queue.Queue()
    read_task = asyncio.create_task(read_links(queue_links)) # 链接逐行读进任务队列
    download_task = asyncio.create_task(check_and_download(queue_links))
    subprocess_task = asyncio.create_task(run_subprocess()) # 为python-bot开一个子进程
    try:
        await asyncio.gather(subprocess_task, read_task, download_task)
    except asyncio.CancelledError:
        subprocess_task.cancel()
        read_task.cancel()
        download_task.cancel()
        await subprocess_task
        await read_task
        await download_task

if __name__ == "__main__":
    asyncio.run(main())
