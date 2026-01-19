## Waitlist API (FastAPI + PostgreSQL)

Production-minded waitlist backend for collecting sign-ups (email + optional source), preventing duplicates, and storing entries in Postgres so you can later invite users to your app.

### What this is for

- Capture real user sign-ups to a waitlist
- Prevent duplicate emails (DB-enforced, case-insensitive)
- Provide a simple backend your main app can call (mobile/web/landing page)

### Interactive API Documentation

For a comprehensive overview of all endpoints, request/response schemas, and the ability to **test endpoints directly in your browser**, visit the Swagger UI:

**🔗 [https://waitlist-api-j29t.onrender.com/docs](https://waitlist-api-j29t.onrender.com/docs)**

> **Note:** The base URL (`https://waitlist-api-j29t.onrender.com`) returns minimal service info. Append `/docs` to access the full interactive documentation.

### API endpoints

- **GET `/`**: basic service info
- **GET `/health`**: health check (returns 503 if DB is unavailable)
- **POST `/waitlist`**: add an email to the waitlist
  - **Body**: `{ "email": "user@example.com", "source": "landing-page" }`
  - **201**: created
  - **409**: email already on the waitlist
  - **422**: invalid input
- **GET `/admin/export?key=YOUR_KEY`**: download all signups as CSV (requires `ADMIN_API_KEY`)

### Environment variables

- **`DATABASE_URL`** (required): Postgres connection string  
  Examples:
  - `postgresql://user:pass@host:5432/db`
  - `postgres://user:pass@host:5432/db`

- **`ALLOWED_ORIGINS`** (optional): Comma-separated list of allowed CORS origins  
  - Defaults to `*` (all origins allowed)
  - Example: `https://myapp.com,https://staging.myapp.com`

- **`RESEND_API_KEY`** (optional): [Resend](https://resend.com) API key for sending welcome emails  
  - If not set, emails are skipped (logged as warning)
  - Get your key at [resend.com/api-keys](https://resend.com/api-keys)

- **`EMAIL_FROM`** (optional): Sender address for welcome emails  
  - Defaults to `Waitlist <onboarding@resend.dev>`
  - For production, use your verified domain: `Waitlist <hello@yourdomain.com>`

- **`DAILY_EMAIL_LIMIT`** (optional): Max emails per day  
  - Defaults to `300`
  - Protects against runaway costs

- **`ADMIN_API_KEY`** (optional): Secret key for admin endpoints (CSV export)  
  - Required for `/admin/export` endpoint
  - Generate a secure random string (e.g., `openssl rand -hex 32`)

### Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# set DATABASE_URL for this terminal session
$env:DATABASE_URL="postgresql://user:pass@localhost:5432/db"

# create/update tables
alembic upgrade head

uvicorn app.main:app --reload
```

Open docs at **`/docs`**.

### Deploy (Render)

See `RENDER.md`.
