# Asset Monitor — prototipo

Calcula la media móvil de 200 sesiones y la **media móvil de 52 semanas** (promedio de 52 cierres semanales), la desviación porcentual y alertas configurables.

## Instalar y ejecutar

Requiere Python 3.10 o posterior.

```bash
python -m venv .venv
```

Activa el entorno:
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

Instala y ejecuta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abrirá en el navegador.

## Uso

1. Edita la lista de tickers y tipos.
2. Configura los umbrales en la barra lateral.
3. Elige si alertar según 200 sesiones, 52 semanas o cualquiera de las dos.
4. Pulsa **Actualizar cotizaciones y calcular**.
5. Puedes descargar los resultados como CSV.

Por defecto: 10 % para índices/fondos indexados y 20 % para acciones/ETF/ETC y criptomonedas. Los umbrales son configurables.

## Limitaciones

Usa Yahoo Finance mediante `yfinance`, que no es una API oficial garantizada. Puede haber retrasos, límites o símbolos no disponibles. No envía avisos automáticos en segundo plano; la actualización se inicia al pulsar el botón.
