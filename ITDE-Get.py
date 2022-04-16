import zipfile
import shutil
from aiohttp import ClientSession
import os
import json
import asyncio, aiofiles
from glob import glob
from os import system
from urllib.parse import unquote
from bs4 import BeautifulSoup

print("Starting Up!")

URL = "https://www.incometax.gov.in/iec/foportal/downloads"
PAGE_DL_DIR = "fportal-downloads"
DATA_DL_DIR = "uploads"
TEMP_DL_DIR = "tmp"
BASE_GIT = "https://github.com/New-dev0/ITDE-Get/tree/main/"
DL_GIT = "https://github.com/New-dev0/ITR-Get/raw/main/"

if not os.path.exists(PAGE_DL_DIR):
    print("Creating Download Directory..")
    os.mkdir(PAGE_DL_DIR)

if not os.path.exists(DATA_DL_DIR):
    print("Making Upload dir")
    os.mkdir(DATA_DL_DIR)

if not os.path.exists(TEMP_DL_DIR):
    os.mkdir(TEMP_DL_DIR)

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def get(url):
    async with ClientSession() as seS:
        async with seS.get(url) as out:
            return await out.read()


async def write_file(content, name):
    file = await aiofiles.open(name, "wb")
    await file.write(content)
    await file.close()
    return name


async def download(file, Path):
    dirname = file.text.strip()
    name = TEMP_DL_DIR + "/" + unquote(file["href"].split("/")[-1])

    print(f">> Downloading {name}")
    await write_file(await get(file["href"]), name)
    ORIG_PATH = f"{Path}/{dirname}"

    if os.path.exists(ORIG_PATH):
        system(f"rm -rf '{ORIG_PATH}'")
    os.mkdir(ORIG_PATH)

    if name.endswith((".zip")):
        with zipfile.ZipFile(name) as file:
            file.extractall(ORIG_PATH)
    else:
        shutil.move(name, ORIG_PATH)

    for JsonPath in glob(ORIG_PATH + "/**/latest.json"):
        open(JsonPath, "w").write(json.dumps(json.load(open(JsonPath, "r")), indent=1))

    os.remove(name)
    print(f">>> Finished Extracting {name}")


async def main():
    print("Getting ITR Downloads Page...")
    PAGE_CONTENT = await get(URL)

    await write_file(PAGE_CONTENT, PAGE_DL_DIR + "/downloads.html")

    BS4Client = BeautifulSoup(PAGE_CONTENT, "html.parser", from_encoding="utf-8")

    for Row in BS4Client.find_all("div", "views-row")[1:]:
        Header = Row.find("div", "views-field-title").text.strip()
        Files = Row.find_all("a", "file-download")
        if not Files:
            print(f"{Header} having no Files...")
            continue
        print("# Taking up", Header)
        TASKS = []
        MainPath = DATA_DL_DIR + "/" + Header
        if not os.path.exists(MainPath):
            os.mkdir(MainPath)

        for File in Files:
            TASKS.append(download(File, MainPath))
        await asyncio.gather(*TASKS)


asyncio.run(main())

# Clean Up After Work
os.removedirs(TEMP_DL_DIR)
