import asyncio

from apscheduler.schedulers.blocking import BlockingScheduler

from app.scraper.fetch_details import process_links
from app.scraper.fetch_links import collect_all_links
from app.db import Base, engine
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
SCRAPE_TIME_HOUR = os.getenv('SCRAPE_TIME_HOUR', 12)


def dump_db():
    dt = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.system(f"pg_dump -U postgres -h db -d autos > dumps/dump_{dt}.sql")


async def run():
    Base.metadata.create_all(bind=engine)
    links = collect_all_links()
    await process_links(links)
    dump_db()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(main, 'cron', hour=int(SCRAPE_TIME_HOUR), minute=0)
    scheduler.start()
