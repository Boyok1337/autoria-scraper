import asyncio
import time
import logging
from datetime import datetime
import re

import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.models import Car
from app.db import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}


async def fetch_phone_playwright(url: str) -> str:
    logger.info(f"Fetching phone number from {url} using Playwright")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(url, timeout=6000, wait_until="domcontentloaded")

            phones_block = await page.wait_for_selector(
                'div#phonesBlock div.phones_item span.phone',
                timeout=6000
            )

            await phones_block.click()
            time.sleep(2)

            phone_number = await phones_block.get_attribute("data-phone-number")
            if not phone_number:
                phone_number = (await phones_block.inner_text()).strip()

            await browser.close()
            logger.info(f"Phone number found: {phone_number}")
            return phone_number
    except Exception as e:
        logger.error(f"Error fetching phone number from {url}: {e}")
        return ""


async def fetch(session, url):
    try:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                logger.info(f"Successfully fetched URL: {url}")
                return url, await response.text()
            else:
                logger.warning(f"Non-200 response ({response.status}) from URL: {url}")
                return url, None
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return url, None


async def parse(html, url):
    logger.info(f"Parsing URL: {url}")
    soup = BeautifulSoup(html, "html.parser")

    def extract(sel, regex=None, transform=None):
        el = soup.select_one(sel)
        if not el:
            return None
        text = el.get_text(strip=True).replace('\xa0', '')
        if regex:
            match = re.search(regex, text)
            return transform(match.group(1)) if match else None
        return transform(text) if transform else text

    # phone_number = await fetch_phone_playwright(url)
    phone_number = ""

    image_url = ""
    img = soup.select_one('.carousel-inner img')
    if img and img.get('src'):
        image_url = img['src']

    car = Car(
        url=url,
        title=extract("h1.head"),
        price_usd=extract("div.price_value strong", r"(\d[\d\s]*)", lambda x: int(x.replace(" ", ""))),
        odometer=extract("div.base-information.bold", r"(\d+)", lambda x: int(x) * 1000),
        username=extract("div.seller_info_name"),
        phone_number=phone_number,
        image_url=image_url,
        images_count=extract("a.show-all.link-dotted", r"(\d+)", int),
        car_number=extract("span.state-num"),
        car_vin=extract("span.label-vin"),
        datetime_found=datetime.utcnow()
    )

    logger.info(f"Parsed car: {car.title} - {car.price_usd}$")
    return car


async def process_links(links):
    logger.info(f"Starting to process {len(links)} links")
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in links]
        results = await asyncio.gather(*tasks)

        db = SessionLocal()
        success_count = 0
        for url, html in results:
            if html:
                car = await parse(html, url)
                if car:
                    db.merge(car)
                    success_count += 1
        db.commit()
        db.close()
        logger.info(f"Finished processing. Successfully saved {success_count} cars to the database.")
