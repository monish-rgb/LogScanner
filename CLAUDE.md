# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

### Full Stack (Docker Compose)
```bash
docker-compose up --build    # Build and start all 3 services (db, backend, frontend)
docker-compose down          # Stop all services
```

### Frontend Only (development)
```bash
cd frontend
npm install
npm run dev       # Vite dev server on http://localhost:5000 (proxies /api to backend)
npm run build     # TypeScript check + production build
npm run lint      # ESLint
```

### Backend Only (development)
```bash
cd backend
pip install -r requirements.txt
flask db upgrade              # Run migrations
gunicorn wsgi:app             # Start server
```

### Database Migrations
```bash
cd backend
flask db migrate -m "description"   # Generate migration
flask db upgrade                     # Apply migrations
```

## Architecture

### Backend (Flask)
Three blueprints registered in `app/__init__.py`:
- **auth_bp** (`/api/auth`) — register, login, JWT issuance via Flask-JWT-Extended
- **upload_bp** (`/api`) — file upload + synchronous parsing into LogEntry records
- **dashboard_bp** (`/api/dashboard`) — file listing, paginated entries, anomaly results, AI analysis trigger

Extensions are centralized in `app/extensions.py` (db, jwt, bcrypt, migrate) and initialized in the `create_app()` factory.

**Services layer** (`app/services/`) contains business logic separate from routes:
- `upload_service` — saves files with UUID names, streams through parser, bulk-inserts entries in batches of 1000
- `analysis_service` — chunks entries (500/chunk), calls Claude API sequentially with 1s delay between chunks, parses JSON response into AnalysisResult records
- `auth_service` — user registration/authentication with bcrypt

**Parser plugin system** (`app/parsers/`): `get_parser()` reads first 10 lines to auto-detect format. Currently supports ZScaler web proxy logs in key-value, JSON, and CSV formats.

### Frontend (React + TypeScript)
- **Auth state**: React Context (`AuthContext.tsx`) stores JWT in memory (not localStorage). The Axios client in `api/client.ts` attaches the token via request interceptor and dispatches `auth:unauthorized` on 401 to trigger logout.
- **Routing**: React Router with `ProtectedRoute` wrapper that redirects unauthenticated users to `/login`.
- **Pages**: LoginPage → RegisterPage → UploadPage (drag-and-drop) → DashboardPage (file sidebar + entries table + anomaly cards).

### Data Flow
Upload → Parser extracts LogEntry rows → User clicks "Analyze with AI" → Backend chunks entries → Claude API returns anomalies as JSON → Stored as AnalysisResult records with `is_anomalous` flag on entries → Frontend displays highlighted rows + anomaly cards with severity/confidence.

## Key Configuration

- **TailwindCSS v4**: Uses `@tailwindcss/vite` plugin (not PostCSS). CSS imports via `@import "tailwindcss"`.
- **TypeScript**: `verbatimModuleSyntax: true` — must use `import type` for type-only imports.
- **Claude model**: Configured in `config.py` as `ANTHROPIC_MODEL = "claude-sonnet-4-20250514"`.
- **Vite proxy**: Dev server proxies `/api` requests to `http://localhost:5000`.
- **Nginx** (production): `frontend/nginx.conf` proxies `/api/` to `backend:5000` via Docker networking.

## Environment Variables

Copy `.env.example` to `.env`. Required:
- `ANTHROPIC_API_KEY` — needed for AI analysis
- `DB_PASSWORD` — PostgreSQL password (default: `changeme`)
- `JWT_SECRET_KEY` — JWT signing secret

## Database Models

Four models in `app/models/`: User → LogFile → LogEntry → AnalysisResult. LogFile tracks `upload_status` (processing/parsed/failed) and `analysis_status` (pending/analyzing/completed/failed). AnalysisResult links to both LogFile and optionally to the specific LogEntry flagged.
