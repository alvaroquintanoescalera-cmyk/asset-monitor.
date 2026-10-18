import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date

st.set_page_config(page_title="Asset Monitor", page_icon="📈", layout="wide")
st.title("📈 Asset Monitor")
st.caption("Prototipo de seguimiento técnico · Media móvil de 200 sesiones y media móvil de 52 semanas")

with st.sidebar:
    st.header("Configuración")
    stock_threshold = st.number_input("Umbral acciones / ETF / ETC (%)", min_value=1.0, max_value=90.0, value=20.0, step=1.0)
    index_threshold = st.number_input("Umbral índices / fondos indexados (%)", min_value=1.0, max_value=90.0, value=10.0, step=1.0)
    crypto_threshold = st.number_input("Umbral criptomonedas (%)", min_value=1.0, max_value=90.0, value=20.0, step=1.0)
    ma_choice = st.selectbox("Media que activa la alerta", ["200 sesiones", "52 semanas", "Cualquiera de las dos"])
    st.markdown("---")
    st.caption("Los datos se consultan al pulsar el botón. Yahoo Finance puede tener retrasos, símbolos no disponibles o cambios en su servicio.")

st.subheader("1. Añade tus activos")
st.write("Introduce un ticker por línea. Ejemplos de símbolos de Yahoo Finance: `NKE`, `MSTR`, `SPYL.DE`, `BTC-EUR`.")
initial = """NKE,Acción
IREN,Acción
MSTR,Acción
SPYL.DE,Fondo indexado
BTC-EUR,Criptomoneda
IB1T.DE,ETC"""
tickers_text = st.text_area("Ticker,Tipo (opcional)", value=initial, height=145,
    help="Tipos sugeridos: Acción, ETF, ETC, Fondo indexado, Índice, Criptomoneda. Si no indicas tipo, se tratará como Acción.")
st.caption("Edita o borra los ejemplos y añade tus propios símbolos. La lista no se guarda de forma permanente en este prototipo.")

def parse_assets(raw):
    rows, seen = [], set()
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",", 1)]
        ticker = parts[0].upper()
        typ = parts[1] if len(parts) > 1 and parts[1] else "Acción"
        if ticker and ticker not in seen:
            seen.add(ticker)
            rows.append({"Ticker": ticker, "Tipo": typ})
    return rows

assets = parse_assets(tickers_text)
st.subheader("2. Calcula medias y desviaciones")
st.write("La media de 200 sesiones usa los últimos 200 cierres diarios disponibles. La media de 52 semanas usa los últimos 52 cierres semanales, uno por semana.")
run = st.button("🔄 Actualizar cotizaciones y calcular", type="primary")

