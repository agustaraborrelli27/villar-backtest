from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backtest import run_backtest

app = FastAPI(title="Villar Backtest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BacktestRequest(BaseModel):
    tickers: list
    capital: float
    start: str
    end: str
    weights: Optional[dict] = None


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/backtest")
def backtest(req: BacktestRequest):
    try:
        result = run_backtest(
            tickers=req.tickers,
            capital=req.capital,
            start=req.start,
            end=req.end,
            weights=req.weights,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {e}")

    return {
        "dates": result.dates,
        "portfolio_value": result.portfolio_value,
        "per_asset_value": result.per_asset_value,
        "metrics": result.metrics,
    }