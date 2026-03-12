import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

def fetch_rss_feed(url: str) -> list:
    """
    Fetches and parses an RSS feed (e.g., Upwork).
    Returns a list of dicts: {title, link, description, published}.
    """
    print(f"RSSReader: Fetching RSS feed from {url}...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        items = []
        
        for item in root.findall(".//item"):
            title = item.find("title").text if item.find("title") is not None else "No Title"
            link = item.find("link").text if item.find("link") is not None else "#"
            desc = item.find("description").text if item.find("description") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            
            items.append({
                "title": title,
                "link": link,
                "description": desc,
                "published": pub_date,
                "source": "RSS"
            })
            
        print(f"RSSReader: Found {len(items)} items in RSS feed.")
        return items
        
    except Exception as e:
        print(f"RSSReader Error fetching RSS: {e}")
        return []

async def ejecutar(**kwargs) -> Dict[str, Any]:
    """
    AgentProtocol implementation for RSSReader.
    """
    if "rss_url" in kwargs:
        items = fetch_rss_feed(kwargs["rss_url"])
        return {"items": items, "status": "COMPLETED"}
        
    return {"error": "No RSS URL provided", "status": "FAILED"}
