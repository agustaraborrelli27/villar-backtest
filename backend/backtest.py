"""
Lógica de backtesting de portafolios.

Estrategia: "buy and hold" con fecha de compra (y venta opcional) individual por activo.
- Cada activo tiene su propio capital, fecha de compra y fecha de venta opcional.
- Antes de la fecha de compra, ese capital se considera en efectivo (no invertido, no crece).
- Si se indica fecha de venta, después de esa fecha el valor queda fijo (se vendió, no se reinvierte).
- No se rebalancea, no se descuentan comisiones ni impuestos, no se reinvierten dividendos.
"""

from dataclasses import dataclass

import pandas as pd
import yfinance as yf


@dataclass
class BacktestResult:
    dates: list
    portfolio_value: list
    per_asset_value: dict
    metrics: dict
    benchmark_value: list = None


def _download_close(ticker, start, end):
    """Descarga precios de cierre ajustados para un ticker. Devuelve None si no hay datos."""
    data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if data.empty:
        return None
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()
    if close.empty:
        return None
    return close


def _compute_benchmark(dates_index, start, end, capital, ticker="SPY"):
    """Calcula cómo hubiera rendido invertir el mismo capital en el benchmark (SPY)."""
    try:
        close = _download_close(ticker, start, end)
    except Exception:
        return None
    if close is None:
        return None
    close = close.reindex(dates_index).ffill().bfill()
    if close.isna().all():
        return None
    shares = capital / close.iloc[0]
    value = close * shares
    return [round(v, 2) for v in value.tolist()]


def run_backtest(assets, end):
    """
    assets: lista de dicts, cada uno con:
        ticker: str
        capital: float
        buy_date: str (YYYY-MM-DD)
        sell_date: str opcional (YYYY-MM-DD). Si no se indica, se usa 'end'.
    end: fecha final del análisis (YYYY-MM-DD).
    """
    if not assets:
        raise ValueError("Agregá al menos 1 activo.")
    if len(assets) > 10:
        raise ValueError("Máximo 10 activos.")

    total_capital = 0.0
    buy_dates = []

    for a in assets:
        if not a.get("ticker"):
            raise ValueError("Todos los activos necesitan un ticker.")
        if not a.get("buy_date"):
            raise ValueError(f"Falta la fecha de compra de {a.get('ticker')}.")
        if not a.get("capital") or a.get("capital") <= 0:
            raise ValueError(f"El capital de {a.get('ticker')} tiene que ser mayor a 0.")
        sell_date = a.get("sell_date") or end
        if sell_date < a["buy_date"]:
            raise ValueError(f"La fecha de venta de {a['ticker']} no puede ser anterior a la de compra.")
        total_capital += float(a["capital"])
        buy_dates.append(a["buy_date"])

    global_start = min(buy_dates)
    combined_index = pd.bdate_range(global_start, end)

    per_asset_value = {}
    portfolio_value = pd.Series(0.0, index=combined_index)

    for i, a in enumerate(assets):
        ticker = a["ticker"].strip().upper()
        capital = float(a["capital"])
        buy_date = a["buy_date"]
        sell_date = a.get("sell_date") or end

        close = _download_close(ticker, buy_date, sell_date)
        if close is None:
            raise ValueError(f"No se encontraron datos para {ticker} entre {buy_date} y {sell_date}.")

        buy_price = close.iloc[0]
        shares = capital / buy_price
        value_series = close * shares

        aligned = value_series.reindex(combined_index)
        aligned = aligned.ffill()
        aligned = aligned.fillna(capital)

        label = f"{ticker}_{i + 1}"
        per_asset_value[label] = [round(v, 2) for v in aligned.tolist()]
        portfolio_value = portfolio_value.add(aligned, fill_value=0)

    metrics = _compute_metrics(portfolio_value, total_capital)
    benchmark_value = _compute_benchmark(portfolio_value.index, global_start, end, total_capital)

    return BacktestResult(
        dates=[d.strftime("%Y-%m-%d") for d in portfolio_value.index],
        portfolio_value=[round(v, 2) for v in portfolio_value.tolist()],
        per_asset_value=per_asset_value,
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