if run:
    if not assets:
        st.error("Introduce al menos un ticker.")
        st.stop()

    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, asset in enumerate(assets):
        ticker, typ = asset["Ticker"], asset["Tipo"]
        status.write(f"Consultando {ticker}…")
        try:
            hist = yf.Ticker(ticker).history(period="3y", interval="1d", auto_adjust=True)
            if hist is None or hist.empty or "Close" not in hist:
                results.append({"Ticker": ticker, "Tipo": typ, "Estado": "Sin datos"})
                progress.progress((i + 1) / len(assets))
                continue

            close = hist["Close"].dropna()
            if close.empty:
                results.append({"Ticker": ticker, "Tipo": typ, "Estado": "Sin cierres"})
                progress.progress((i + 1) / len(assets))
                continue

            price = float(close.iloc[-1])
            latest_date = close.index[-1]
            ma200 = float(close.tail(200).mean()) if len(close) >= 200 else None

            # One last available close per week, then average the last 52 weekly closes.
            weekly_close = close.resample("W-FRI").last().dropna()
            ma52w = float(weekly_close.tail(52).mean()) if len(weekly_close) >= 52 else None

            dev200 = (price / ma200 - 1) * 100 if ma200 else None
            dev52w = (price / ma52w - 1) * 100 if ma52w else None

            t = typ.lower()
            if any(x in t for x in ["índice", "indice", "fondo indexado", "index fund"]):
                threshold = float(index_threshold)
            elif any(x in t for x in ["cripto", "bitcoin", "crypto"]):
                threshold = float(crypto_threshold)
            else:
                threshold = float(stock_threshold)

            if ma_choice == "200 sesiones":
                checked = [dev200]
            elif ma_choice == "52 semanas":
                checked = [dev52w]
            else:
                checked = [dev200, dev52w]
            valid = [v for v in checked if v is not None]
            alert = any(v <= -threshold for v in valid) if valid else False

            if alert:
                signal = "🔴 ALERTA"
            elif not valid:
                signal = "🟡 Histórico insuficiente"
            else:
                signal = "🟢 Sin alerta"

            results.append({
                "Ticker": ticker,
                "Tipo": typ,
                "Último cierre": price,
                "Fecha del cierre": latest_date.strftime("%Y-%m-%d"),
                "Media 200 sesiones": ma200,
                "Desv. vs 200 (%)": dev200,
                "Media móvil 52 semanas": ma52w,
                "Desv. vs 52 semanas (%)": dev52w,
                "Umbral alerta (%)": threshold,
                "Señal": signal,
                "Estado": "OK" if valid else "Histórico insuficiente",
            })
        except Exception as e:
            results.append({"Ticker": ticker, "Tipo": typ, "Estado": f"Error de consulta: {str(e)[:120]}"})
        progress.progress((i + 1) / len(assets))

    status.empty()
    progress.empty()
    st.session_state["asset_monitor_results"] = pd.DataFrame(results)

if "asset_monitor_results" in st.session_state:
    df = st.session_state["asset_monitor_results"].copy()
    st.subheader("3. Resultados")
    if "Señal" in df.columns:
        alerts = df[df["Señal"].astype(str).str.contains("ALERTA", na=False)]
        c1, c2, c3 = st.columns(3)
        c1.metric("Activos consultados", len(df))
        c2.metric("Alertas", len(alerts))
        c3.metric("Con datos válidos", int((df.get("Estado", pd.Series(dtype=str)) == "OK").sum()))
        if not alerts.empty:
            st.error("Se han alcanzado uno o más umbrales configurados.")
            st.dataframe(alerts, use_container_width=True, hide_index=True)
        else:
            st.success("No hay alertas con los umbrales y la media seleccionados.")

    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={
            "Último cierre": st.column_config.NumberColumn(format="%.4f"),
            "Media 200 sesiones": st.column_config.NumberColumn(format="%.4f"),
            "Desv. vs 200 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Media móvil 52 semanas": st.column_config.NumberColumn(format="%.4f"),
            "Desv. vs 52 semanas (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Umbral alerta (%)": st.column_config.NumberColumn(format="%.1f%%"),
        }
    )
    st.download_button("⬇️ Descargar resultados CSV", data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"asset_monitor_{date.today().isoformat()}.csv", mime="text/csv")

with st.expander("Cómo se calcula y límites del prototipo"):
    st.markdown("""
- **Desviación (%)** = `(último cierre / media móvil - 1) × 100`.
- **Media de 200 sesiones:** promedio de los últimos 200 cierres diarios disponibles.
- **Media móvil de 52 semanas:** promedio de los últimos 52 cierres semanales (un cierre por semana). No es lo mismo que promediar 252 cierres diarios.
- Umbrales iniciales: 10 % para índices/fondos indexados y 20 % para acciones, ETF y ETC; criptomonedas tienen umbral independiente del 20 %. Se pueden cambiar en la barra lateral.
- Si eliges **Cualquiera de las dos**, la alerta se activa si una u otra media cruza el umbral.
- Este prototipo no ejecuta actualizaciones ni envía avisos en segundo plano: debes abrirlo y pulsar **Actualizar**. Se puede añadir después programación y correo.
- Consulta Yahoo Finance mediante `yfinance`; puede haber retrasos, límites o símbolos no disponibles. Las medias usan precios ajustados y datos históricos disponibles.
""")
st.caption("Herramienta de seguimiento técnico, no recomendación de compra o venta.")
