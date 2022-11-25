import logging
import sys
import json
from time import sleep
import aiofiles
import aiohttp
import asyncio
import datetime
import os

SHIKIMOTI_URL = "https://shikimori.one/"

LOG_FILE_NAME = (
    f"./logs/log {datetime.datetime.now().strftime('date-%Y-%m-%d_time-%H_%M_%S')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE_NAME,
    filemode="w",
)


def do_try_complite_async(func):
    async def wrapper(*args, **kwargs):
        while True:
            try:
                return await func(*args, **kwargs)
            except aiohttp.client_exceptions.ContentTypeError as e:
                # logging.info(f"HTTP ERR {e}")
                sleep(0.3)
            except (
                asyncio.exceptions.TimeoutError,
                aiohttp.client_exceptions.ServerDisconnectedError,
            ):
                sleep(0.3)
            except Exception as e:
                logging.error("ERROR!!!!!!!!!!!", e)

    return wrapper


@do_try_complite_async
async def get_screenshots_list(session, anime_id: int) -> list[str]:
    ans = []
    async with session.get(
        SHIKIMOTI_URL + f"/api/animes/{anime_id}/screenshots"
    ) as resp:
        ans = await resp.json()

    ans = list(map(lambda x: x["original"], ans))

    return ans


@do_try_complite_async
async def get_anime_ids(page_num: int):
    dirty_anime_list = []
    async with aiofiles.open(f"./animes/page_{page_num}.json", encoding="utf8") as f:
        s = await f.read()
        dirty_anime_list = json.loads(s)

    anime_ids = []
    for i in dirty_anime_list:
        try:
            anime_ids.append((i["id"], i["image"]["original"]))
        except:
            pass

    return anime_ids


@do_try_complite_async
async def download_image(session, url: str):
    async with session.get(url) as resp:
        if resp.status == 200:
            return await resp.read()


async def save_image(anime_id, page_num, image, file_name):
    path = f"./images/{page_num}/{anime_id}"
    if not os.path.exists(path):
        os.makedirs(path)

    async with aiofiles.open(os.path.join(path, file_name), mode="wb") as file:
        await file.write(image)


async def download_and_save_image(session, url, anime_id, page_num, file_name):
    data = await download_image(session, url)
    await save_image(anime_id, page_num, data, file_name)


async def parse_for_page(session, page_num: int):
    ids = await get_anime_ids(page_num)

    tasks = []
    for aid, poster in ids:

        screenshots = await get_screenshots_list(session, aid)
        tasks = []

        tail = poster.split("/")[-1].split("?")[0].split(".")[-1]
        if not os.path.exists("./images/{page_num}/{aid}/poster.{tail}"):
            tasks.append(
                download_and_save_image(
                    session, SHIKIMOTI_URL + poster, aid, page_num, f"poster.{tail}"
                )
            )
        for idx, screenshot in enumerate(screenshots[:5]):
            tail = screenshot.split("/")[-1].split("?")[0].split(".")[-1]

            if not os.path.exists("./images/{page_num}/{aid}/{idx}.{tail}"):
                tasks.append(
                    download_and_save_image(
                        session,
                        SHIKIMOTI_URL + screenshot,
                        aid,
                        page_num,
                        f"{idx}.{tail}",
                    )
                )
        await asyncio.gather(*tasks)


async def main():
    first_page, last_page = int(sys.argv[1]), int(sys.argv[2]) + 1
    tasks = []
    async with aiohttp.ClientSession() as session:
        for page_num in range(first_page, last_page):
            tasks.append(parse_for_page(session, page_num))
        await asyncio.gather(*tasks)


asyncio.run(main())
