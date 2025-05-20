import asyncio
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import re
import time

DB_NAME = "cars.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            url TEXT PRIMARY KEY,
            title TEXT,
            price_usd INTEGER,
            odometer INTEGER,
            username TEXT,
            phone_number TEXT,
            images_count INTEGER,
            car_number TEXT,
            car_vin TEXT,
            datetime_found TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO cars
        (url, title, price_usd, odometer, username, phone_number, images_count, car_number, car_vin, datetime_found)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["url"],
        data["title"],
        data["price_usd"],
        data["odometer"],
        data["username"],
        data["phone_number"],
        data["images_count"],
        data["car_number"],
        data["car_vin"],
        data["datetime_found"]
    ))
    conn.commit()
    conn.close()


async def fetch(session: ClientSession, url: str):
    print(f"🔎 Fetching: {url}")
    try:
        async with session.get(url, headers=HEADERS, timeout=30) as response:
            html = await response.text()
            print(f"✅ Fetched: {url}")
            return url, html
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return url, None


def parse(html: str, url: str):
    soup = BeautifulSoup(html, "html.parser")

    def extract(selector, attr=None, regex=None, transform=None):
        el = soup.select_one(selector)
        if not el:
            return None
        text = el.get(attr) if attr else el.get_text(strip=True)
        if regex:
            match = re.search(regex, text.replace('\xa0', ''))
            return transform(match.group(1)) if match else None
        return transform(text) if transform else text

    title = extract("h1.head")
    price_usd = extract("div.price_value strong", regex=r"(\d[\d\s]*)", transform=lambda x: int(x.replace(" ", "")))
    odometer = extract("div.base-information.bold", regex=r"(\d+)", transform=lambda x: int(x) * 1000)
    username = extract("div.seller_info_name")
    phone_number = extract("span.phone")
    images_count = extract("a.show-all.link-dotted", regex=r"(\d+)", transform=int)
    car_vin = extract("span.label-vin")
    car_number = None

    print(f"🔍 Parsed: title={title}, price={price_usd}, odo={odometer}, phone={phone_number}")

    return {
        "url": url,
        "title": title,
        "price_usd": price_usd,
        "odometer": odometer,
        "username": username,
        "phone_number": phone_number,
        "images_count": images_count,
        "car_number": car_number,
        "car_vin": car_vin,
        "datetime_found": datetime.now().isoformat()
    }


async def worker(name, queue: asyncio.Queue, session: ClientSession):
    while True:
        url = await queue.get()
        print(f"👷‍♂️ {name} processing: {url} (Remaining: {queue.qsize()})")
        url, html = await fetch(session, url)
        if html:
            try:
                data = parse(html, url)
                save_to_db(data)
                print(f"✅ {name}: Saved {data['title']}")
            except Exception as e:
                print(f"❌ {name}: Error parsing/saving {url}: {e}")
        else:
            print(f"⚠️ {name}: Failed to fetch HTML for {url}")
        queue.task_done()


async def main():
    init_db()
    with open("all_links.txt", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip().startswith("https://")]

    print(f"📋 Total links to process: {len(links)}")

    queue = asyncio.Queue()
    for link in links:
        queue.put_nowait(link)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(20):  # 20 workers
            task = asyncio.create_task(worker(f"Worker-{i+1}", queue, session))
            tasks.append(task)

        start_time = time.time()
        await queue.join()
        end_time = time.time()

        print(f"🏁 All tasks done in {end_time - start_time:.2f} seconds")

        for task in tasks:
            task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
