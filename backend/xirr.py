import datetime


def _xnpv(tasa: float, flujos: list[dict]) -> float:
    """Valor presente neto de los flujos, dada una tasa anual."""
    fecha_base = flujos[0]["fecha"]
    total = 0.0
    for f in flujos:
        dias = (f["fecha"] - fecha_base).days
        total += f["monto_usd"] / (1 + tasa) ** (dias / 365.0)
    return total


def _xnpv_derivada(tasa: float, flujos: list[dict]) -> float:
    """Derivada del XNPV respecto a la tasa, para Newton-Raphson."""
    fecha_base = flujos[0]["fecha"]
    total = 0.0
    for f in flujos:
        dias = (f["fecha"] - fecha_base).days
        t = dias / 365.0
        if t == 0:
            continue
        total += -t * f["monto_usd"] / (1 + tasa) ** (t + 1)
    return total


def calcular_xirr(flujos: list[dict], tasa_inicial: float = 0.1, max_iter: int = 100, tolerancia: float = 1e-6) -> float:
    """
    Calcula la TIR anualizada (XIRR) de una lista de flujos con fecha.
    Cada flujo: {"fecha": date, "monto_usd": float}
    Los flujos negativos son plata que sale del bolsillo del inversor,
    los positivos son plata que vuelve.
    """
    if len(flujos) < 2:
        raise ValueError("Se necesitan al menos 2 flujos para calcular la TIR.")

    montos = [f["monto_usd"] for f in flujos]
    if all(m >= 0 for m in montos) or all(m <= 0 for m in montos):
        raise ValueError("Los flujos deben tener al menos un valor negativo y uno positivo.")

    tasa = tasa_inicial
    for _ in range(max_iter):
        # (1 + tasa) no puede ser <= 0, o la potencia fraccionaria explota
        if tasa <= -0.999999:
            tasa = -0.999999

        try:
            valor = _xnpv(tasa, flujos)
            derivada = _xnpv_derivada(tasa, flujos)
        except (OverflowError, ZeroDivisionError):
            break

        if derivada == 0:
            break

        nueva_tasa = tasa - valor / derivada

        # Frenar saltos gigantes que hacen diverger el método
        if nueva_tasa - tasa > 1:
            nueva_tasa = tasa + 1
        elif nueva_tasa - tasa < -1:
            nueva_tasa = tasa - 1

        if abs(nueva_tasa - tasa) < tolerancia:
            return nueva_tasa
        tasa = nueva_tasa

    # Si Newton-Raphson no convergió, probamos por búsqueda binaria en un rango amplio
    try:
        return _xirr_bisector(flujos)
    except ValueError:
        raise ValueError("La TIR no convergió. Revisá los datos cargados (fechas y montos).")


def _xirr_bisector(flujos: list[dict], baja: float = -0.999, alta: float = 10.0, max_iter: int = 200, tolerancia: float = 1e-6) -> float:
    """Respaldo: búsqueda binaria, más lenta pero muy estable."""
    valor_baja = _xnpv(baja, flujos)
    valor_alta = _xnpv(alta, flujos)

    if valor_baja * valor_alta > 0:
        raise ValueError("No se encontró una TIR en el rango esperado.")

    for _ in range(max_iter):
        medio = (baja + alta) / 2
        valor_medio = _xnpv(medio, flujos)
        if abs(valor_medio) < tolerancia:
            return medio
        if valor_baja * valor_medio < 0:
            alta = medio
            valor_alta = valor_medio
        else:
            baja = medio
            valor_baja = valor_medio

    return (baja + alta) / 2
