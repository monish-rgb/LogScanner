# LogScanner

A web-based security log analysis tool that uses AI to detect anomalies in web proxy logs. Built for SOC analysts and security teams who need to quickly triage large volumes of ZScaler proxy logs without manually reading thousands of lines.

Upload a log file, and LogScanner parses it, stores the entries in a database, and then runs them through Claude (Anthropic's LLM) acting as a SOC analyst. It flags suspicious entries — things like data exfiltration, brute force attempts, malware communication — and gives you a severity rating and plain-English explanation for each finding.

---

## Architecture

```
┌────────────────────┐         ┌─────────────────────────────────────────────────┐
│                    │  HTTP   │              Backend (Flask)                    │
│   React Frontend   │────────>│                                                │
│   (Nginx in prod)  │  /api/* │  ┌──────────┐  ┌───────────┐  ┌────────────┐  │
│                    │<────────│  │ Auth      │  │ Upload    │  │ Dashboard  │  │
│  - Login/Register  │         │  │ Blueprint │  │ Blueprint │  │ Blueprint  │  │
│  - File Upload     │         │  └──────────┘  └─────┬─────┘  └──────┬─────┘  │
│  - Dashboard       │         │                      │               │         │
│  - Anomaly Cards   │         │               ┌──────▼──────┐  ┌─────▼──────┐  │
└────────────────────┘         │               │   Parser    │  │  Analysis  │  │
                               │               │   Service   │  │  Service   │  │
                               │               └──────┬──────┘  └─────┬──────┘  │
                               │                      │               │         │
                               └──────────────────────┼───────────────┼─────────┘
                                                      │               │
                                              ┌───────▼───────┐  ┌───▼──────────┐
                                              │  PostgreSQL   │  │ Claude API   │
                                              │  (log data,   │  │ (anomaly     │
                                              │   users,      │  │  detection)  │
                                              │   results)    │  │              │
                                              └───────────────┘  └──────────────┘
```

**How a request flows:**

1. User uploads a `.log`, `.txt`, or `.csv` file through the React frontend.
2. The Upload blueprint saves the file, auto-detects the format, and parses it into individual `LogEntry` rows (batched in groups of 1000).
3. User clicks "Analyze with AI" on the dashboard.
4. The Analysis service chunks all entries into groups of 500 and sends each chunk to the Claude API with a SOC analyst system prompt.
5. Claude returns a JSON array of anomalies — each one linked back to a specific log line with a severity, confidence score, and explanation.
6. Results are stored as `AnalysisResult` records and the matching log entries get flagged as anomalous.
7. The dashboard shows highlighted rows and anomaly cards so you can quickly see what needs attention.

---

## Tech Stack

| Layer      | Technology              | Version   |
|------------|-------------------------|-----------|
| Frontend   | React                   | 19.2.0    |
| Frontend   | TypeScript              | 5.9.3     |
| Frontend   | Vite                    | 7.3.1     |
| Frontend   | TailwindCSS             | 4.2.1     |
| Frontend   | React Router            | 7.13.1    |
| Frontend   | Axios                   | 1.13.5    |
| Backend    | Python                  | 3.12      |
| Backend    | Flask                   | 3.1.0     |
| Backend    | SQLAlchemy              | (via Flask-SQLAlchemy 3.1.1) |
| Backend    | Flask-JWT-Extended      | 4.7.1     |
| Backend    | Gunicorn                | 23.0.0    |
| Backend    | Anthropic Python SDK    | 0.42.0    |
| Database   | PostgreSQL              | 16        |
| Infra      | Docker Compose          | 3.9       |
| Infra      | Nginx                   | alpine    |

---

## Prerequisites

Before you start, make sure you have:

- **Docker** and **Docker Compose** installed (for the containerized setup)
- An **Anthropic API key** — you need this for the AI analysis feature. Get one at [console.anthropic.com](https://console.anthropic.com/)
- **Node.js 20+** and **npm** (only if running the frontend outside Docker)
- **Python 3.12+** and **pip** (only if running the backend outside Docker)
- **PostgreSQL 16** (only if running the database outside Docker)

---

## Setup Instructions

### Option 1: Docker (recommended)

This is the easiest way to get everything running. Three containers — database, backend, frontend — all wired together.

1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/LogScanner.git
   cd LogScanner
   ```

2. Create a `.env` file in the project root (copy from the example):
   ```bash
   cp .env.example .env
   ```

3. Open `.env` and fill in your values:
   ```
   DB_PASSWORD=changeme
   JWT_SECRET_KEY=pick-something-random-here
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

4. Build and start everything:
   ```bash
   docker-compose up --build
   ```

5. Once it's up:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:5000](http://localhost:5000)
   - PostgreSQL: `localhost:5432`

6. To stop:
   ```bash
   docker-compose down
   ```

### Option 2: Manual Setup (for development)

If you want to run things separately (useful for debugging or working on just the frontend/backend):

**Database:**
```bash
# Start a PostgreSQL instance however you prefer, then create the database:
createdb logscanner
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt

# Set environment variables (or use a .env file)
export DATABASE_URL=postgresql://localhost:5432/logscanner
export JWT_SECRET_KEY=dev-secret
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# Run migrations and start the server
flask db upgrade
gunicorn wsgi:app --bind 0.0.0.0:5000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

The Vite dev server starts on `http://localhost:5173` and proxies `/api` requests to the Flask backend at `http://localhost:5000`.

---

## Environment Variables

| Variable              | Required | Default       | Description                                                        |
|-----------------------|----------|---------------|--------------------------------------------------------------------|
| `ANTHROPIC_API_KEY`   | Yes      | —             | Your Anthropic API key for Claude. Without it, AI analysis won't work. |
| `DB_PASSWORD`         | Yes      | —             | Password for the PostgreSQL database.                              |
| `JWT_SECRET_KEY`      | Yes      | `dev-secret`  | Secret used to sign JWT tokens. Use something strong in production. |
| `DATABASE_URL`        | No       | Built from `DB_PASSWORD` | Full PostgreSQL connection string. Docker sets this automatically. |
| `FLASK_ENV`           | No       | `development` | `development` or `production`. Controls debug mode.                |
| `MAX_UPLOAD_SIZE_MB`  | No       | `100`         | Max file upload size in megabytes.                                 |
| `UPLOAD_FOLDER`       | No       | `uploads`     | Directory where uploaded log files are stored.                     |
| `ANTHROPIC_MODEL`     | No       | `claude-sonnet-4-20250514` | Which Claude model to use for analysis.               |

---

## API Documentation

All endpoints except auth require a JWT token in the `Authorization: Bearer <token>` header.

### Authentication

#### Register
```
POST /api/auth/register
```
```json
// Request
{
  "username": "analyst1",
  "email": "analyst1@company.com",
  "password": "securepassword"
}

// Response (201)
{
  "id": 1,
  "username": "analyst1",
  "email": "analyst1@company.com",
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### Login
```
POST /api/auth/login
```
```json
// Request
{
  "username": "analyst1",
  "password": "securepassword"
}

// Response (200)
{
  "access_token": "eyJhbGciOi...",
  "user": {
    "id": 1,
    "username": "analyst1",
    "email": "analyst1@company.com",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### Get Current User
```
GET /api/auth/me
Authorization: Bearer <token>

// Response (200)
{
  "id": 1,
  "username": "analyst1",
  "email": "analyst1@company.com",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### File Upload

#### Upload a Log File
```
POST /api/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

// Form field: "file" (accepts .log, .txt, .csv — max 100MB)

// Response (202)
{
  "file_id": 1,
  "original_filename": "proxy_logs_jan.log",
  "entry_count": 0,
  "upload_status": "processing",
  "analysis_status": "pending"
}
```

#### Check Upload Status
```
GET /api/upload/1/status
Authorization: Bearer <token>

// Response (200)
{
  "file_id": 1,
  "upload_status": "parsed",
  "analysis_status": "pending",
  "entry_count": 4523
}
```

### Dashboard

#### List Uploaded Files
```
GET /api/dashboard/files?page=1&per_page=10
Authorization: Bearer <token>

// Response (200)
{
  "files": [
    {
      "id": 1,
      "original_filename": "proxy_logs_jan.log",
      "file_size": 2048576,
      "entry_count": 4523,
      "upload_status": "parsed",
      "analysis_status": "completed",
      "uploaded_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

#### Get Log Entries (paginated)
```
GET /api/dashboard/files/1/entries?page=1&per_page=50&anomalous_only=false
Authorization: Bearer <token>

// Response (200)
{
  "entries": [
    {
      "id": 1,
      "line_number": 1,
      "timestamp": "2025-01-15T10:30:45Z",
      "source_ip": "192.168.1.100",
      "destination_url": "https://example.com",
      "user": "john.doe@company.com",
      "action": "ALLOWED",
      "risk_score": 25,
      "bytes_transferred": 50000,
      "is_anomalous": false,
      "raw_line": "..."
    }
  ],
  "total": 4523,
  "page": 1,
  "per_page": 50,
  "pages": 91
}
```

#### Trigger AI Analysis
```
POST /api/dashboard/files/1/analyze
Authorization: Bearer <token>

// Response (200)
{
  "status": "completed",
  "anomalies_found": 12
}
```

#### Get Anomalies
```
GET /api/dashboard/files/1/anomalies
Authorization: Bearer <token>

// Response (200)
{
  "anomalies": [
    {
      "id": 1,
      "log_entry_id": 42,
      "anomaly_type": "data_exfiltration",
      "confidence_score": 0.92,
      "severity": "high",
      "explanation": "Unusually large outbound transfer of 45MB to an uncategorized external host during off-hours.",
      "created_at": "2025-01-15T11:00:00Z"
    }
  ],
  "total": 12
}
```

#### Get Analysis Summary
```
GET /api/dashboard/files/1/summary
Authorization: Bearer <token>

// Response (200)
{
  "total_entries": 4523,
  "total_anomalies": 12,
  "severity_breakdown": {
    "low": 3,
    "medium": 5,
    "high": 3,
    "critical": 1
  },
  "top_anomaly_types": [
    { "type": "data_exfiltration", "count": 4 },
    { "type": "suspicious_url", "count": 3 }
  ],
  "analysis_status": "completed"
}
```

---

## AI/LLM Approach

This is the core of what makes LogScanner useful — instead of writing static rules, it uses Claude as a SOC analyst to catch things that pattern matching would miss.

### What the AI Does

The AI examines parsed log entries and classifies them into threat categories:

- **data_exfiltration** — unusually large outbound transfers
- **suspicious_url** — connections to uncategorized or sketchy domains
- **brute_force** — repeated blocked attempts from the same source
- **unusual_traffic_volume** — abnormal request patterns
- **policy_violation** — actions that break security policies
- **malware_communication** — C2-like traffic patterns
- **credential_stuffing** — mass login attempts
- **dns_tunneling** — DNS-based data exfiltration
- **unauthorized_access** — access to restricted resources

Each finding gets a confidence score (0.0–1.0), a severity level (low/medium/high/critical), and a short explanation in plain English.

### How It's Prompted

The system prompt tells Claude to act as a SOC analyst. Here's the gist of it (the full prompt lives in [analysis_service.py](backend/app/services/analysis_service.py)):

```
You are a Security Operations Center (SOC) analyst AI assistant.
You analyze web proxy log entries to detect security anomalies.
```

It then asks for output as a strict JSON array:
```json
[
  {
    "line_number": 42,
    "anomaly_type": "data_exfiltration",
    "confidence_score": 0.92,
    "severity": "high",
    "explanation": "Unusually large outbound transfer of 45MB to an uncategorized external host."
  }
]
```

The prompt specifically tells Claude what to look for:
- Large data transfers (bytes_transferred)
- Connections to suspicious/uncategorized URLs
- Repeated blocked actions from the same source
- High risk scores
- Abnormal response times
- Patterns suggesting data exfiltration
- Repeated failed attempts from the same user or IP

### How Entries Are Sent to the AI

Log entries are formatted into a compact single-line format to fit more context per API call:

```
[Line 123] ts=2025-01-15 10:30:45 src=192.168.1.100 url=https://example.com user=john.doe action=ALLOWED category=news risk=25 bytes=50000 resp_ms=150 dept=sales location=office proto=HTTPS method=GET status=200
```

Entries are chunked into groups of **500** and sent sequentially to the API with a **1-second delay** between chunks to stay within rate limits. The model used is `claude-sonnet-4-20250514` with a max token output of 4096.

### Where in the Code

| What                        | File                                                                 | Function                     |
|-----------------------------|----------------------------------------------------------------------|------------------------------|
| System prompt + API call    | [analysis_service.py](backend/app/services/analysis_service.py)      | `analyze_log_file()`         |
| Entry formatting            | [analysis_service.py](backend/app/services/analysis_service.py)      | `format_entries_for_prompt()` |
| Response JSON parsing       | [analysis_service.py](backend/app/services/analysis_service.py)      | `parse_claude_response()`    |
| Chunking logic              | [chunking.py](backend/app/utils/chunking.py)                        | `chunk_log_entries()`        |
| Analysis trigger endpoint   | [dashboard.py](backend/app/blueprints/dashboard.py)                  | `analyze_file()`             |
| Model config                | [config.py](backend/config.py)                                       | `ANTHROPIC_MODEL`            |

---

## Example Log Files for Testing

You can create test files in any of the three supported formats. Save them as `.log`, `.txt`, or `.csv` and upload through the UI.

### ZScaler Key-Value Format (.log)

```
datetime=2025-01-15 08:23:14 clientip=10.0.15.201 url=https://docs.google.com/spreadsheets/d/abc123 login=maria.chen@company.com action=ALLOWED urlcategory=Web-based Email pagerisk=10 transactionsize=2048 clienttranstime=85 department=Engineering location=HQ protocol=HTTPS requestmethod=GET serverip=142.250.80.46 responsesize=1950 requestsize=512 statuscode=200 contenttype=text/html useragent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) threatname=None threatclass=None threatcategory=None threatseverity=None filetype=None fileclass=None
datetime=2025-01-15 08:24:01 clientip=10.0.15.201 url=https://mega.nz/file/xyz789 login=maria.chen@company.com action=ALLOWED urlcategory=File Sharing pagerisk=75 transactionsize=48500000 clienttranstime=32000 department=Engineering location=HQ protocol=HTTPS requestmethod=POST serverip=31.216.148.12 responsesize=200 requestsize=48500000 statuscode=200 contenttype=application/octet-stream useragent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) threatname=None threatclass=None threatcategory=None threatseverity=None filetype=None fileclass=None
datetime=2025-01-15 08:24:45 clientip=10.0.22.87 url=https://pastebin.com/raw/abc456 login=david.kim@company.com action=BLOCKED urlcategory=Uncategorized pagerisk=90 transactionsize=0 clienttranstime=15 department=Finance location=Remote protocol=HTTPS requestmethod=GET serverip=104.20.67.143 responsesize=0 requestsize=350 statuscode=403 contenttype=None useragent=curl/7.81.0 threatname=None threatclass=None threatcategory=None threatseverity=None filetype=None fileclass=None
datetime=2025-01-15 08:25:30 clientip=10.0.22.87 url=https://pastebin.com/raw/def789 login=david.kim@company.com action=BLOCKED urlcategory=Uncategorized pagerisk=90 transactionsize=0 clienttranstime=12 department=Finance location=Remote protocol=HTTPS requestmethod=GET serverip=104.20.67.143 responsesize=0 requestsize=340 statuscode=403 contenttype=None useragent=curl/7.81.0 threatname=None threatclass=None threatcategory=None threatseverity=None filetype=None fileclass=None
datetime=2025-01-15 08:26:00 clientip=10.0.22.87 url=https://pastebin.com/raw/ghi012 login=david.kim@company.com action=BLOCKED urlcategory=Uncategorized pagerisk=90 transactionsize=0 clienttranstime=14 department=Finance location=Remote protocol=HTTPS requestmethod=GET serverip=104.20.67.143 responsesize=0 requestsize=355 statuscode=403 contenttype=None useragent=curl/7.81.0 threatname=None threatclass=None threatcategory=None threatseverity=None filetype=None fileclass=None
datetime=2025-01-15 08:30:00 clientip=10.0.8.45 url=https://outlook.office365.com/owa login=sarah.jones@company.com action=ALLOWED urlcategory=Web-based Email pagerisk=5 transactionsize=4096 clienttranstime=120 department=Marketing location=HQ protocol=HTTPS requestmethod=GET serverip=52.96.166.130 responsesize=3800 requestsize=296 statuscode=200 contenttype=text/html useragent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) threatname=None threatclass=None threatcategory=None threatseverity=None filetype=None fileclass=None
```

This sample includes a few things the AI should catch:
- Line 2: A 48MB upload to mega.nz (file sharing site) — potential data exfiltration
- Lines 3–5: Repeated blocked requests to pastebin using `curl` from a Finance user — suspicious pattern

### ZScaler CSV Format (.csv)

```csv
01/15/2025,08:23:14,ALLOWED,maria.chen@company.com,Engineering,HQ,10.0.15.201,docs.google.com,HTTPS,200,GET,text/html,512,1950,Web-based Email,10,Mozilla/5.0 (Windows NT 10.0; Win64; x64),https://docs.google.com/spreadsheets/d/abc123
01/15/2025,08:24:01,ALLOWED,maria.chen@company.com,Engineering,HQ,10.0.15.201,mega.nz,HTTPS,200,POST,application/octet-stream,48500000,200,File Sharing,75,Mozilla/5.0 (Windows NT 10.0; Win64; x64),https://mega.nz/file/xyz789
01/15/2025,08:31:00,BLOCKED,unknown@external.com,Unknown,Unknown,203.0.113.50,internal-wiki.company.com,HTTPS,403,GET,None,500,0,Corporate,95,python-requests/2.28.1,https://internal-wiki.company.com/api/secrets
01/15/2025,08:31:02,BLOCKED,unknown@external.com,Unknown,Unknown,203.0.113.50,internal-wiki.company.com,HTTPS,403,GET,None,500,0,Corporate,95,python-requests/2.28.1,https://internal-wiki.company.com/api/users
01/15/2025,08:31:05,BLOCKED,unknown@external.com,Unknown,Unknown,203.0.113.50,internal-wiki.company.com,HTTPS,403,POST,None,12000,0,Corporate,95,python-requests/2.28.1,https://internal-wiki.company.com/api/admin
```

### ZScaler JSON Format (.log)

```json
{"datetime": "2025-01-15 09:00:00", "clientip": "10.0.5.12", "url": "https://github.com/company/repo", "login": "alex.dev@company.com", "action": "ALLOWED", "urlcategory": "Professional Services", "pagerisk": "5", "transactionsize": "15000", "clienttranstime": "200", "department": "Engineering", "location": "HQ", "protocol": "HTTPS", "requestmethod": "GET", "serverip": "140.82.121.4", "responsesize": "14500", "requestsize": "500", "statuscode": "200", "contenttype": "text/html", "useragent": "Mozilla/5.0", "threatname": "None", "threatclass": "None", "threatcategory": "None", "threatseverity": "None", "filetype": "None", "fileclass": "None"}
{"datetime": "2025-01-15 09:01:30", "clientip": "10.0.5.12", "url": "https://transfer.sh/random123", "login": "alex.dev@company.com", "action": "ALLOWED", "urlcategory": "Uncategorized", "pagerisk": "80", "transactionsize": "95000000", "clienttranstime": "45000", "department": "Engineering", "location": "HQ", "protocol": "HTTPS", "requestmethod": "PUT", "serverip": "144.76.136.153", "responsesize": "150", "requestsize": "95000000", "statuscode": "200", "contenttype": "application/octet-stream", "useragent": "curl/8.1.2", "threatname": "None", "threatclass": "None", "threatcategory": "None", "threatseverity": "None", "filetype": "None", "fileclass": "None"}
```

The JSON example has a 95MB upload to transfer.sh via `curl` — a textbook data exfiltration pattern.

---

## Project Structure

```
LogScanner/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── wsgi.py
│   ├── config.py
│   ├── app/
│   │   ├── __init__.py            # Flask app factory
│   │   ├── extensions.py          # db, jwt, bcrypt, migrate
│   │   ├── blueprints/
│   │   │   ├── auth.py            # /api/auth endpoints
│   │   │   ├── upload.py          # /api/upload endpoints
│   │   │   └── dashboard.py       # /api/dashboard endpoints
│   │   ├── models/
│   │   │   ├── user.py            # User model
│   │   │   ├── log_file.py        # LogFile model
│   │   │   ├── log_entry.py       # LogEntry model (30+ fields)
│   │   │   └── analysis_result.py # AnalysisResult model
│   │   ├── services/
│   │   │   ├── auth_service.py    # Registration + login logic
│   │   │   ├── upload_service.py  # File saving + parsing
│   │   │   └── analysis_service.py# Claude API integration
│   │   ├── parsers/
│   │   │   ├── __init__.py        # Auto-detection (get_parser)
│   │   │   └── zscaler_parser.py  # JSON, CSV, key-value parsing
│   │   └── utils/
│   │       └── chunking.py        # Entry chunking for AI
│   └── migrations/                # Alembic migrations
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                # Routes
│       ├── api/
│       │   ├── client.ts          # Axios instance + interceptors
│       │   ├── auth.ts
│       │   ├── upload.ts
│       │   └── dashboard.ts
│       ├── context/
│       │   └── AuthContext.tsx     # JWT stored in memory
│       ├── pages/
│       │   ├── LoginPage.tsx
│       │   ├── RegisterPage.tsx
│       │   ├── UploadPage.tsx
│       │   └── DashboardPage.tsx
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Navbar.tsx
│       │   │   └── ProtectedRoute.tsx
│       │   ├── dashboard/
│       │   │   ├── LogTable.tsx
│       │   │   ├── AnomalyCard.tsx
│       │   │   ├── SummaryStats.tsx
│       │   │   ├── SeverityBadge.tsx
│       │   │   └── ConfidenceBadge.tsx
│       │   └── upload/
│       │       ├── DropZone.tsx
│       │       └── ProgressBar.tsx
│       └── types/
│           ├── auth.ts
│           ├── logEntry.ts
│           └── analysis.ts
└── README.md
```

---

## License

This project is for educational and internal use. See LICENSE file for details.
