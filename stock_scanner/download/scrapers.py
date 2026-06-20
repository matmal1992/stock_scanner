import cloudscraper
from bs4 import BeautifulSoup
from newspaper import Article


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


def extract_text_newspaper(url: str) -> str:
    article = Article(url)
    article.download()
    article.parse()
    return article.text


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
