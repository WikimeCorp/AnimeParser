from shikimori_api import Shikimori
import datetime
from time import sleep
import json
import requests
import sys
from tqdm import tqdm
import logging

LIMIT_ONE_PAGE = 50
LAST_PAGE = None

LOG_FILE_NAME = (
    f"./logs/log {datetime.datetime.now().strftime('date-%Y-%m-%d_time-%H_%M_%S')}.log"
)


logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE_NAME,
    filemode="w",
)


def do_try_complite(func):
    while True:
        try:
            ans = func()
            return ans
        except requests.exceptions.HTTPError as e:
            # logging.info(f"HTTP ERR {e}")
            sleep(0.5)
        except Exception as e:
            logging.error("ERROR!!!!!!!!!!!", e)


def get_anime_ids(api, page_num: int, limit: int) -> list[int]:
    ans = api.animes.GET(page=page_num, limit=limit, censored='false')
    return list(map(lambda x: x["id"], ans))


def get_anime_by_id(api, anime_id: int) -> dict:
    anime = api.animes(anime_id).GET()
    return anime


def write_page_to_file(page_num: int, animes: list[dict]):
    with open(f"./animes/page_{page_num}.json", "w", encoding="utf8") as file:
        json.dump(animes, file, ensure_ascii=False)


def get_animes_by_ids(api, anime_ids: list[int], page=-1) -> list[dict]:
    animes = []
    for aid in tqdm(anime_ids, desc=f"Page #{page}", leave=False):
        do_try_complite(lambda: animes.append(get_anime_by_id(api, aid)))
    return animes


def get_animes(api, count: int):
    assert count >= 1
    pages = count // LIMIT_ONE_PAGE
    last_page_limit = count % LIMIT_ONE_PAGE
    ids = []

    outer_progress_bar = tqdm(
        desc="Pages", total=pages + int(bool(last_page_limit)) - LAST_PAGE
    )
    for page_num in range(1 + LAST_PAGE, pages + 1):
        ids = do_try_complite(lambda: get_anime_ids(api, page_num, LIMIT_ONE_PAGE))
        if ids == []:
            print("Аниме закончилось :(")
            break
        animes = get_animes_by_ids(api, ids, page_num)
        write_page_to_file(page_num, animes)
        outer_progress_bar.update(1)

    if last_page_limit != 0:
        ids = do_try_complite(lambda: get_anime_ids(api, pages + 1, last_page_limit))

        animes = get_animes_by_ids(api, ids, pages + 1)
        write_page_to_file(pages + 1, animes)

        outer_progress_bar.update(1)
    outer_progress_bar.close()


def create_anime_wikime():
    pass


if __name__ == "__main__":
    LAST_PAGE = int(sys.argv[1])
    session = Shikimori()
    api = session.get_api()

    get_animes(api, 50000)
