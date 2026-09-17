# helper/news.py
"""
BeautyJournal (https://www.beautyjournal.id/beauty-az) Skincare News & Beauty A-Z Scraper
Powered by Scrapling (https://github.com/d4vinci/Scrapling)
Supports infinite scroll pagination (skip/limit) and full article/glossary detail scraping.
"""
import urllib.request
import urllib.parse
import json
import re
from typing import List, Dict, Any, Optional
from scrapling import Selector, Fetcher
from core.logger import log_action

BASE_URL = "https://www.beautyjournal.id/beauty-az"
API_BASE = "https://bj-public-api.beautyjournal.id"
DEFAULT_COVER = "https://images.soco.id/beautyjournal/default-az.jpg"

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Origin": "https://www.beautyjournal.id",
    "Referer": "https://www.beautyjournal.id/beauty-az",
    "Accept": "application/json, text/html, */*"
}

def _fetch_api_json(url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """Fetch JSON from BeautyJournal public API using Scrapling Fetcher with urllib fallback."""
    try:
        response = Fetcher.get(url, headers=COMMON_HEADERS, timeout=timeout)
        if response.status == 200:
            if hasattr(response, "json"):
                try:
                    return response.json()
                except Exception:
                    pass
            if hasattr(response, "body") and response.body:
                return json.loads(response.body.decode("utf-8", errors="ignore"))
    except Exception as e:
        log_action("scrap", f"Scrapling Fetcher JSON fallback for {url}: {e}", level="warning")

    try:
        req = urllib.request.Request(url, headers=COMMON_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception as e:
        log_action("scrap", f"Failed to fetch JSON from {url}: {e}", level="error")
        return None

def _fetch_html_with_scrapling(url: str, timeout: int = 15) -> str:
    """Fetch HTML using Scrapling Fetcher with urllib fallback."""
    try:
        response = Fetcher.get(url, headers=COMMON_HEADERS, timeout=timeout)
        if response.status == 200:
            if hasattr(response, "text") and response.text:
                return response.text
            if hasattr(response, "body") and response.body:
                return response.body.decode("utf-8", errors="ignore")
    except Exception as e:
        log_action("scrap", f"Scrapling Fetcher HTML fallback for {url}: {e}", level="warning")

    req = urllib.request.Request(url, headers=COMMON_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def _html_to_markdown(html_content: str) -> str:
    """Parse HTML blocks into clean Markdown using Scrapling Selector."""
    if not html_content:
        return ""
    
    doc = Selector(html_content)
    elements = doc.css("p, h1, h2, h3, h4, h5, h6, blockquote, ul, ol, div.paragraph")
    content_blocks = []

    for el in elements:
        tag = el.tag
        text = "".join(el.css("::text").getall()).strip()
        if not text:
            continue

        low_text = text.lower()
        if "baca juga" in low_text or "cookie" in low_text or "subscribe" in low_text:
            continue

        if tag == "h1":
            content_blocks.append(f"# {text}")
        elif tag == "h2":
            content_blocks.append(f"## {text}")
        elif tag == "h3":
            content_blocks.append(f"### {text}")
        elif tag == "h4":
            content_blocks.append(f"#### {text}")
        elif tag in ("h5", "h6"):
            content_blocks.append(f"##### {text}")
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
        all_text = [t.strip() for t in doc.css("::text").getall() if len(t.strip()) > 10]
        markdown_text = "\n\n".join(all_text)

    return markdown_text

def get_news_list(page: int = 1, page_size: int = 15) -> Dict[str, Any]:
    """
    Retrieve BeautyJournal skincare news & beauty A-Z items.
    Handles the infinite scroll mechanism using skip & limit query parameters.
    """
    skip = (page - 1) * page_size
    api_url = f"{API_BASE}/glossary?limit={page_size}&skip={skip}"
    log_action("scrap", f"Fetching BeautyJournal infinite scroll feed (page={page}, skip={skip}, limit={page_size}) via Scrapling...")

    data = _fetch_api_json(api_url)
    article_list = []

    if data and data.get("success"):
        groups = data.get("data", {})
        # Data is returned as dictionary of alphabetical groups e.g. {"#": [...], "A": [...]}
        for _, items in groups.items():
            for item in items:
                title = item.get("title", "").strip()
                slug = item.get("slug", "").strip()
                if not title or not slug:
                    continue

                link = f"https://www.beautyjournal.id/beauty-az/{slug}"
                
                # Extract image
                images = item.get("images") or []
                img_url = DEFAULT_COVER
                for img_obj in images:
                    if isinstance(img_obj, dict) and img_obj.get("url"):
                        img_url = img_obj.get("url")
                        if img_obj.get("is_cover"):
                            break

                # Extract date
                raw_date = str(item.get("published_at") or item.get("created_at") or "")
                date_str = raw_date[:10] if raw_date else ""

                # Extract category / tag
                tags = item.get("tags") or []
                category = tags[0].get("name") if (tags and isinstance(tags[0], dict)) else "Beauty A-Z"

                summary = item.get("summary") or ""
                if not summary and item.get("content"):
                    summary = _html_to_markdown(item.get("content"))[:200]

                article_list.append({
                    "Title": title,
                    "Link": link,
                    "Image": img_url,
                    "Date": date_str,
                    "Category": category,
                    "Snippet": summary.strip()
                })

    log_action("scrap", f"BeautyJournal extracted {len(article_list)} items for page {page}")

    paginations = {
        "Current_Page": str(page),
        "Prev_Page": str(page - 1) if page > 1 else None,
        "Next_Page": str(page + 1) if len(article_list) >= page_size else None,
        "Limit": page_size,
        "Skip": skip
    }

    return {
        "Article_List": article_list,
        "Pagination": paginations
    }

def get_news(url: str) -> List[Dict[str, Any]]:
    """
    Retrieve full article or glossary detail from BeautyJournal or external URL.
    Returns a list with a single dictionary for compatibility with NewsService.
    """
    log_action("scrap", f"Fetching article detail for {url} via Scrapling...")
    slug = url.rstrip("/").split("/")[-1].split("?")[0]

    # 1. Try BeautyJournal Glossary API by slug filter
    glossary_filter = urllib.parse.quote(json.dumps({"slug": slug}))
    glossary_api = f"{API_BASE}/glossary?filter={glossary_filter}&limit=1"
    glossary_data = _fetch_api_json(glossary_api)

    if glossary_data and glossary_data.get("success"):
        data_dict = glossary_data.get("data", {})
        for _, items in data_dict.items():
            if items and len(items) > 0:
                item = items[0]
                title = item.get("title", "")
                
                # Image
                images = item.get("images") or []
                cover_image = DEFAULT_COVER
                for img_obj in images:
                    if isinstance(img_obj, dict) and img_obj.get("url"):
                        cover_image = img_obj.get("url")
                        if img_obj.get("is_cover"):
                            break

                raw_date = str(item.get("published_at") or item.get("created_at") or "")
                date_str = raw_date[:10] if raw_date else ""
                author = item.get("owner", {}).get("name") if isinstance(item.get("owner"), dict) else "Beauty Journal Editorial"
                
                raw_html = item.get("content") or item.get("summary") or ""
                markdown_content = _html_to_markdown(raw_html)

                return [{
                    "Title": title,
                    "Cover_Image": cover_image,
                    "ImageUrl": cover_image,
                    "Date": date_str,
                    "Source": "BeautyJournal",
                    "Author": author,
                    "Content": markdown_content
                }]

    # 2. Try BeautyJournal Posts API (editorial articles)
    post_filter = urllib.parse.quote(json.dumps({"slug": slug}))
    posts_api = f"{API_BASE}/posts?filter={post_filter}&limit=1"
    posts_data = _fetch_api_json(posts_api)

    if posts_data and posts_data.get("success") and posts_data.get("data"):
        p = posts_data["data"][0]
        title = p.get("title", "")
        author = p.get("owner", {}).get("name", "Beauty Journal Editorial") if isinstance(p.get("owner"), dict) else "Beauty Journal Editorial"
        date_str = str(p.get("published_at", ""))[:10]
        cover_image = p.get("attachments", {}).get("featured_image", DEFAULT_COVER) if isinstance(p.get("attachments"), dict) else DEFAULT_COVER
        raw_html = p.get("content", "")
        markdown_content = _html_to_markdown(raw_html)

        return [{
            "Title": title,
            "Cover_Image": cover_image,
            "ImageUrl": cover_image,
            "Date": date_str,
            "Source": "BeautyJournal",
            "Author": author,
            "Content": markdown_content
        }]

    # 3. Fallback: Direct HTML scraping via Scrapling Selector
    try:
        html = _fetch_html_with_scrapling(url)
        doc = Selector(html)
        title = (
            doc.css("h1.read__title::text, h1.entry-title::text, h1::text").get()
            or doc.css("meta[property='og:title']::attr(content)").get()
            or "Skincare Article"
        )
        cover_image = (
            doc.css("meta[property='og:image']::attr(content)").get()
            or doc.css("div.photo__wrap img::attr(src), img.wp-post-image::attr(src)").get()
            or DEFAULT_COVER
        )
        date_str = (
            doc.css("meta[property='article:published_time']::attr(content)").get()
            or doc.css("time::text").get()
            or ""
        )
        author = (
            doc.css("div.credit-title-nameEditor::text, span.author::text, meta[name='author']::attr(content)").get()
            or "Beauty Journal Editorial"
        )
        markdown_content = _html_to_markdown(html)

        return [{
            "Title": title.strip(),
            "Cover_Image": cover_image.strip(),
            "ImageUrl": cover_image.strip(),
            "Date": date_str[:10] if date_str else "",
            "Source": "BeautyJournal",
            "Author": author.strip(),
            "Content": markdown_content
        }]
    except Exception as e:
        log_action("scrap", f"Direct HTML scraping failed for {url}: {e}", level="error")
        return []