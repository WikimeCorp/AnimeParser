import aiohttp
import asyncio
import datetime
import json
from tqdm import tqdm
import sys


ADDR = "http://localhost:3030"


def anime_to_my_format(anime: dict):
    date = anime["aired_on"]
    if date is None:
        date = 0
        if anime["released_on"] is not None:
            date = anime["released_on"]
    if isinstance(date, str):
        date = int(
            datetime.datetime.strptime(date, "%Y-%m-%d")
            .replace(tzinfo=datetime.timezone.utc)
            .timestamp()
        )

    originTitle = (
        oTitle[0] if (oTitle := anime["english"]) != [] else "Empty english title"
    )
    if originTitle is None:
        originTitle = "Empty english title"

    description = (
        desc if (desc := anime["description"]) is not None else "Empty description"
    )

    director = (
        studios[0]["name"] if (studios := anime["studios"]) != [] else "No director"
    )

    average = anime["score"]

    ans = {
        "title": anime["name"],
        "originTitle": originTitle,
        "description": description,
        "director": director,
        "genres": list(map(lambda x: x["russian"], anime["genres"])),
        "releaseDate": date,
        "average": average,
    }
    return ans


def get_anime_list(page_num):
    dirty_anime_list = []
    with open(f"./animes/page_{page_num}.json", encoding="utf8") as f:
        dirty_anime_list = json.load(f)

    anime_list = []
    for i in dirty_anime_list:
        anime_list.append(anime_to_my_format(i))

    return anime_list


async def push_anime(session, anime: dict):

    async with session.post(
        ADDR + "/anime",
        json=anime,
        headers={"Content-Type": "application/json"},
    ) as resp:
        response = await resp.json()  # [2]

    av = {"average": float(anime["average"])}

    async with session.put(
        ADDR + f"/anime/{response['animeId']}",
        json=av,
        headers={"Content-Type": "application/json"},
    ) as resp:
        response = await resp.json()  # [2]


async def main():
    first_page = int(sys.argv[1])
    last_page = int(sys.argv[2])
    global count
    async with aiohttp.ClientSession() as session:
        arr = []
        for i in tqdm(range(first_page, last_page), desc="Pages"):
            anime_list = get_anime_list(i)
            array = []
            for anime in anime_list:
                array.append(push_anime(session, anime))
                # await asyncio.gather(*[push_anime(session, anime)])
            arr.extend(array)
        await asyncio.gather(*arr)


asyncio.run(main())
