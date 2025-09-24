import feedparser
import hashlib
import os
from feedgen.feed import FeedGenerator
import xml.etree.ElementTree as ET

FEEDS = [
    "https://politepol.com/fd/hYxyD0YIwERV.xml",
    "https://politepol.com/fd/252sONZTOIDX.xml",
    "https://politepol.com/fd/42bU3PeKaKjf.xml",
    "https://politepol.com/fd/svZEZwEXeeYC.xml",
    "https://politepol.com/fd/vkBVLkhLdU6Y.xml",
    "https://politepol.com/fd/pL68k3eA2SrA.xml",
    "https://politepol.com/fd/qmEwvjQrNyvg.xml",
    "https://politepol.com/fd/lHWPAUKpkaqz.xml",
    "https://politepol.com/fd/V9Hk3fW83a2N.xml",
    "https://politepol.com/fd/jvYL3YgY1MBF.xml",
]

OUTPUT_FILE = "combined.xml"
INDEX_FILE = "index.txt"
MAX_ITEMS = 200

def get_id(entry):
    """Generate a unique ID for an entry."""
    if "id" in entry:
        return entry.id
    elif "link" in entry:
        return entry.link
    else:
        return hashlib.sha256(entry.title.encode("utf-8")).hexdigest()

def load_seen():
    """Load IDs of already-seen entries."""
    if not os.path.exists(INDEX_FILE):
        return set()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip() and not line.startswith("#"))

def save_seen(seen):
    """Save the set of seen IDs."""
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        for eid in seen:
            f.write(eid + "\n")

def load_existing_entries():
    """Load existing articles from combined.xml into a dict."""
    if not os.path.exists(OUTPUT_FILE):
        return {}
    try:
        tree = ET.parse(OUTPUT_FILE)
    except ET.ParseError:
        return {}
    root = tree.getroot()
    entries = {}
    for item in root.findall("./channel/item"):
        link = item.find("link").text if item.find("link") is not None else None
        title = item.find("title").text if item.find("title") is not None else ""
        eid = link or hashlib.sha256(title.encode("utf-8")).hexdigest()
        entries[eid] = {
            "title": title,
            "link": link,
            "pubDate": item.find("pubDate").text if item.find("pubDate") is not None else None,
            "description": item.find("description").text if item.find("description") is not None else None
        }
    return entries

def main():
    fg = FeedGenerator()
    fg.title("Merged RSS Feed (10 sources)")
    fg.link(href="https://yourusername.github.io/rss-merged-feed/combined.xml", rel="self")
    fg.description("Combined feed from 10 sources, no duplicates")
    fg.language("en")

    seen = load_seen()
    new_seen = set(seen)

    all_entries = load_existing_entries()

    # Fetch all feeds and add new unseen entries
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            eid = get_id(entry)
            if eid not in seen:
                all_entries[eid] = {
                    "title": entry.title,
                    "link": entry.link if "link" in entry else None,
                    "pubDate": entry.published if "published" in entry else None,
                    "description": entry.summary if "summary" in entry else None
                }
                new_seen.add(eid)

    # Convert to list and sort by pubDate descending
    sorted_entries = list(all_entries.items())
    sorted_entries.sort(key=lambda x: x[1]["pubDate"] if x[1]["pubDate"] else "", reverse=True)

    # Trim to MAX_ITEMS
    for eid, data in sorted_entries[:MAX_ITEMS]:
        fe = fg.add_entry()
        fe.id(eid)
        fe.title(data["title"])
        if data["link"]:
            fe.link(href=data["link"])
        if data["pubDate"]:
            fe.pubDate(data["pubDate"])
        if data["description"]:
            fe.description(data["description"])

    fg.rss_file(OUTPUT_FILE)
    save_seen(new_seen)

if __name__ == "__main__":
    main()
