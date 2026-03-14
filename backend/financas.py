import yfinance as yf
import asyncio
import time

CACHE_FINANCAS = {}
TEMPO_CACHE = 300

def get_cache(key: str):

    if key in CACHE_FINANCAS:
        data, timestamp = CACHE_FINANCAS[key]
        if time.time() - timestamp < TEMPO_CACHE:
            return data
        
    return None

def save_cache(key: str, data):
    CACHE_FINANCAS[key] = (data, time.time())

async def ticker_exists(ticker: str) -> bool:
    
    key = f"exists_{ticker}"
    cached = get_cache(key)
    if cached is not None:
        return cached
    
    try:

        stock = yf.Ticker(ticker)
        hist = await asyncio.to_thread(stock.history, "1d")
        exists = not hist.empty
        save_cache(key, exists)
        return exists
    
    except:

        return False

async def fecth_quote(name: str) -> dict:
    
    ticker = name.upper()
    key = f"quote_{name}"
    cached = get_cache(key)
    if cached:
        return cached
    
    stock = yf.Ticker(ticker)
    info = await asyncio.to_thread(getattr, stock, 'info')

    if not info or "symbol" not in info:
        raise ValueError("It was not possible to get Yahoo Finance Data")

    result =  {
        "company": ticker,
        "current_price": info.get("currentPrice", "N/A"),
        "previous_close": info.get("regularMarketPreviousClose", "N/A"),
        "market_cap": info.get("marketCap", "N/A"),
        "high_52_weeks": info.get("fiftyTwoWeekHigh", "N/A"),
        "low_52_weeks": info.get("fiftyTwoWeekLow", "N/A"),
        "dividend_yield": info.get("dividendYield", "N/A")
    }

    save_cache(key, result)
    return result
    
async def fecth_info(name: str) -> dict:
     
    ticker = name.upper()
    key = f"info_{ticker}"
    cached = get_cache(key)
    if cached:
        return cached
    
    stock = yf.Ticker(ticker)
    info = await asyncio.to_thread(getattr, stock, 'info')

    if not info or "symbol" not in info:
        raise ValueError("It was not possible to gather info about the company")

    result = {
        "company_name": info.get("longName", ticker),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "employees": info.get("fullTimeEmployees", "N/A"),
        "country": info.get("country", "N/A"),
        "summary": info.get("longBusinessSummary", "Unavailable summary.")
    }

    save_cache(key, result)
    return result

async def fecth_history(name: str) -> dict:

    ticker = name.upper()
    key = f"hist_{ticker}"
    cached = get_cache(key)
    if cached:
        return cached
    
    stock = yf.Ticker(ticker)
    hist = await asyncio.to_thread(stock.history, period = "1mo")

    if hist.empty:
        raise ValueError("No history available for this stcok")
    
    dates = hist.index.strftime("'%Y-%m-%d").tolist()
    closes = hist['Close'].round(2).tolist()

    history_data = [{"date": d, "close": c} for d, c in zip(dates, closes)]

    result = {
        "company": ticker,
        "total_days": len(history_data),
        "data": history_data
    }

    save_cache(key, result)
    return result

async def fecth_recommendations(name: str) -> dict:
    
    ticker = name.upper()
    key = f"recs_{ticker}"
    cached = get_cache(key)
    if cached:
        return cached

    stock = yf.Ticker(ticker)
    recs = await asyncio.to_thread(getattr, stock, 'recommendations')

    if recs is None or recs.empty:
        result = {
            "company": ticker,
            "period": "N/A",
            "strong_buy": 0,
            "buy": 0,
            "hold": 0,
            "sell": 0,
            "strong_sell": 0
        }
        save_cache(key, result)
        return result
    
    latest_rec = recs.iloc[0].to_dict()

    result = {
        "company": ticker,
        "period": latest_rec.get("period", "N/A"),
        "strong_buy": latest_rec.get("strongBuy", 0),
        "buy": latest_rec.get("buy", 0),
        "hold": latest_rec.get("hold", 0),
        "sell": latest_rec.get("sell", 0),
        "strong_sell": latest_rec.get("strongSell", 0)
    }
    
    save_cache(key, result)
    return result
