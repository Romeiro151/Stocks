from pydantic import BaseModel

class QuoteResponse(BaseModel):
    company: str
    current_price: float | str
    previous_close: float | str
    market_cap: int | str
    high_52_weeks: float | str
    low_52_weeks: float | str
    dividend_yield: float | str

class InfoResponse(BaseModel):
    company_name: str
    sector: str
    industry: str
    employees: int | str
    country: str
    summary: str

class HistoryData(BaseModel):
    date: str
    close: float

class HistoryResponse(BaseModel):
    company: str
    total_days: int
    data: list[HistoryData]

class RecResponse(BaseModel):
    company: str
    period: str
    strong_buy: int
    buy: int
    hold: int
    sell: int
    strong_sell: int