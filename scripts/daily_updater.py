"""Daily Automated Multi-Channel Synchronizer for USD/MXN Macro Monitor

Ingests 4 Global Intelligence Channels:
1. Geopolítica & Petróleo (Medio Oriente, Ormuz, Ucrania, Crudo)
2. EE.UU. & Fed (Política monetaria, Tasas, Aranceles globales)
3. Multipolaridad & BRICS (Riesgo global, Mercados emergentes)
4. México & Banxico (Política interna, T-MEC, Reformas)
"""

import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"

CHANNELS = [
    {
        "channel": "geopolitica_energia",
        "tag_ui": "🌍 Geopolítica & Petróleo",
        "query": 'guerra OR "medio oriente" OR ormuz OR israel OR ucrania OR petroleo OR wti when:3d'
    },
    {
        "channel": "eeuu_fed",
        "tag_ui": "🇺🇸 EE.UU. & Fed",
        "query": '"reserva federal" OR powell OR "guerra comercial" OR "tasas de interes" OR aranceles when:3d'
    },
    {
        "channel": "global_brics",
        "tag_ui": "🌐 Global & BRICS",
        "query": 'brics OR "aversion al riesgo" OR "mercados emergentes" OR "desdolarizacion" when:3d'
    },
    {
        "channel": "mexico_banxico",
        "tag_ui": "🇲🇽 México & Banxico",
        "query": 'peso mexicano OR "banco de mexico" OR banxico OR "t-mec" OR "reforma" when:3d'
    }
]

def fetch_channel_news(channel_info):
    articles = []
    query = channel_info["query"]
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=es-419&gl=MX&ceid=MX:es-419"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read()
        root = ET.fromstring(content)
        for item in root.findall(".//item")[:6]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            source = item.findtext("source", "Medio Internacional")
            
            parts = title.rsplit(" - ", 1)
            clean_title = parts[0] if parts else title
            if len(parts) > 1:
                source = parts[1]

            direction = "NEUTRAL"
            tl = clean_title.lower()
            if any(k in tl for k in ["guerra", "ataque", "escala", "sancion", "alza de tasa", "arancel", "cae el peso", "sube el dolar", "debilita", "presion"]):
                direction = "ALCISTA_DOLAR"
            elif any(k in tl for k in ["recorte de tasa", "tregua", "aprecia", "superpeso", "fortalece", "gana", "acuerdo comercial"]):
                direction = "BAJISTA_DOLAR"

            articles.append({
                "id": f"NEWS-{abs(hash(link)) % 100000000:08x}",
                "title": clean_title,
                "source": source,
                "url": link,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "channel": channel_info["channel"],
                "channel_ui": channel_info["tag_ui"],
                "archetype": channel_info["channel"],
                "direction": direction
            })
    except Exception as e:
        print(f"Error fetching channel {channel_info['channel']}: {e}")
    return articles

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_js_path = os.path.join(root_dir, "data.js")
    
    if not os.path.exists(data_js_path):
        print("data.js no encontrado.")
        return

    all_articles = []
    for ch in CHANNELS:
        arts = fetch_channel_news(ch)
        print(f"Canal '{ch['channel']}': {len(arts)} artículos recuperados.")
        all_articles.extend(arts)

    if all_articles:
        with open(data_js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        news_json = json.dumps(all_articles, indent=2, ensure_ascii=False)
        pattern = r"const RECENT_NEWS = \[.*?\];"
        replacement = f"const RECENT_NEWS = {news_json};"
        new_content = re.sub(pattern, replacement, js_content, flags=re.S)

        with open(data_js_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"data.js actualizado con {len(all_articles)} noticias globales.")
    else:
        print("No se pudieron descargar noticias frescas.")

if __name__ == "__main__":
    main()
