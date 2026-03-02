# LogScanner

A web-based security log parser and analysis tool that uses AI to detect anomalies in web proxy logs. Built for SOC analysts and security teams who need to quickly triage large volumes of ZScaler proxy logs without manually reading thousands of logs.

Upload a log file, and LogScanner parses it, stores the entries in a database, and then runs them through Claude (Anthropic's LLM) acting as a SOC analyst. It reports suspicious entries and gives you a severity rating and explanation for each finding.

**How a request flows:**

1. User uploads a `.log`, `.txt`, or `.csv` file through the React frontend.
2. The Upload blueprint saves the file, auto-detects the format, and parses it into individual `LogEntry` rows.
3. User clicks "Analyze with AI" on the dashboard tab once logged in.
4. The Analysis service chunks all entries into groups of 500 and sends each chunk to the Claude API with a SOC analyst system prompt.
5. Claude returns a JSON array - one linked back to a specific log line with a severity, confidence score, and explanation.
6. Results are stored as `AnalysisResult` records and the matching log entries get flagged as anomalous.
7. The dashboard shows highlighted rows and anomaly cards so you can quickly see what needs attention.

---

## Tech Stack

**Frontend**

- React 19 + TypeScript
- Vite (dev server & bundler)
- TailwindCSS v4
- React Router
- Axios

**Backend**

- Python 3.12 + Flask
- SQLAlchemy (Flask-SQLAlchemy)
- Flask-JWT-Extended (auth)
- Gunicorn (WSGI server)
- Anthropic Python SDK (Claude API)

**Database & Infrastructure**

- PostgreSQL 16
- Docker Compose
- Nginx (production reverse proxy)

---

## Prerequisites

Before you start, make sure you have:

- **Docker** and **Docker Compose** installed (for the local setup)
- An **Anthropic API key**  you need this for the AI analysis feature.
- **Node.js 20+** and **npm** (only if running the frontend outside Docker)
- **Python 3.12+** and **pip** (only if running the backend outside Docker)
- **PostgreSQL 16** (only if running the database outside Docker)

---

## Setup Instructions

### Option 1: Docker (easy way and fast setup)

This is the easiest way to get everything running. Three containers (database, backend, frontend) all connected together.

1. Clone the repo:

   ```bash
   git clone https://github.com/monish-rgb/LogScanner.git
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
   docker-compose down or ctrl+c
   ```

### Option 2: Manual Setup (for development)

If you want to run things separately (useful for debugging):

**Database:**

```bash
# Start a PostgreSQL instance however you prefer, then create the database:
createdb logscanner
```

**Backend:**

```bash
cd backend
pip install -r requirements.txt

# Set environment variables
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

## AI/LLM Approach

This is what makes LogScanner useful - instead of writing static rules, it uses Claude (claude-sonnet-4-20250514) reasoning ability as a SOC analyst to catch anomalies.

### What the AI Does

The AI examines parsed log entries and classifies them into threat categories:

- **data_exfiltration** - unusually large outbound transfers
- **suspicious_url** - connections to uncategorized or sketchy domains
- **brute_force** - repeated blocked attempts from the same source
- **unusual_traffic_volume** - abnormal request patterns
- **policy_violation** - actions that break security policies
- **credential_stuffing** - mass login attempts
- **dns_tunneling** - DNS-based data exfiltration
- **unauthorized_access** - access to restricted resources

Each finding gets a confidence score (0.0 to 1.0), a severity level (low/medium/high/critical), and a short explanation.

### How It's Prompted

The system prompt tells Claude to act as a SOC analyst. Here's the example of it ( [analysis_service.py](backend/app/services/analysis_service.py)):

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

## Example Log Files for Testing

You can create test files in any of the three supported formats. Save them as `.log`, `.txt`, or `.csv` and upload through the UI only json and csv data format supported in the files

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
