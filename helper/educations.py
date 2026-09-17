# helper/educations.py
"""
Lab Muffin Beauty Science (https://labmuffin.com/) Education Scraper
Powered by Scrapling (https://github.com/d4vinci/Scrapling)
Supports multi-page pagination and full-article lazy scraping.
"""
import urllib.request
import re
from typing import Tuple, List, Dict, Any
from scrapling import Selector, Fetcher
from core.logger import log_action

BASE_URL = "https://labmuffin.com/"

def fetch_html_with_scrapling(url: str, timeout: int = 15) -> str:
    """Fetch HTML using Scrapling Fetcher with graceful fallback to urllib."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    try:
        response = Fetcher.get(url, headers=headers, timeout=timeout)
        if response.status == 200 and response.text:
            return response.text
    except Exception as e:
        log_action("scrap", f"Scrapling Fetcher fallback for {url}: {e}", level="warning")

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def get_educations_list(page_number: int = 1) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Scrape educational articles from Lab Muffin with pagination support."""
    url = f"{BASE_URL}page/{page_number}/" if page_number > 1 else BASE_URL
    log_action("scrap", f"Fetching Lab Muffin education feed from {url} using Scrapling...")

    try:
        html = fetch_html_with_scrapling(url)
    except Exception as e:
        log_action("scrap", f"Failed to fetch Lab Muffin page {page_number}: {e}", level="error")
        return [], {}

    doc = Selector(html)
    articles = doc.css("article.inside-article, article.post, article.hentry")
    log_action("scrap", f"Scrapling extracted {len(articles)} articles from Lab Muffin page {page_number}")

    posts_data = []
    for art in articles:
        title_el = art.css("h2.entry-title a, h2 a")
        title = title_el.css("::text").get()
        link = title_el.css("::attr(href)").get()

        if not title or not link:
            continue

        # Extract image (support lazy-load data-src, srcset, or standard src)
        img_el = art.css("div.post-image img, img.wp-post-image, img")
        img_src = (
            img_el.css("::attr(data-src)").get()
            or img_el.css("::attr(src)").get()
            or ""
        )
        if img_src.startswith("data:image"):
            # If base64/placeholder svg, try noscript or data-srcset
            noscript_img = art.css("noscript img::attr(src)").get()
            if noscript_img:
                img_src = noscript_img

        # Extract summary / snippet
        summary_el = art.css("div.entry-summary p, div.entry-content p")
        summary_text = summary_el.css("::text").get() if summary_el else ""

        # Extract date
        date_el = art.css("time.entry-date::text, time.published::text")
        date_str = date_el.get() if date_el else ""

        # Extract category
        cat_el = art.css("span.cat-links a::text, .entry-meta .cat-links::text")
        category = cat_el.get() if cat_el else "Skincare Science"

        posts_data.append({
            "Title": title.strip(),
            "Link": link.strip(),
            "Image": img_src.strip(),
            "Snippet": summary_text.strip() if summary_text else "",
            "Date": date_str.strip() if date_str else "",
            "Category": category.strip() if category else "Skincare Science"
        })

    pagination_info = {
        "Current_Page": str(page_number),
        "Prev_Page": str(page_number - 1) if page_number > 1 else None,
        "Next_Page": str(page_number + 1),
        "Current_Link": url
    }

    return posts_data, pagination_info

def get_educations_details(url: str) -> Dict[str, Any]:
    """Scrape full educational article content from Lab Muffin into structured Markdown."""
    log_action("scrap", f"Scraping Lab Muffin article detail from {url} using Scrapling...")
    html = fetch_html_with_scrapling(url)
    doc = Selector(html)

    # Title
    title = (
        doc.css("h1.entry-title::text").get()
        or doc.css("h1::text").get()
        or doc.css("meta[property='og:title']::attr(content)").get()
        or "Skincare Science Education"
    )

    # Author
    author = (
        doc.css("span.author a::text, .entry-meta .author::text").get()
        or "Dr Michelle Wong (Lab Muffin)"
    )

    # Date
    date = (
        doc.css("time.entry-date::text, time.published::text").get()
        or doc.css("meta[property='article:published_time']::attr(content)").get()
        or ""
    )

    # Cover Image
    cover_image = (
        doc.css("div.post-image img::attr(src)").get()
        or doc.css("meta[property='og:image']::attr(content)").get()
        or ""
    )

    # Extract Content and format to clean Markdown
    content_container = doc.css("article div.entry-content, div.entry-content")
    content_blocks = []

    if content_container:
        # Process paragraphs, headings, blockquotes, and lists
        elements = content_container.css("p, h2, h3, h4, blockquote, ul, ol")
        for el in elements:
            tag = el.tag
            # Skip promotional blocks and newsletters
            text = "".join(el.css("::text").getall()).strip()
            if not text:
                continue

            low_text = text.lower()
            if "subscribe to" in low_text or "mailerlite" in low_text or "cookie" in low_text:
                continue

            if tag == "h2":
                content_blocks.append(f"## {text}")
            elif tag == "h3":
                content_blocks.append(f"### {text}")
            elif tag == "h4":
                content_blocks.append(f"#### {text}")
            elif tag == "blockquote":
                content_blocks.append(f"> {text}")
            elif tag in ("ul", "ol"):
                list_items = el.css("li")
                for li in list_items:
                    li_text = "".join(li.css("::text").getall()).strip()
                    if li_text:
                        content_blocks.append(f"- {li_text}")
            else:
                content_blocks.append(text)

    markdown_text = "\n\n".join(content_blocks)
    if not markdown_text:
        # Fallback to general paragraph extraction
        all_p = [p.strip() for p in doc.css("p::text").getall() if len(p.strip()) > 30]
        markdown_text = "\n\n".join(all_p)

    return {
        "Title": title.strip(),
        "Author": author.strip(),
        "Date": date.strip(),
        "Cover_Image": cover_image.strip(),
        "Content": markdown_text
    }