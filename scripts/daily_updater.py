"""Daily Automated Synchronizer for USD/MXN Macro Monitor

Runs inside GitHub Actions daily at 19:00 UTC (13:00 CST México).
Fetches latest market news and updates data.js.
"""

import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

FEED_URL = "https://news.google.com/rss/search?q=peso+mexicano+dolar+banxico+when:2d&hl=es-419&gl=MX&ceid=MX:es-419"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"

def fetch_latest_news():
    articles = []
    try:
        req = urllib.request.Request(FEED_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read()
        root = ET.fromstring(content)
        for item in root.findall(".//item")[:15]:
            title = item.findtext("title", "")
            url = item.findtext("link", "")
            source = item.findtext("source", "Medio Financiero")
            pub_date = item.findtext("pubDate", "")
            
            # Limpiar título
            parts = title.rsplit(" - ", 1)
            clean_title = parts[0] if parts else title
            if len(parts) > 1:
                source = parts[1]

            direction = "NEUTRAL"
            title_lower = clean_title.lower()
            if any(k in title_lower for k in ["cae", "baja el peso", "sube el dolar", "deprecia", "aranceles", "riesgo"]):
                direction = "ALCISTA_DOLAR"
            elif any(k in title_lower for k in ["sube el peso", "baja el dolar", "aprecia", "superpeso", "ganancias"]):
                direction = "BAJISTA_DOLAR"

            archetype = "macro"
            if "banxico" in title_lower or "tasa" in title_lower:
                archetype = "decision_banxico"
            elif "arancel" in title_lower or "t-mec" in title_lower:
                archetype = "aranceles_comercio"
            elif "inflacion" in title_lower:
                archetype = "inflacion_datos"

            articles.append({
                "id": f"NEWS-{abs(hash(url)) % 100000000:08x}",
                "title": clean_title,
                "source": source,
                "url": url,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "archetype": archetype,
                "direction": direction
            })
    except Exception as e:
        print(f"Error fetching RSS: {e}")
    return articles

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_js_path = os.path.join(root_dir, "data.js")
    
    if not os.path.exists(data_js_path):
        print("data.js not found.")
        return

    fresh_news = fetch_latest_news()
    if fresh_news:
        print(f"Fetched {len(fresh_news)} live articles.")
        with open(data_js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Reemplazar RECENT_NEWS en data.js
        news_json = json.dumps(fresh_news, indent=2, ensure_ascii=False)
        pattern = r"const RECENT_NEWS = \[.*?\];"
        replacement = f"const RECENT_NEWS = {news_json};"
        new_content = re.sub(pattern, replacement, js_content, flags=re.S)

        with open(data_js_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("data.js updated with fresh news.")
    else:
        print("No fresh news fetched, keeping existing dataset.")

if __name__ == "__main__":
    main()
