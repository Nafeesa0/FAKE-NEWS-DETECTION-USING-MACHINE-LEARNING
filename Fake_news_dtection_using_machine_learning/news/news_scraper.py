"""
News Scraper — RSS-based real article fetcher.

Strategy: use RSS feed content directly (title + description + full content
where available). Full-page fetching is attempted as an optional enhancement
but the scraper works correctly even if every page fetch fails — BBC and CNN
actively block bots, so RSS-only is the reliable baseline.

Sources:
  - BBC News            (description in RSS, ~200-400 chars per article)
  - CNN                 (description in RSS, ~100-300 chars)
  - The Guardian        (full article text in RSS via <content:encoded>)
  - Reuters             (description in RSS, ~150-300 chars)
  - Al Jazeera English  (description in RSS, ~200-400 chars)
  - NPR News            (description + content in RSS)
"""

import requests
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

# ── RSS feed registry ─────────────────────────────────────────────────────
# (feed_url, source_name, default_category)
RSS_FEEDS = [
    # BBC News
    ('https://feeds.bbci.co.uk/news/world/rss.xml',                    'BBC News',       'world'),
    ('https://feeds.bbci.co.uk/news/technology/rss.xml',               'BBC News',       'technology'),
    ('https://feeds.bbci.co.uk/news/business/rss.xml',                 'BBC News',       'business'),
    ('https://feeds.bbci.co.uk/news/health/rss.xml',                   'BBC News',       'health'),
    ('https://feeds.bbci.co.uk/news/science_and_environment/rss.xml',  'BBC News',       'science'),
    ('https://feeds.bbci.co.uk/news/politics/rss.xml',                 'BBC News',       'politics'),
    # CNN (active feeds only)
    ('http://rss.cnn.com/rss/edition.rss',                             'CNN',            'world'),
    ('http://rss.cnn.com/rss/edition_technology.rss',                  'CNN',            'technology'),
    ('http://rss.cnn.com/rss/money_news_international.rss',            'CNN',            'business'),
    ('http://rss.cnn.com/rss/edition_us.rss',                          'CNN',            'politics'),
    ('http://rss.cnn.com/rss/edition_world.rss',                       'CNN',            'world'),
    # The Guardian — includes full article text in <content:encoded>
    ('https://www.theguardian.com/world/rss',                          'The Guardian',   'world'),
    ('https://www.theguardian.com/technology/rss',                     'The Guardian',   'technology'),
    ('https://www.theguardian.com/us-news/rss',                        'The Guardian',   'politics'),
    ('https://www.theguardian.com/science/rss',                        'The Guardian',   'science'),
    # Reuters - feeds discontinued as of 2026, removed to prevent errors
    # Alternative: Use Google News RSS for Reuters articles:
    # ('https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com&ceid=US:en&hl=en-US&gl=US', 'Reuters', 'world'),
    # Al Jazeera English
    ('https://www.aljazeera.com/xml/rss/all.xml',                      'Al Jazeera',     'world'),
    # NPR News
    ('https://feeds.npr.org/1001/rss.xml',                             'NPR News',       'world'),
    ('https://feeds.npr.org/1019/rss.xml',                             'NPR News',       'politics'),
    ('https://feeds.npr.org/1045/rss.xml',                             'NPR News',       'technology'),
]

# XML namespaces used by some feeds (Guardian content:encoded, media, dc)
NS = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'media':   'http://search.yahoo.com/mrss/',
    'dc':      'http://purl.org/dc/elements/1.1/',
    'atom':    'http://www.w3.org/2005/Atom',
}

CATEGORY_KEYWORDS = {
    'technology': ['tech', 'software', 'ai', 'digital', 'cyber', 'data', 'internet', 'app', 'robot', 'computer'],
    'health':     ['health', 'medical', 'disease', 'vaccine', 'hospital', 'doctor', 'mental', 'cancer', 'drug', 'covid'],
    'business':   ['business', 'economy', 'market', 'finance', 'stock', 'trade', 'bank', 'inflation', 'gdp', 'recession'],
    'politics':   ['politic', 'government', 'election', 'parliament', 'minister', 'president', 'senate', 'vote', 'congress'],
    'science':    ['science', 'research', 'study', 'discovery', 'space', 'climate', 'environment', 'nasa', 'fossil'],
    'world':      ['war', 'conflict', 'international', 'global', 'crisis', 'diplomacy', 'sanction', 'refugee'],
}

REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}
REQUEST_TIMEOUT  = 8    # seconds per HTTP request (reduced from 12)
MIN_CONTENT_LEN  = 40   # minimum chars — RSS descriptions are short but valid
MAX_CONTENT_LEN  = 5000 # cap to avoid huge Guardian articles overwhelming the model


# ── Helpers ───────────────────────────────────────────────────────────────

def _infer_category(text, default='world'):
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return default


def _parse_date(date_str):
    """Parse date string and return timezone-aware datetime in UTC."""
    if not date_str:
        return None
    try:
        # parsedate_to_datetime already returns timezone-aware datetime
        dt = parsedate_to_datetime(date_str)
        # Convert to UTC if needed
        from datetime import timezone as tz
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tz.utc)
        return dt.astimezone(tz.utc)
    except Exception:
        try:
            # Handle ISO format dates
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            from datetime import timezone as tz
            if dt.tzinfo is None:
                return dt.replace(tzinfo=tz.utc)
            return dt.astimezone(tz.utc)
        except Exception:
            return None


def _clean_html(raw):
    """Strip HTML tags and normalise whitespace."""
    if not raw:
        return ''
    text = BeautifulSoup(raw, 'html.parser').get_text(' ', strip=True)
    # Collapse multiple spaces/newlines
    import re
    return re.sub(r'\s+', ' ', text).strip()


def _fetch_xml(url):
    """Fetch RSS/Atom XML. Returns ElementTree root or None."""
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code in (404, 410):
            logger.debug(f"RSS feed gone ({resp.status_code}), skipping: {url}")
            return None
        resp.raise_for_status()

        # Handle empty responses
        if not resp.content:
            logger.warning(f"Empty response from {url}")
            return None

        return ET.fromstring(resp.content)
    except requests.Timeout:
        logger.warning(f"Timeout fetching RSS feed: {url}")
        return None
    except requests.ConnectionError as exc:
        logger.warning(f"Connection error for {url}: {exc}")
        return None
    except requests.HTTPError as exc:
        logger.debug(f"RSS HTTP error [{url}]: {exc}")
        return None
    except ET.ParseError as exc:
        logger.warning(f"XML parse error for {url}: {exc}")
        return None
    except Exception as exc:
        logger.warning(f"RSS fetch failed [{url}]: {exc}")
        return None


def _extract_item_text(item):
    """
    Pull the richest available text from an RSS <item>.
    Priority: content:encoded > description > summary
    Returns cleaned plain text.
    """
    # 1. content:encoded (Guardian, NPR, some Reuters)
    # Try with namespace prefix first
    ce = item.find(f"{{{NS['content']}}}encoded")
    if ce is None:
        # Try without namespace (some feeds don't use it properly)
        for child in item:
            if child.tag.endswith('encoded') or child.tag == 'encoded':
                ce = child
                break

    if ce is not None and ce.text:
        text = _clean_html(ce.text)
        if len(text) >= MIN_CONTENT_LEN:
            return text[:MAX_CONTENT_LEN]

    # 2. <description>
    desc_el = item.find('description')
    if desc_el is not None and desc_el.text:
        text = _clean_html(desc_el.text)
        if len(text) >= MIN_CONTENT_LEN:
            return text[:MAX_CONTENT_LEN]

    # 3. <summary> (some Atom-style RSS)
    summary_el = item.find('summary')
    if summary_el is not None and summary_el.text:
        text = _clean_html(summary_el.text)
        if len(text) >= MIN_CONTENT_LEN:
            return text[:MAX_CONTENT_LEN]

    return ''


