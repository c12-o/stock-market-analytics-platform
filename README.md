# Real-Time Stock Market Analytics Platform

Full-stack app: **FastAPI + pandas/NumPy** backend that pulls historical stock
data and computes financial indicators (Moving Average, RSI, MACD, Bollinger
Bands, Volatility), with a **React dashboard** frontend that visualizes it.
Results are cached in a database (SQLite locally, PostgreSQL in production).

```
stock-platform/
├── backend/
│   ├── main.py           <- FastAPI app & REST endpoints
│   ├── indicators.py     <- All indicator math (pandas/numpy)
│   ├── database.py       <- Caching layer (SQLite/Postgres via SQLAlchemy)
│   ├── requirements.txt
│   ├── render.yaml        <- one-click Render deploy config
│   └── Procfile            <- Railway/Heroku-style deploy config
└── frontend/
    └── index.html          <- React dashboard (CDN-based, no build step)
```

---

## 1. Run it locally tonight

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Visit `http://localhost:8000` — you should see `{"status": "ok", ...}`.
Test a real query: `http://localhost:8000/api/stock/AAPL?period=6mo`

No database setup needed — it auto-creates a local `stock_cache.db` SQLite file.

### Frontend
The frontend is a single static HTML file (React loaded via CDN — no npm
install or build step, so it runs instantly).

1. Open `frontend/index.html` directly in your browser, **or** serve it:
   ```bash
   cd frontend
   python3 -m http.server 5500
   ```
   Then visit `http://localhost:5500`.

2. By default it talks to `http://localhost:8000` (your local backend). To
   point it at a different backend URL, add this line right before the
   closing `</head>` tag:
   ```html
   <script>window.STOCK_API_BASE = "https://your-backend-url.onrender.com";</script>
   ```

---

## 2. Deploy tomorrow (free tier, ~15 minutes total)

### Step A — Push to GitHub
Create a new repo (or reuse an existing one) and push the whole
`stock-platform/` folder to it.

### Step B — Deploy the backend on Render
1. Go to [render.com](https://render.com) → sign in with GitHub.
2. **New +** → **Web Service** → connect your repo.
3. Render will detect `render.yaml` automatically. If it asks manually, set:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. (Optional but recommended) Add a free PostgreSQL database: **New +** →
   **PostgreSQL** → once created, copy its **Internal Database URL** → in
   your web service's **Environment** tab, add:
   - `DATABASE_URL` = `<paste the URL>`
   If you skip this, the app just uses SQLite on Render's disk — fine for a
   demo, but data won't persist across redeploys.
5. Click **Deploy**. Wait ~2–3 minutes. You'll get a URL like
   `https://stock-analytics-api.onrender.com`.
6. Test it: visit `https://stock-analytics-api.onrender.com/api/stock/AAPL`.

### Step C — Deploy the frontend on Netlify
1. Open `frontend/index.html` and add your Render backend URL right before
   `</head>`:
   ```html
   <script>window.STOCK_API_BASE = "https://stock-analytics-api.onrender.com";</script>
   ```
2. Go to [app.netlify.com/drop](https://app.netlify.com/drop).
3. Drag the `frontend` folder in. Netlify gives you a live URL instantly,
   e.g. `https://your-app.netlify.app`.

### Step D — Fix CORS (if the dashboard shows a network error)
In `backend/main.py`, the CORS middleware currently allows all origins
(`allow_origins=["*"]`), so this should work out of the box. If you tighten
it later, add your exact Netlify URL to the `allow_origins` list and
redeploy the backend.

---

## 3. What each indicator means (for your project writeup)

| Indicator | What it shows |
|---|---|
| **Moving Average (20/50-day)** | Smoothed trend direction, filters out daily noise |
| **RSI (14-day)** | Momentum oscillator (0–100); >70 = overbought, <30 = oversold |
| **MACD** | Trend-following momentum via the difference between two EMAs, plus a signal line |
| **Bollinger Bands** | Volatility bands (±2 std dev around a 20-day SMA); price near the bands suggests extended moves |
| **Volatility** | Annualized standard deviation of daily log returns, as a % |

---

## 4. Known limitations / next steps
- Data comes from Yahoo Finance via `yfinance` — free but occasionally
  rate-limits on very heavy use; the caching layer (15-min TTL) protects
  against that for repeated queries.
- No user auth/watchlists yet — every request is public and stateless.
- The frontend uses Chart.js (not Recharts) to avoid an npm build step and
  guarantee it deploys with zero tooling issues by your deadline. If you
  want a Vite + Recharts version with a proper build pipeline later, that's
  a straightforward follow-up.
