from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backtest import run_backtest
from excel_flujos import leer_flujos
from xirr import calcular_xirr

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
    
@app.post("/api/tir")
async def tir(archivo: UploadFile = File(...)):
    try:
        contenido = await archivo.read()
        flujos = leer_flujos(contenido)
        resultado = calcular_xirr(flujos)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {e}")

    return {
        "tir": resultado,
        "tir_porcentaje": round(resultado * 100, 2),
        "flujos": [
            {
                "fecha": f["fecha"].isoformat(),
                "monto_usd": round(f["monto_usd"], 2),
                "tipo": f["tipo"],
            }
            for f in flujos
        ],
    }
