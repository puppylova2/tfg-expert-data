"""
Crawls the public TerraFirmaGreg wiki (Field Guide, Recipe Book, Quest Book)
and saves all page text as JSON. This site is public, so this is a normal,
polite crawl (small delay between requests, respects a page-count limit).

Run with: python crawl_wiki.py
Output:   data/wiki.json
"""

import json
import time
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

START_URLS = [
    "https://wiki.terrafirmagreg.team/modern/field-guide",
    "https://wiki.terrafirmagreg.team/modern/recipe-book",
    "https://wiki.terrafirmagreg.team/modern/quest-book",
]
ALLOWED_DOMAIN = "wiki.terrafirmagreg.team"
MAX_PAGES = 5000          # safety cap so a bug can't crawl forever
DELAY_SECONDS = 0.5       # be polite to the server
OUTPUT_PATH = "data/wiki.json"

HEADERS = {
    "User-Agent": "TFG-Expert-Bot/1.0 (personal project, respectful crawl)"
}


def clean_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def crawl():
    seen = set()
    queue = deque(START_URLS)
    pages = []

    while queue and len(pages) < MAX_PAGES:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  ! skip {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else url

        pages.append({
            "url": url,
            "title": title,
            "text": clean_text(soup),
        })
        print(f"  + crawled ({len(pages)}): {url}")

        for link in soup.find_all("a", href=True):
            next_url = urljoin(url, link["href"])
            parsed = urlparse(next_url)
            next_url = next_url.split("#")[0]  # drop in-page anchors
            if (
                parsed.netloc == ALLOWED_DOMAIN
                and next_url not in seen
                and next_url not in queue
            ):
                queue.append(next_url)

        time.sleep(DELAY_SECONDS)

    return pages


if __name__ == "__main__":
    print("Crawling TerraFirmaGreg wiki...")
    pages = crawl()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    print(f"Done. Saved {len(pages)} pages to {OUTPUT_PATH}")
