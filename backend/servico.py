from transformers import pipeline
from datetime import datetime

print("Loading FinBERT model into memory ... (This can take a few seconds)")

finbert = pipeline("sentiment-analysis", model = "ProsusAI/finbert")
print("FinBERT loaded successfully!")

def analyse_behavior(raw_news: list) -> dict:

    if not raw_news:
        return {"overall_feeling": "N/A", "details": []}
    
    clean_data = []
    text_for_ai = []

    for article in raw_news:
        content =  article.get('content', {})
        title = content.get('title', 'No title')
        summary = content.get('summaty', '')

        full_text = f"{title}. {summary}"[:500]
        text_for_ai.append(full_text)

        raw_date = content.get("pubDate")
        try:
            dt = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ")
            formatted_date = dt.strftime("%d/%m/%Y %H:%M")
        except Exception as e:
            formatted_date = raw_date

        url = (
            content.get("clickThroughUrl", {}).get("url") or \
            content.get("canonicalUrl", {}).get("url") or \
            "Unavailable Link" 
        )

        clean_data.append({
            "date": formatted_date,
            "title": title,
            "editor": content.get("provider", {}).get("displayName", "Unknown"),
            "link": url
        })
        
    results_ai = finbert(text_for_ai)

    score_math = 0.0

    for item, result_ai in zip(clean_data, results_ai):
        label = result_ai['label'].upper()
        confidence_decimal = result_ai['score']

        item["feeling"] = result_ai['label'].upper()
        item["confidence"] = round(result_ai['score'] * 100, 1)

        if label == "POSITIVE":
            score_math += confidence_decimal
        elif label == "NEGATIVE":
            score_math -= confidence_decimal
    
    if score_math > 0.5:
        overall = "BULLISH"
    elif score_math < -0.5:
        overall = "BEARISH"
    else:
        overall = "NEUTRAL"

    return {
        "overall_feeling": overall,
        "details": clean_data
    }