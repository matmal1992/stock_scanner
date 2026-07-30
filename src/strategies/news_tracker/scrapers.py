import cloudscraper
from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

from src.core.utils import date_str_to_int
from src.strategies.news_tracker.entry_repo import NewsEntry


def get_html(url: str) -> str:
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "mobile": False,
        }
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    for attempt in range(3):
        try:
            response = scraper.get(
                url,
                headers=headers,
                timeout=20,
                allow_redirects=True,
            )

            if response.status_code == 200:
                return response.text

        except Exception:
            pass

    raise ValueError("Nie udało się pobrać strony")


def extract_text_bs4(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    article = soup.find("article")

    if article:
        raw_text = article.get_text(separator="\n")
    else:
        raw_text = soup.get_text(separator="\n")

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return "\n".join(lines)


def clean_text_for_llm(text: str) -> str:
    lines = text.splitlines()

    cleaned = []
    seen = set()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if len(line) < 30:
            continue

        if line in seen:
            continue

        seen.add(line)
        cleaned.append(line)

    return "\n\n".join(cleaned)


def accept_cookies(page: Page) -> bool:
    selectors = [
        "button:has-text('Zaakceptuj i zamknij')",
        "text=Zaakceptuj i zamknij",
        "[aria-label*='Zaakceptuj']",
        "button >> text=Zaakceptuj i zamknij",
    ]

    page.wait_for_timeout(5000)

    for selector in selectors:
        try:
            button = page.locator(selector).first

            if button.is_visible(timeout=2000):
                print("Klikam zgodę cookies:", selector)
                button.click()
                page.wait_for_timeout(2000)
                return True

        except Exception:
            pass

    print("Nie znaleziono bannera cookies")
    return False


def scrape_with_playwright() -> list[NewsEntry]:
    URL = "https://www.bankier.pl/gielda/wiadomosci/komunikaty-spolek"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000, wait_until="networkidle")
        accept_cookies(page)
        page.wait_for_selector("a.m-quotes-announcements-item__anchor")
        items = page.locator("li.m-quotes-announcements-list__item")

        entries: list[NewsEntry] = []
        count = min(items.count(), 5)

        for i in range(count):
            item = items.nth(i)

            date_str = item.locator("span.m-quotes-announcements-item__date").inner_text()
            title = item.locator("a.m-quotes-announcements-item__anchor").inner_text()
            link = item.locator("a.m-quotes-announcements-item__anchor").get_attribute("href")
            published = date_str_to_int(date_str)

            if not link:
                continue

            entries.append({"title": title, "link": link, "published": published, "source_type": "ESPI"})

        browser.close()

    return entries
