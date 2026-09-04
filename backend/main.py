"""
Real-Time Stock Market Analytics Platform — API
Fetches historical market data (yfinance), computes financial indicators
(pandas/numpy), caches results (SQLite/PostgreSQL), and serves everything
through a FastAPI REST API for the React dashboard.
"""
import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from indicators import compute_all_indicators
from database import init_db, get_cached, set_cached

app = FastAPI(title="Stock Market Analytics API", version="1.0.0")

# Allow the React frontend (any origin — tighten this to your deployed
# frontend URL once you know it, e.g. ["https://your-app.netlify.app"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


def _clean_for_json(df: pd.DataFrame) -> list:
    """Convert a DataFrame with a DatetimeIndex into a list of JSON-safe dicts."""
    df = df.replace({np.nan: None})
    records = []
    for idx, row in df.iterrows():
        record = {"date": idx.strftime("%Y-%m-%d")}
        record.update(row.to_dict())
        records.append(record)
    return records


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Stock Market Analytics API",
        "endpoints": ["/api/stock/{ticker}", "/api/summary/{ticker}"],
    }


@app.get("/api/stock/{ticker}")
def get_stock_data(
    ticker: str,
    period: str = Query("6mo", description="1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    interval: str = Query("1d", description="1d, 1wk, 1mo"),
):
    ticker = ticker.upper().strip()

    cached = get_cached(ticker, period, interval)
    if cached is not None:
        return {"ticker": ticker, "period": period, "interval": interval, "cached": True, "data": cached}

    try:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch data for {ticker}: {e}")

    if raw is None or raw.empty:
        raise HTTPException(status_code=404, detail=f"No data found for ticker '{ticker}'")

    # yfinance sometimes returns MultiIndex columns for a single ticker — flatten them
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    enriched = compute_all_indicators(raw)
    records = _clean_for_json(enriched)

    set_cached(ticker, period, interval, records)

    return {"ticker": ticker, "period": period, "interval": interval, "cached": False, "data": records}


@app.get("/api/summary/{ticker}")
def get_summary(ticker: str):
    ticker = ticker.upper().strip()
    try:
        info = yf.Ticker(ticker).fast_info
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch summary for {ticker}: {e}")

    if not info:
        raise HTTPException(status_code=404, detail=f"No summary found for '{ticker}'")

    return {
        "ticker": ticker,
        "last_price": getattr(info, "last_price", None),
        "previous_close": getattr(info, "previous_close", None),
        "day_high": getattr(info, "day_high", None),
        "day_low": getattr(info, "day_low", None),
        "year_high": getattr(info, "year_high", None),
        "year_low": getattr(info, "year_low", None),
        "market_cap": getattr(info, "market_cap", None),
        "volume": getattr(info, "last_volume", None),
    }
