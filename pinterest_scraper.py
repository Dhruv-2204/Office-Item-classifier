#!/usr/bin/env python3
"""Simple Pinterest image scraper.

This script attempts to download images for a given search query from
Pinterest and save them into an output directory.

Notes:
- Pinterest is dynamic and may block automated scraping. This script
  uses requests + BeautifulSoup to find image URLs exposed in the
  initial HTML. If that fails, there is an optional Selenium mode.
- Use responsibly and follow Pinterest's Terms of Service.
"""

import argparse
import os
import sys
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
tqdm_available = True
try:
    from tqdm import tqdm
except Exception:
    tqdm_available = False


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
    )
}


def query_url(query: str) -> str:
    return f"https://www.pinterest.com/search/pins/?q={requests.utils.requote_uri(query)}"


def gather_image_urls_requests(query: str, max_images: int = 50):
    """Try to fetch image URLs using requests + BeautifulSoup from initial HTML."""
    url = query_url(query)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Pinterest puts image urls into <img> tags as src or data-src, and
    # sometimes as background-image in inline styles. We'll collect them.
    urls = []
    for img in soup.find_all("img"):
        for attr in ("src", "data-src", "data-image-url"):
            v = img.get(attr)
            if v and v.startswith("http"):
                urls.append(v)
    # Also search for JSON blobs that might contain images
    for script in soup.find_all("script"):
        if not script.string:
            continue
        text = script.string
        # quick heuristic: look for "url":"https://i.pinimg.com"
        if "i.pinimg.com" in text:
            parts = text.split('"')
            for p in parts:
                if p.startswith("https://") and ("pinimg.com" in p or p.endswith(('.jpg', '.png', '.webp'))):
                    urls.append(p)

    # dedupe while preserving order
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
        if len(out) >= max_images:
            break
    return out


def download_image(url: str, out_dir: Path, session: requests.Session = None, timeout: int = 30):
    s = session or requests
    resp = s.get(url, headers=HEADERS, stream=True, timeout=timeout)
    resp.raise_for_status()
    # determine extension
    parsed = urlparse(url)
    name = os.path.basename(parsed.path)
    ext = os.path.splitext(name)[1]
    if not ext:
        # fallback to jpg
        ext = ".jpg"

    # use sha1 to create stable unique names based on url
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()
    filename = f"{h}{ext}"
    out_path = out_dir / filename
    # write file
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(1024 * 8):
            if chunk:
                f.write(chunk)
    return out_path


def ensure_out_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Download Pinterest images for a query")
    parser.add_argument("query", help="Search query / prompt")
    parser.add_argument("--limit", "-n", type=int, default=50, help="Maximum images to download")
    parser.add_argument("--out", "-o", default=r"C:\Users\dylan\Documents\Computer science\Computer Science Year 3\temp\pinterest shit", help="Output directory")
    parser.add_argument("--use-selenium", action="store_true", help="Use Selenium fallback (requires webdriver) if requests fails")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between downloads in seconds")
    args = parser.parse_args()

    out_dir = Path(args.out)
    ensure_out_dir(out_dir)

    try:
        urls = gather_image_urls_requests(args.query, max_images=args.limit)
    except Exception as e:
        print(f"Requests fetch failed: {e}")
        urls = []

    if not urls and args.use_selenium:
        print("Selenium fallback requested but not implemented in this script. Please enable or implement Selenium mode.")

    if not urls:
        print("No image URLs found. Pinterest often requires a browser; try using Selenium or adjusting query.")
        sys.exit(1)

    session = requests.Session()
    it = urls
    if tqdm_available:
        it = tqdm(urls, desc="Downloading")

    downloaded = []
    for u in it:
        try:
            p = download_image(u, out_dir, session=session)
            downloaded.append(str(p))
        except Exception as e:
            print(f"Failed to download {u}: {e}")
        time.sleep(args.delay)

    print(f"Downloaded {len(downloaded)} images to {out_dir}")


if __name__ == "__main__":
    main()
