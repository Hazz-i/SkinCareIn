# tests/test_scrapling_scrapers.py
"""
Unit tests for Scrapling-powered scrapers:
- Lab Muffin Beauty Science (Education) with multi-page pagination
- BeautyJournal (News & Beauty A-Z) with infinite scroll pagination (skip/limit)
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch, MagicMock
from helper.educations import get_educations_list, get_educations_details
from helper.news import get_news_list, get_news

MOCK_LABMUFFIN_HTML = """
<html>
<body>
    <article class="inside-article">
        <div class="post-image">
            <img src="https://labmuffin.com/wp-content/uploads/sunscreen.jpg" alt="Sunscreen"/>
        </div>
        <header class="entry-header">
            <h2 class="entry-title"><a href="https://labmuffin.com/how-sunscreen-works/">How Sunscreen Works</a></h2>
            <div class="entry-meta">
                <span class="cat-links"><a href="#">Sunscreen Science</a></span>
                <time class="entry-date">September 15, 2026</time>
            </div>
        </header>
        <div class="entry-summary">
            <p>A deep dive into sunscreen filters and UV protection science.</p>
        </div>
    </article>
</body>
</html>
"""

MOCK_LABMUFFIN_DETAIL_HTML = """
<html>
<body>
    <article>
        <h1 class="entry-title">How Sunscreen Works</h1>
        <div class="entry-meta">
            <span class="author"><a href="#">Dr Michelle Wong</a></span>
            <time class="entry-date">September 15, 2026</time>
        </div>
        <div class="post-image">
            <img src="https://labmuffin.com/wp-content/uploads/sunscreen.jpg" />
        </div>
        <div class="entry-content">
            <h2>Introduction</h2>
            <p>Sunscreen is crucial for skin protection against UV radiation.</p>
            <h3>Key Takeaways</h3>
            <ul>
                <li>UVA causes aging</li>
                <li>UVB causes burning</li>
            </ul>
            <blockquote>Always wear SPF daily.</blockquote>
        </div>
    </article>
</body>
</html>
"""

MOCK_BJ_GLOSSARY_JSON = {
    "success": True,
    "data": {
        "N": [
            {
                "_id": "60123456789abcdef",
                "title": "Niacinamide",
                "slug": "niacinamide",
                "summary": "Vitamin B3 derivative that helps with pores and skin barrier.",
                "content": "<p>Niacinamide is a potent active ingredient.</p><h2>Benefits</h2><p>Improves elasticity and calms redness.</p>",
                "images": [
                    {
                        "url": "https://images.soco.id/beautyjournal/niacinamide.jpg",
                        "is_cover": True
                    }
                ],
                "tags": [{"name": "Active Ingredients"}],
                "owner": {"name": "Beauty Journal Science"},
                "published_at": "2026-08-10T10:00:00.000Z"
            }
        ]
    }
}

def test_labmuffin_list_scraping():
    with patch("helper.educations.fetch_html_with_scrapling", return_value=MOCK_LABMUFFIN_HTML):
        articles, pagination = get_educations_list(page_number=2)
        assert len(articles) == 1
        art = articles[0]
        assert art["Title"] == "How Sunscreen Works"
        assert art["Link"] == "https://labmuffin.com/how-sunscreen-works/"
        assert art["Image"] == "https://labmuffin.com/wp-content/uploads/sunscreen.jpg"
        assert art["Date"] == "September 15, 2026"
        assert art["Category"] == "Sunscreen Science"
        assert "A deep dive" in art["Snippet"]

        assert pagination["Current_Page"] == "2"
        assert pagination["Prev_Page"] == "1"
        assert pagination["Next_Page"] == "3"

def test_labmuffin_detail_scraping():
    with patch("helper.educations.fetch_html_with_scrapling", return_value=MOCK_LABMUFFIN_DETAIL_HTML):
        detail = get_educations_details("https://labmuffin.com/how-sunscreen-works/")
        assert detail["Title"] == "How Sunscreen Works"
        assert "Dr Michelle Wong" in detail["Author"]
        assert detail["Cover_Image"] == "https://labmuffin.com/wp-content/uploads/sunscreen.jpg"
        assert "## Introduction" in detail["Content"]
        assert "### Key Takeaways" in detail["Content"]
        assert "- UVA causes aging" in detail["Content"]
        assert "> Always wear SPF daily." in detail["Content"]

def test_beautyjournal_list_infinite_scroll():
    with patch("helper.news._fetch_api_json", return_value=MOCK_BJ_GLOSSARY_JSON):
        # Page 2 with page_size=15 -> skip=15, limit=15
        result = get_news_list(page=2, page_size=15)
        articles = result["Article_List"]
        pagination = result["Pagination"]

        assert len(articles) == 1
        item = articles[0]
        assert item["Title"] == "Niacinamide"
        assert item["Link"] == "https://www.beautyjournal.id/beauty-az/niacinamide"
        assert item["Image"] == "https://images.soco.id/beautyjournal/niacinamide.jpg"
        assert item["Category"] == "Active Ingredients"
        assert item["Date"] == "2026-08-10"

        assert pagination["Current_Page"] == "2"
        assert pagination["Prev_Page"] == "1"
        assert pagination["Skip"] == 15
        assert pagination["Limit"] == 15

def test_beautyjournal_detail_scraping():
    with patch("helper.news._fetch_api_json", return_value=MOCK_BJ_GLOSSARY_JSON):
        news = get_news("https://www.beautyjournal.id/beauty-az/niacinamide")
        assert len(news) == 1
        item = news[0]
        assert item["Title"] == "Niacinamide"
        assert item["Cover_Image"] == "https://images.soco.id/beautyjournal/niacinamide.jpg"
        assert item["Source"] == "BeautyJournal"
        assert item["Author"] == "Beauty Journal Science"
        assert "## Benefits" in item["Content"]
        assert "Improves elasticity" in item["Content"]

if __name__ == "__main__":
    test_labmuffin_list_scraping()
    print("[PASS] test_labmuffin_list_scraping passed")
    test_labmuffin_detail_scraping()
    print("[PASS] test_labmuffin_detail_scraping passed")
    test_beautyjournal_list_infinite_scroll()
    print("[PASS] test_beautyjournal_list_infinite_scroll passed")
    test_beautyjournal_detail_scraping()
    print("[PASS] test_beautyjournal_detail_scraping passed")
    print("\nAll Scrapling scraper tests passed successfully!")
