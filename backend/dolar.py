import datetime
import requests

BASE_URL = "https://api.argentinadatos.com/v1/cotizaciones/dolares/contadoconliqui"


def _pedir_cotizacion(fecha: datetime.date) -> float | None:
    """Pide al servicio el CCL de una fecha puntual. Devuelve None si no hay dato ese día."""
    fecha_str = fecha.strftime("%Y/%m/%d")
    url = f"{BASE_URL}/{fecha_str}"
    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException:
        return None

    if resp.status_code != 200:
        return None

    data = resp.json()
    venta = data.get("venta")
    if venta is None:
        return None
    return float(venta)


def obtener_ccl(fecha: datetime.date, max_dias_atras: int = 10) -> float:
    """
    Devuelve la cotización del dólar CCL (venta) para una fecha dada.
    Si esa fecha no tiene cotización (fin de semana, feriado), retrocede
    día por día hasta encontrar el día hábil anterior más cercano con dato.
    """
    for i in range(max_dias_atras + 1):
        fecha_intento = fecha - datetime.timedelta(days=i)
        valor = _pedir_cotizacion(fecha_intento)
        if valor is not None:
            return valor

    raise ValueError(
        f"No se encontró cotización de CCL para {fecha} ni en los {max_dias_atras} días anteriores."
    )
