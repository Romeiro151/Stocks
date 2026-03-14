from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import yfinance as yf
import time
import asyncio

from servico import analyse_behavior
from financas import ticker_exists, fecth_quote, fecth_info, fecth_history, fecth_recommendations
from modelos import QuoteResponse, InfoResponse, HistoryResponse, RecResponse

app = FastAPI(title = "Terminal Bloomberg API", version = "2.0")

NEWS_CACHE = {}
CACHE_EXPERATION_SECONDS = 900

@app.get("/data/{name}")
def get_data(name = str, period: str = "1mo"):
    print(f"Request received in the API for the stock: {name.upper()} (Period: {period})")

    try: 
        stock = yf.Ticker(name)
        price_evolution = stock.history(period = period)

        if price_evolution.empty:
            raise HTTPException(status_code=404, detail = f"Name: {name} not found")
        
        price_evolution = price_evolution.reset_index()

        price_evolution['Date'] = price_evolution['Date'].dt.strftime('%Y-%m-%d')

        return price_evolution[['Date', 'Close', 'Volume']].to_dict(orient = "records")
    
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    
@app.get("/news/{name}")
async def get_news_analysis(name: str):

    ticker = name.upper()
    current_time = time.time()    

    if ticker in NEWS_CACHE:
        cached_data, timestamp = NEWS_CACHE[ticker]
        if current_time - timestamp < CACHE_EXPERATION_SECONDS:
            print("From CACHE !")
            return cached_data
        
    if not await ticker_exists(ticker):
        raise HTTPException(status_code = 404, detail =f"Action '{ticker}' not found in stocks' market")

    try:
        stock = yf.Ticker(ticker)
        raw_news = await asyncio.to_thread(getattr, stock, 'news')

        if not raw_news:
            return {"message":f"There were no news from {ticker}."}
        
        analysis_results = await asyncio.to_thread(analyse_behavior, raw_news)

        response = {
            "company": ticker,
            "total_news": len(analysis_results["details"]),
            "overall_feeling": analysis_results["overall_feeling"],
            "analysis": analysis_results["details"]
        }

        NEWS_CACHE[ticker] = (response, current_time)

        return response
    
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Error analysing news: str{(e)}")
    
@app.get("/quote/{name}", response_model=QuoteResponse)
async def get_quote(name: str):
    ticker = name.upper()
    if not await ticker_exists(ticker):
        raise HTTPException(status_code=404, detail=f"Ação '{ticker}' não encontrada.")
    return await fecth_quote(ticker)


@app.get("/info/{name}", response_model=InfoResponse)
async def get_company_info(name: str):
    ticker = name.upper()
    if not await ticker_exists(ticker):
        raise HTTPException(status_code=404, detail=f"Ação '{ticker}' não encontrada.")
    return await fecth_info(ticker)


@app.get("/history/{name}", response_model=HistoryResponse)
async def get_history(name: str):
    ticker = name.upper()
    if not await ticker_exists(ticker):
        raise HTTPException(status_code=404, detail=f"Ação '{ticker}' não encontrada.")
    return await fecth_history(ticker)


@app.get("/recommendations/{name}", response_model=RecResponse)
async def get_recommendations(name: str):
    ticker = name.upper()
    if not await ticker_exists(ticker):
        raise HTTPException(status_code=404, detail=f"Ação '{ticker}' não encontrada.")
    return await fecth_recommendations(ticker)


app.mount("/static", StaticFiles(directory = "static"), name = "static")

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")
