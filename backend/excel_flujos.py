import io
import datetime
import pandas as pd

from dolar import obtener_ccl


def _parsear_fecha(valor) -> datetime.date:
    if isinstance(valor, datetime.datetime):
        return valor.date()
    if isinstance(valor, datetime.date):
        return valor
    return pd.to_datetime(valor, dayfirst=True).date()


def _monto_en_usd(fecha: datetime.date, moneda: str, monto: float) -> float:
    moneda = str(moneda).strip().upper()
    if moneda == "USD":
        return float(monto)
    if moneda == "ARS":
        ccl = obtener_ccl(fecha)
        return float(monto) / ccl
    raise ValueError(f"Moneda no reconocida: {moneda}. Debe ser ARS o USD.")


def leer_flujos(archivo_bytes: bytes) -> list[dict]:
    """
    Lee el Excel de 3 pestañas (Ingreso, Retiro, Cartera) y devuelve una lista
    de flujos ordenados por fecha, cada uno con:
      - fecha (datetime.date)
      - monto_usd (float, ya convertido)
      - signo: negativo para plata que sale del bolsillo del inversor
               (Ingreso, Valor Inicial), positivo para plata que vuelve
               (Retiro, Valor Actual)
    """
    xls = pd.ExcelFile(io.BytesIO(archivo_bytes))

    flujos = []

    # --- Ingresos: salen del bolsillo -> negativo ---
    if "Ingreso" in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name="Ingreso", header=3)
        df = df.dropna(subset=["Fecha", "Moneda", "Monto"])
        for _, fila in df.iterrows():
            fecha = _parsear_fecha(fila["Fecha"])
            monto_usd = _monto_en_usd(fecha, fila["Moneda"], fila["Monto"])
            flujos.append({"fecha": fecha, "monto_usd": -monto_usd, "tipo": "Ingreso"})

    # --- Retiros: vuelven al bolsillo -> positivo ---
    if "Retiro" in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name="Retiro", header=3)
        df = df.dropna(subset=["Fecha", "Moneda", "Monto"])
        for _, fila in df.iterrows():
            fecha = _parsear_fecha(fila["Fecha"])
            monto_usd = _monto_en_usd(fecha, fila["Moneda"], fila["Monto"])
            flujos.append({"fecha": fecha, "monto_usd": monto_usd, "tipo": "Retiro"})

    # --- Cartera: Valor Inicial (negativo) y Valor Actual (positivo) ---
    if "Cartera" not in xls.sheet_names:
        raise ValueError("El Excel no tiene la pestaña 'Cartera'.")

    df_cart = pd.read_excel(xls, sheet_name="Cartera", header=3)
    df_cart = df_cart.dropna(subset=["Tipo", "Fecha", "Moneda", "Monto"])

    tiene_inicial = False
    tiene_actual = False

    for _, fila in df_cart.iterrows():
        tipo = str(fila["Tipo"]).strip()
        fecha = _parsear_fecha(fila["Fecha"])
        monto_usd = _monto_en_usd(fecha, fila["Moneda"], fila["Monto"])

        if tipo == "Valor Inicial":
            flujos.append({"fecha": fecha, "monto_usd": -monto_usd, "tipo": "Valor Inicial"})
            tiene_inicial = True
        elif tipo == "Valor Actual":
            flujos.append({"fecha": fecha, "monto_usd": monto_usd, "tipo": "Valor Actual"})
            tiene_actual = True
        else:
            raise ValueError(f"Tipo inválido en pestaña Cartera: {tipo}")

    if not tiene_inicial:
        raise ValueError("Falta la fila 'Valor Inicial' en la pestaña Cartera.")
    if not tiene_actual:
        raise ValueError("Falta la fila 'Valor Actual' en la pestaña Cartera.")

    flujos.sort(key=lambda f: f["fecha"])
    return flujos
