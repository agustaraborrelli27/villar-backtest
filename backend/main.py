from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backtest import run_backtest

app = FastAPI(title="Villar Backtest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AssetInput(BaseModel):
    ticker: str
    capital: float
    buy_date: str
    sell_date: Optional[str] = None


class BacktestRequest(BaseModel):
    assets: List[AssetInput]
    end: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/backtest")
def backtest(req: BacktestRequest):
    try:
        assets = [a.dict() for a in req.assets]
        result = run_backtest(assets=assets, end=req.end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {e}")

    return {
        "dates": result.dates,
        "portfolio_value": result.portfolio_value,
        "per_asset_value": result.per_asset_value,
        "metrics": result.metrics,
        "benchmark_value": result.benchmark_value,
    }
