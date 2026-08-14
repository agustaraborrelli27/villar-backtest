Villar Backtest — Contexto del proyecto
Qué es esto

Herramienta de backtesting de portafolios estilo "buy and hold": el usuario elige símbolos, capital y un rango de fechas, y la app simula cómo habría rendido esa cartera comprando una sola vez al inicio y manteniendo sin rebalancear.

Es un MVP inspirado en la herramienta de backtesting de villarcapital.com.ar.

Estado actual (funcionando)

El prototipo YA funciona de punta a punta en local: formulario → backend FastAPI → yfinance → cálculo → gráfico con datos reales de mercado. Primer commit hecho en Git.

Próximos pasos, EN ESTE ORDEN
Diseño visual (ver sección más abajo) — hacer esto ANTES de subirlo a internet.
Deploy: backend a Render o Railway, frontend a Vercel o Netlify. Actualizar la URL de la API en el frontend (hoy apunta a localhost:8000).
Recién después: base de datos de precios, pesos custom, benchmark, datos argentinos.
Stack
Backend: Python + FastAPI, en backend/. Lógica en backend/backtest.py, endpoint en backend/main.py.
Datos: yfinance 1.6.0 (actualizado desde 0.2.43 porque Yahoo estaba bloqueando la versión vieja).
Frontend: HTML + JS plano en frontend/index.html. Gráfico con Chart.js vía CDN de jsdelivr (cdnjs daba 404, no usar cdnjs para Chart.js).
Python: usar 3.12, NO 3.14 (pandas no compila bien en 3.14 sin Visual Studio instalado).
Cómo correr el proyecto

cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000

Después abrir frontend/index.html directo en el navegador.

Diseño visual (referencia para la próxima sesión)

Inspirado en nicolasmessa.com. Elementos a imitar:

Fondo oscuro (casi negro / azul muy oscuro).
Degradado tipo aurora boreal de fondo: morado a violeta/azul, difuminado y suave, no sólido.
Tipografía sans-serif grande, redondeada, moderna, en blanco para los títulos.
Botones simples: blanco sólido, o transparente con borde fino.
Sensación general: fintech premium pero cálido, no corporativo-frío.
No copiar la estructura de esa página (es un sitio de venta de curso/asesoría); nuestro proyecto es una sola herramienta enfocada.
Decisiones de diseño técnico (y por qué)
Buy & hold, sin rebalanceo: simplifica el cálculo, mismo enfoque que Villar Capital.
Sin comisiones, impuestos, dividendos ni slippage: simplificación intencional del MVP.
Capital repartido en partes iguales por defecto: el backend soporta weights custom, el frontend todavía no lo expone.
CORS abierto: bien en desarrollo local, restringir al dominio real antes de producción.
Roadmap conocido (después del deploy)
Persistencia de precios (SQLite/Postgres) para no depender de Yahoo Finance en cada request.
Pesos custom por activo en el frontend.
Comparación contra benchmark (ej. SPY).
Datos argentinos (CEDEARs, bonos, Merval, dólar MEP/CCL) — evaluar fuentes.
Convenciones
Textos de UI y mensajes de error en español rioplatense.
Métricas financieras nuevas van en _compute_metrics() en backtest.py.