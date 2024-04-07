import asyncio
import os
import queue

from telegraphlib.download import TelegraphDownloader
from telegraphlib.logger import logger


async def run_subprocess():
    while True:
        try:
            os.chdir(os.path.dirname(__file__))
            process = await asyncio.create_subprocess_exec('python', 'tgbot_service.py')  # 创建子进程
            await process.communicate()
        except Exception as e:
            logger.error(f'Subprocess Error: {e}')


async def download_from_link(queue_links, filename):
    while True:
        os.chdir(os.path.dirname(__file__))
        if os.path.exists(filename):
            with open(filename, "r", encoding = 'utf-8') as file:
                for link in file:
                    queue_links.put(link.strip())
            logger.info(f'Read {filename} and add links to the queue.')

        if not queue_links.empty():
            try:
                os.remove(filename)
            except:
                pass
            downloader = TelegraphDownloader()
            downloader.url = queue_links.get()
            logger.info(f'{downloader.url} is added to task.')
            download_task = downloader.pack_zip()
            if download_task == 114514:
                logger.error("Task failed")
            elif download_task == 0:
                await download_task

        await asyncio.sleep(1)


async def main():
    komga_queue_link = queue.Queue()
    komga_task = asyncio.create_task(
        download_from_link(komga_queue_link, 'komga_link'))
    epub_queue_link = queue.Queue()
    epub_task = asyncio.create_task(
        download_from_link(epub_queue_link, 'epub_link'))
    logger.info('Start links monitoring service.')

    subprocess_task = asyncio.create_task(run_subprocess())
    logger.info('Start bot service.')

    while True:
        try:
            done, _ = await asyncio.wait({subprocess_task, komga_task, epub_task},
                                         return_when = asyncio.FIRST_COMPLETED)

            if subprocess_task in done:
                if subprocess_task.exception() is not None:
                    logger.error('Subprocess_task has exited unexpectedly. Restarting...')
                    subprocess_task = asyncio.create_task(run_subprocess())

        except asyncio.CancelledError:
            logger.error('Task has been cancelled.')
            return


if __name__ == "__main__":
    asyncio.run(main())
