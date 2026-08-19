"""
Lógica de backtesting de portafolios.

Estrategia implementada: "buy and hold" simple.
- Se reparte el capital inicial entre los activos elegidos (por defecto, en partes iguales).
- Se compra una sola vez, al precio de cierre del primer día del período.
- No se rebalancea, no se descuentan comisiones ni impuestos, no se reinvierten dividendos.
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import yfinance as yf


@dataclass
class BacktestResult:
    dates: list
    portfolio_value: list
    per_asset_value: dict
    metrics: dict
        benchmark_value: list = None


def _download_prices(tickers, start, end):
    """Descarga precios de cierre ajustados para una lista de tickers."""
    data = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )

    if data.empty:
        raise ValueError("No se encontraron datos para los tickers/fechas indicados.")

    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"]
    else:
        close = data[["Close"]]
        close.columns = tickers

    close = close.dropna(how="all")
    return close


def _compute_benchmark(dates_index, start, end, capital, ticker="SPY"):
    """Calcula cómo hubiera rendido invertir el mismo capital en el benchmark (SPY)."""
    try:
        data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    except Exception:
        return None

    if data.empty:
        return None

    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.reindex(dates_index).ffill().bfill()
    if close.isna().all():
        return None

    shares = capital / close.iloc[0]
    value = close * shares
    return [round(v, 2) for v in value.tolist()]


def run_backtest(tickers, capital, start, end, weights: Optional[dict] = None):
    if len(tickers) < 2:
        raise ValueError("Seleccioná al menos 2 símbolos.")

    tickers = [t.strip().upper() for t in tickers]

    if weights is None:
        weights = {t: 1.0 / len(tickers) for t in tickers}
    else:
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-6:
            weights = {k: v / total for k, v in weights.items()}

    prices = _download_prices(tickers, start, end)
    prices = prices.dropna()

    if prices.empty:
        raise ValueError("No hay fechas con datos simultáneos para todos los activos elegidos.")

    first_prices = prices.iloc[0]

    shares = {}
    for t in tickers:
        capital_asset = capital * weights[t]
        shares[t] = capital_asset / first_prices[t]

    per_asset_value = {t: (prices[t] * shares[t]) for t in tickers}
    per_asset_df = pd.DataFrame(per_asset_value)
    portfolio_value = per_asset_df.sum(axis=1)

    metrics = _compute_metrics(portfolio_value, capital)
    benchmark_value = _compute_benchmark(portfolio_value.index, start, end, capital)

    return BacktestResult(
        dates=[d.strftime("%Y-%m-%d") for d in portfolio_value.index],
        portfolio_value=[round(v, 2) for v in portfolio_value.tolist()],
        per_asset_value={
            t: [round(v, 2) for v in per_asset_df[t].tolist()] for t in tickers
        },
        metrics=metrics,
                benchmark_value=benchmark_value,
    )


def _compute_metrics(portfolio_value, capital):
    final_value = portfolio_value.iloc[-1]
    total_return = (final_value / capital) - 1

    days = (portfolio_value.index[-1] - portfolio_value.index[0]).days
    years = days / 365.25 if days > 0 else 0
    cagr = (final_value / capital) ** (1 / years) - 1 if years > 0 else 0

    daily_returns = portfolio_value.pct_change().dropna()
    volatility_annual = daily_returns.std() * (252 ** 0.5) if len(daily_returns) > 1 else 0

    running_max = portfolio_value.cummax()
    drawdown = (portfolio_value - running_max) / running_max
    max_drawdown = drawdown.min()

    risk_free = 0.0
    sharpe = (
        (daily_returns.mean() * 252 - risk_free) / volatility_annual
        if volatility_annual > 0
        else 0
    )

    return {
        "capital_inicial": round(capital, 2),
        "valor_final": round(final_value, 2),
        "retorno_total_pct": round(total_return * 100, 2),
        "cagr_pct": round(cagr * 100, 2),
        "volatilidad_anual_pct": round(volatility_annual * 100, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "sharpe_aprox": round(sharpe, 2),
    }
