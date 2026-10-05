"""Daily Automated Multi-Channel Synchronizer for USD/MXN Macro Monitor

Ingests 4 Global Intelligence Channels:
1. Geopolítica & Petróleo (Medio Oriente, Ormuz, Ucrania, Crudo)
2. EE.UU. & Fed (Política monetaria, Tasas, Aranceles globales)
3. Multipolaridad & BRICS (Riesgo global, Mercados emergentes)
4. México & Banxico (Política interna, T-MEC, Reformas)

Computes Quantamental Impact Scoring (1.0 to 10.0) & Deterministic Transmission Mechanisms.
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

def calculate_quantamental_metrics(title, source, channel):
    """
    Computes Deterministic Quantamental Impact Score (1.0 to 10.0),
    Impact Category, Direction, and Macro Transmission Summary.
    """
    tl = title.lower()
    sl = source.lower()

    # 1. Authority / Source Tier (Weight 40%)
    if any(k in sl for k in ["banco de méxico", "banxico", "reserva federal", "federal reserve", "powell", "hacienda", "shcp", "casa blanca", "opep", "opec", "fmi", "imf"]):
        auth_score = 1.0
    elif any(k in tl for k in ["banxico", "fed", "powell", "shcp", "inegi", "cpi", "inflación", "nóminas", "pib"]):
        auth_score = 0.85
    elif any(k in sl for k in ["bloomberg", "reuters", "financial times", "wall street journal", "el economista", "el financiero", "expansion", "forbes"]):
        auth_score = 0.70
    else:
        auth_score = 0.45

    # 2. Structural Shock Magnitude (Weight 40%)
    if any(k in tl for k in ["guerra", "ormuz", "misil", "ataque", "bombardeo", "sanción", "bloqueo", "arancel", "escalada"]):
        shock_score = 0.95
    elif any(k in tl for k in ["tasas de interés", "alza de tasa", "recorte de tasa", "inflación", "reforma judicial", "déficit", "quiebra"]):
        shock_score = 0.80
    elif any(k in tl for k in ["tregua", "acuerdo comercial", "paz", "aprecia", "superpeso", "fortalece"]):
        shock_score = 0.75
    else:
        shock_score = 0.40

    # 3. Density / Market Buzz (Weight 20%)
    density_score = 0.65

    # Combined Score (1.0 - 10.0)
    raw_score = 10.0 * (0.40 * auth_score + 0.40 * shock_score + 0.20 * density_score)
    impact_score = round(max(1.0, min(10.0, raw_score)), 1)

    # Impact Level Category
    if impact_score >= 8.0:
        impact_level = "CRÍTICO"
        impact_badge = "badge-critico"
    elif impact_score >= 6.5:
        impact_level = "ALTO"
        impact_badge = "badge-alto"
    elif impact_score >= 4.5:
        impact_level = "MODERADO"
        impact_badge = "badge-moderado"
    else:
        impact_level = "SEGUIMIENTO"
        impact_badge = "badge-bajo"

    # Direction Classification
    if any(k in tl for k in ["guerra", "ataque", "escala", "sancion", "sanción", "alza de tasa", "arancel", "cae el peso", "sube el dolar", "debilita", "presion", "presión", "desploma"]):
        direction = "ALCISTA_DOLAR"
    elif any(k in tl for k in ["recorte de tasa", "tregua", "aprecia", "superpeso", "fortalece", "gana", "acuerdo comercial", "paz", "desinflacion", "desinflación"]):
        direction = "BAJISTA_DOLAR"
    else:
        direction = "NEUTRAL"

    # Macro Transmission Mechanism Summary
    if channel == "geopolitica_energia":
        if direction == "ALCISTA_DOLAR":
            transmission = "Tensión militar o riesgo en rutas de crudo dispara la aversión al riesgo global y eleva la demanda de refugio en USD."
        elif direction == "BAJISTA_DOLAR":
            transmission = "Distensión geopolítica reduce prima de riesgo del crudo, desinfla el DXY y favorece flujos de carry trade hacia el MXN."
        else:
            transmission = "Seguimiento a cotizaciones energéticas e inventarios sin desbalance inmediato en flujos cambiarios."
    elif channel == "eeuu_fed":
        if direction == "ALCISTA_DOLAR":
            transmission = "Expectativa de tasas elevadas en EE.UU. o riesgos arancelarios fortalecen al dólar y comprimen el diferencial frente a Banxico."
        elif direction == "BAJISTA_DOLAR":
            transmission = "Señales de relajación monetaria en la Fed debilitan al billete verde y amplían el diferencial de rendimiento a favor de México."
        else:
            transmission = "Expectativa de política monetaria asimilada por el consenso de los mercados financieros."
    elif channel == "mexico_banxico":
        if direction == "ALCISTA_DOLAR":
            transmission = "Riesgo legislativo, fiscal o desaceleración económica local eleva la prima de riesgo soberano del peso mexicano."
        elif direction == "BAJISTA_DOLAR":
            transmission = "Postura firme de tasas en Banxico o disciplina presupuestaria sostienen el atractivo de la moneda local."
        else:
            transmission = "Indicadores macroeconómicos domésticos dentro del rango previsto por Banco de México."
    else:  # global_brics
        if direction == "ALCISTA_DOLAR":
            transmission = "Aversión generalizada a mercados emergentes reduce la liquidez y presiona a la baja divisas líquidas como el MXN."
        elif direction == "BAJISTA_DOLAR":
            transmission = "Apetito por riesgo global o diversificación de reservas impulsa entradas de capital hacia divisas de alto rendimiento."
        else:
            transmission = "Evolución multilateral y flujos comerciales globales en proceso de monitoreo continuo."

    return {
        "direction": direction,
        "impact_score": impact_score,
        "impact_level": impact_level,
        "impact_badge": impact_badge,
        "transmission": transmission
    }

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

            metrics = calculate_quantamental_metrics(clean_title, source, channel_info["channel"])

            articles.append({
                "id": f"NEWS-{abs(hash(link)) % 100000000:08x}",
                "title": clean_title,
                "source": source,
                "url": link,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "channel": channel_info["channel"],
                "channel_ui": channel_info["tag_ui"],
                "archetype": channel_info["channel"],
                "direction": metrics["direction"],
                "impact_score": metrics["impact_score"],
                "impact_level": metrics["impact_level"],
                "impact_badge": metrics["impact_badge"],
                "transmission": metrics["transmission"]
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

    # Sort descending by Quantamental Impact Score
    all_articles.sort(key=lambda x: x["impact_score"], reverse=True)

    if all_articles:
        with open(data_js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        news_json = json.dumps(all_articles, indent=2, ensure_ascii=False)
        pattern = r"const RECENT_NEWS = \[.*?\];"
        replacement = f"const RECENT_NEWS = {news_json};"
        new_content = re.sub(pattern, replacement, js_content, flags=re.S)

        with open(data_js_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"data.js actualizado con {len(all_articles)} noticias globales ordenadas por impacto.")
    else:
        print("No se pudieron descargar noticias frescas.")

if __name__ == "__main__":
    main()
