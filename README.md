# AlphaEdge Market Intelligence Engine

A decoupled, 10-factor market intelligence system for Indian Indices (NIFTY, SENSEX, BANKNIFTY).

## Architecture

The system has been decoupled from a monolithic script into a 3-tier architecture:

1. **Data Collector (`collector.py`)**: Fetches market data from Upstox and Yahoo Finance, runs the 10-factor signal engine (Trend, VIX, Open Interest skew, PCR, Max Pain, etc.), and writes the results to a local database.
2. **Database (`alphaedge.db`)**: A SQLite database managed by `alphaedge_db.py`. Stores historical snapshots of index signals and global macro indicators.
3. **API Server (`api_server.py`)**: A FastAPI backend that connects to the database and serves REST endpoints (`/api/latest`, `/api/history`) and the frontend assets.
4. **Dashboard (`frontend/`)**: A clean, minimalist HTML/JS dashboard adhering strictly to the `DESIGN.md` visual tokens. It polls the FastAPI server and visualizes historical trends using Chart.js.

---

## Setup & Installation

Install the required Python packages (FastAPI and Uvicorn):

```bash
pip install fastapi uvicorn[standard]
```

*(Note: If you are using a managed environment on recent Linux distributions, you may need to append `--break-system-packages` or use a virtual environment).*

---

## Usage

You must run the data collector to populate the database, and run the API server to view the dashboard.

### 1. Run the Data Collector

Navigate to the `scripts` directory:
```bash
cd /home/vreddy1/Desktop/Projects/scripts
```

**Single Run:**
Fetch data once and exit. Useful for manual updates or running via cron.
```bash
python3 collector.py
```

**Continuous Loop:**
Run continuously in the background, fetching new data every N minutes.
```bash
python3 collector.py --loop --interval 5
```

### 2. Run the API Server & Dashboard

In a separate terminal, start the FastAPI server:
```bash
cd /home/vreddy1/Desktop/Projects/scripts
python3 api_server.py
```

### 3. View the Dashboard

Open your web browser and navigate to:
**http://localhost:8765**

The dashboard will automatically poll the API every 60 seconds to fetch the latest signals and update the historical Chart.js visualizations.

---

## Endpoints Reference

If you want to consume the AlphaEdge data in other bots or scripts, you can query the local API directly:

- **`GET /api/latest`**
  Returns the most recent signal snapshot for all symbols (NIFTY, SENSEX, BANKNIFTY) along with global macro data (VIX, DXY, Crude Oil, US30, Gold, Silver).

- **`GET /api/history?sym=NIFTY&days=30`**
  Returns a time-series array of metrics (spot price, score, PCR, Max Pain) for a specific symbol over the last N days. Used primarily for Chart.js trend rendering.

- **`GET /api/symbols`**
  Returns a list of supported symbols.
