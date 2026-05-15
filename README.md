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
[ Database ]       -->  Local PostgreSQL via Docker Compose, or hosted PostgreSQL/Supabase
       ↓
[ Change Engine ]  -->  Diffing current vs previous snapshots
       ↓
[ Ops Tracking ]   -->  Crawl logs & Source Health metrics
       ↓
[ Delivery ]       -->  REST API + batched WebSocket broadcast
       ↓
[ UI Dashboard ]   -->  Live visual monitoring
```

---

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL / Supabase
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

Create a `.env` file first. For quick local development, SQLite works:

```bash
cd market-feed-watcher/backend
printf "DATABASE_URL=sqlite:///./market_feed_watcher.db\nAPP_URL=http://localhost:8000\nLOG_LEVEL=INFO\n" > .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open: [http://localhost:8000/docs](http://localhost:8000/docs)

Dashboard: [http://localhost:8000/static/dashboard.html](http://localhost:8000/static/dashboard.html)

### Option 2: Docker Compose

Docker Compose starts both the API and a local PostgreSQL database. You do not need Supabase for local development.

```bash
cd market-feed-watcher/backend
docker compose up --build
```

Open: [http://localhost:8000/docs](http://localhost:8000/docs)

Dashboard: [http://localhost:8000/static/dashboard.html](http://localhost:8000/static/dashboard.html)

### Hosted Database

For Supabase or another hosted PostgreSQL instance, set `DATABASE_URL` in `.env` or your deployment environment:

```bash
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:5432/postgres
```

---

## Demo Flow

1. Start the backend.
2. Open the dashboard at `/static/dashboard.html`.
3. Click **Run Crawler Once**.
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
| `/crawl/run` | `POST` | Triggers the mock async crawler with retry logic |
| `/crawl/http` | `POST` | Triggers the HTTP crawler against a real URL |
| `/ingest` | `POST` | Manually ingest a raw batch of listing data |
| `/snapshots` | `GET` | Retrieve the latest captured listing snapshots |
| `/crawl-runs` | `GET` | History and status of recent crawler executions |
| `/health/source/{name}` | `GET` | Detailed reliability and success rate metrics |
| `/scheduler/start` | `POST` | Start auto-crawl on a configurable interval |
| `/scheduler/stop` | `POST` | Stop the auto-crawl scheduler |
| `/scheduler/status` | `GET` | Check if the scheduler is running |
| `/demo/batch-1` | `POST` | Ingest seed data batch 1 (initial listings) |
| `/demo/batch-2` | `POST` | Ingest seed data batch 2 (with changes) |
| `/ws/changes` | `WS` | Real-time WebSocket feed for batched live updates |

---

## Project Overview

Market Feed Watcher is a backend system designed to explore crawler-style market feed infrastructure. The system simulates marketplace sources, parses listing data, stores snapshots, detects price and status changes, and streams those updates to a live dashboard through WebSockets.

Beyond basic scraping, the project implements:

- **Crawl Run Tracking**: Monitoring execution status and duration.
- **Reliability Layer**: Retry and timeout handling for upstream sources.
- **Operational Metrics**: Real-time source health and success rate analytics.
- **Change Detection**: Automated diffing of snapshots to identify market movements.
- **Testing**: Unit tests covering the core change-detection and health logic.

## Operational Notes

The in-app scheduler is intentionally lightweight and safe for a single API process. It uses an async task, cancellation handling, and a process-local lock to avoid duplicate scheduler tasks inside one worker. In a multi-worker production deployment, schedule crawler work outside the API process with a queue or scheduler service.

Crawler failures are recorded in crawl-run history, logged with context, and returned from API routes as structured error responses.

## Production Scaling

To extend this system for high-scale production environments, the following enhancements would be prioritized:

- **Distributed Processing**: Queue-based workers using Redis/RQ or Celery for parallelized crawling.
- **Resource Management**: Proxy rotation, request policy management, and per-source rate-limiting.
- **Advanced Observability**: Structured logging, Prometheus metrics, and automated alerting for degraded sources.
- **Database Optimization**: PostgreSQL indexes optimized for high-volume snapshot history.
- **Access Control**: Authentication layers for internal dashboard and API access.
- **CI/CD Pipeline**: Automated testing and deployment workflows for reliable updates.