def _try_fetch_article_page(url):
    """
    Optionally fetch the full article page for richer content.
    Returns text or None — failure is always silent (BBC/CNN block bots).
    """
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code != 200:
            return None

        # Handle empty responses
        if not resp.content:
            return None

        soup = BeautifulSoup(resp.content, 'html.parser')

        for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                         'aside', 'noscript', 'figure', 'figcaption']):
            tag.decompose()

        # Source-specific selectors (most likely to succeed first)
        selectors = [
            ('div',  {'data-component': 'text-block'}),   # BBC
            ('div',  {'class': 'article__content'}),      # BBC alt
            ('div',  {'class': 'content__article-body'}), # Guardian
            ('div',  {'class': 'ArticleBody-articleBody'}),# Reuters
            ('div',  {'class': 'zn-body__paragraph'}),    # CNN legacy
            ('article', {}),
            ('main', {}),
        ]

        for tag_name, attrs in selectors:
            el = soup.find(tag_name, attrs) if attrs else soup.find(tag_name)
            if el:
                text = ' '.join(
                    p.get_text(' ', strip=True)
                    for p in el.find_all('p')
                    if p.get_text(strip=True)
                )
                if len(text) >= MIN_CONTENT_LEN:
                    return text[:MAX_CONTENT_LEN]

        # Generic fallback — all <p> tags
        text = ' '.join(
            p.get_text(' ', strip=True)
            for p in soup.find_all('p')
            if p.get_text(strip=True)
        )
        return text[:MAX_CONTENT_LEN] if len(text) >= MIN_CONTENT_LEN else None

    except requests.Timeout:
        return None
    except requests.ConnectionError:
        return None
    except Exception:
        return None


# ── Main scraper class ────────────────────────────────────────────────────

class NewsScraper:
    """Fetches real articles from multiple RSS feeds."""

    def get_sample_news(self, max_per_feed=8, fetch_full_pages=False):
        """
        Scrape all configured RSS feeds and return article dicts.
        Feeds are fetched concurrently to minimise total wall-clock time.

        Each dict: title, content, category, source_name, source_url, published_date.
        """
        def _scrape_feed(feed_url, source_name, default_category):
            """Fetch and parse one RSS feed; returns a list of article dicts."""
            logger.info(f"[NewsScraper] Fetching {source_name} from {feed_url}")
            root = _fetch_xml(feed_url)
            if root is None:
                logger.warning(f"[NewsScraper] Failed to fetch or parse {source_name}")
                return []

            channel = root.find('channel')
            items = channel.findall('item') if channel is not None else root.findall('item')
            if not items:
                return []

            logger.info(f"[{source_name}] {len(items)} items in {feed_url}")
            feed_articles = []

            for item in items[:max_per_feed]:
                try:
                    title = _clean_html(item.findtext('title') or '')
                    link  = (item.findtext('link') or '').strip()
                    pub   = item.findtext('pubDate') or item.findtext('published')

                    if not title or not link:
                        continue

                    content = None
                    if fetch_full_pages:
                        content = _try_fetch_article_page(link)

                    if not content or len(content) < MIN_CONTENT_LEN:
                        content = _extract_item_text(item)

                    if not content or len(content) < MIN_CONTENT_LEN:
                        if len(title) >= MIN_CONTENT_LEN:
                            content = title
                        else:
                            logger.debug(f"Skipping (no usable content): {title[:60]}")
                            continue

                    category = _infer_category(f"{title} {content[:200]}", default_category)
                    feed_articles.append({
                        'title':          title,
                        'content':        content,
                        'category':       category,
                        'source_name':    source_name,
                        'source_url':     link,
                        'published_date': _parse_date(pub),
                    })

                except Exception as exc:
                    logger.warning(f"Error parsing item in {feed_url}: {exc}")

            return feed_articles

        articles = []
        # Fetch all feeds in parallel — wall-clock time ≈ slowest single feed
        with ThreadPoolExecutor(max_workers=len(RSS_FEEDS)) as executor:
            futures = {
                executor.submit(_scrape_feed, url, name, cat): (url, name)
                for url, name, cat in RSS_FEEDS
            }
            for future in as_completed(futures):
                try:
                    articles.extend(future.result())
                except Exception as exc:
                    url, name = futures[future]
                    logger.warning(f"[NewsScraper] Feed worker error [{name}]: {exc}")

        logger.info(f"[NewsScraper] total articles collected: {len(articles)}")
        return articles
