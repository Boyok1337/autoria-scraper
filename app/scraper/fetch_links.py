import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count
from app.config import BASE_URL
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def page_has_listings(page: int) -> bool:
    url = f"{BASE_URL}?page={page}&countpage=100&indexName=auto&custom=1&abroad=2"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        has_listings = bool(soup.select("a.m-link-ticket"))
        logger.debug(f"Checked page {page}: {'has listings' if has_listings else 'no listings'}")
        return has_listings
    except Exception as e:
        logger.error(f"Error checking page {page}: {e}")
        return False


def get_total_pages_binary_search():
    logger.info("Starting binary search for total pages")
    low, high = 1, 100000
    last = 0
    while low <= high:
        mid = (low + high) // 2
        if page_has_listings(mid):
            last = mid
            low = mid + 1
        else:
            high = mid - 1
    logger.info(f"Total pages found: {last}")
    return last


def fetch_links_from_page(page: int) -> list[str]:
    url = f"{BASE_URL}?page={page}&countpage=100&indexName=auto&custom=1&abroad=2"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a['href'] for a in soup.select("a.m-link-ticket") if a.get("href")]
        logger.info(f"Fetched {len(links)} links from page {page}")
        return links
    except Exception as e:
        logger.error(f"Page {page} error: {e}")
        return []


def collect_all_links():
    logger.info("Collecting all links...")
    total_pages = get_total_pages_binary_search()
    with Pool(cpu_count()) as pool:
        results = pool.map(fetch_links_from_page, range(1, total_pages + 1))
    flat_links = [link for sublist in results for link in sublist]
    unique_links = list(set(flat_links))
    logger.info(f"Collected {len(unique_links)} unique links from {total_pages} pages")
    return unique_links
