# Market Feed Watcher

A small production-style backend system for monitoring market listings, detecting price/status changes, and streaming updates in real time.

Built to explore backend infrastructure patterns used in data-heavy systems such as crawlers, market feeds, and operational dashboards.

---

## Why This Project Exists

Market Feed Watcher simulates a backend crawler system that:

- fetches marketplace listing data
- parses HTML into structured records
- stores listing snapshots
- detects price/status changes
- tracks crawler run health
- broadcasts live updates over WebSockets
- exposes operational metrics through APIs
- provides a lightweight dashboard for visibility

The project is intentionally small, but designed around real backend concerns:

- crawler reliability
- retry/timeout behavior
- data freshness
- operational visibility
- source health
- change detection
- real-time monitoring

---

## Architecture

```text
[ Market Source ]  -->  Simulated HTML pages (Batch 1 & 2)
       ↓
[ Async Crawler ]  -->  Fetch logic with retries & timeouts
       ↓
[ HTML Parser ]    -->  BeautifulSoup extraction & normalization
       ↓
[ Database ]       -->  Supabase (PostgreSQL) snapshot storage
       ↓
[ Change Engine ]  -->  Diffing current vs previous snapshots
       ↓
[ Ops Tracking ]   -->  Crawl logs & Source Health metrics
       ↓
[ Delivery ]       -->  REST API + WebSocket broadcast
       ↓
[ UI Dashboard ]   -->  Live visual monitoring
```


---

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- Supabase (PostgreSQL)
- BeautifulSoup
- WebSockets
- Docker Compose
- HTML/CSS/JavaScript dashboard

---

## Core Features

### Async Crawler

The crawler simulates fetching marketplace HTML asynchronously.

It includes:

- timeout handling
- retry behavior
- transient failure simulation
- source-specific parser structure

### Snapshot Tracking

Each listing fetch creates a snapshot containing:

- external listing ID
- title
- price
- status
- source
- capture timestamp

### Change Detection

The system compares incoming listings with the latest known snapshot and detects:

- new listings
- price changes
- status changes

### Crawl Run Tracking

Each crawler execution records:

- source
- status
- listings found
- changes detected
- start time
- finish time
- error message

### Source Health Metrics

The system summarizes recent source reliability:

- total runs
- successful runs
- failed runs
- success rate
- latest status
- total changes detected
- average listings found

### Live Dashboard

The dashboard shows:

- live market-feed changes
- recent snapshots
- source health metrics

---

## Running Locally

### Option 1: Python
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open: [http://localhost:8000/docs](http://localhost:8000/docs)

Then open: `dashboard.html`

---

### Option 2: Docker Compose
```bash
cd backend
docker compose up --build
```

Open: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Demo Flow

1. Start the backend.
2. Open `dashboard.html`.
3. Click **Run Crawler**.
4. First run creates initial listing snapshots.
5. Second run detects:
   - Honda Civic price change
   - Toyota Corolla status change
   - Hyundai Elantra new listing
6. Source health updates after each crawl run.

---

## API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Root service status and version |
| `/crawl/run` | `POST` | Triggers the async crawler (with retry logic) |
| `/ingest` | `POST` | Manually ingest a raw batch of listing data |
| `/snapshots` | `GET` | Retrieve the latest captured listing snapshots |
| `/crawl-runs` | `GET` | History and status of recent crawler executions |
| `/health/source/{name}` | `GET` | Detailed reliability and success rate metrics |
| `/ws/changes` | `WS` | Real-time WebSocket feed for live updates |

---

## Operational Philosophy

This project demonstrates a specialized crawler operations backend. The main objective is building the observability and reliability layer required for production crawler pipelines.

A high-scale version of this system could include:

- Real external marketplace adapters
- `httpx.AsyncClient` with custom middleware
- Proxy rotation and user-agent management
- Distributed task processing (Celery/Arq)
- Queue-based ingestion
- Redis for caching and rate limiting
- Source-specific crawl policies
- Automated alerting on source degradation
- CI/CD deployment pipelines

---

## Future Improvements

- Add background scheduled jobs (Cron/BackgroundTasks)
- Add queue-based ingestion (Redis/RabbitMQ)
- Add Prometheus metrics & Grafana dashboards
- Add unit/integration tests
- Add source configuration database table
- Add admin controls for crawl frequency and concurrency