## Waitlist API (FastAPI + PostgreSQL)

Production-minded waitlist backend for collecting sign-ups (name, email, Nigerian phone number, source of entry), preventing duplicates, sending automated welcome emails, and storing entries in Postgres.

### What this is for

- Capture real user sign-ups to a waitlist (Nigeria-focused)
- Prevent duplicate emails AND phone numbers (DB-enforced)
- Send personalized welcome emails automatically
- Provide a simple backend your main app can call (mobile/web/landing page)
- Export signups to CSV for your team

### Interactive API Documentation

For a comprehensive overview of all endpoints, request/response schemas, and the ability to **test endpoints directly in your browser**, visit the Swagger UI:

**🔗https://waitlist-api-kh5c.vercel.app/docs**

> **Note:** Append `/docs` to your deployed URL to access the full interactive documentation.

### API endpoints

- **GET `/`**: basic service info
- **GET `/health`**: health check (returns 503 if DB is unavailable)
- **POST `/waitlist`**: add a user to the waitlist
  - **Body**:
    ```json
    {
      "first_name": "Chidi",
      "last_name": "Okonkwo",
      "email": "chidi@example.com",
      "phone": "08012345678",
      "source": "landing-page"
    }
    ```
  - Phone accepts: `08012345678`, `+2348012345678`, `080-1234-5678`
  - **201**: created (+ welcome email sent)
  - **409**: email or phone already on the waitlist
  - **422**: invalid input (bad email/phone format)
- **GET `/admin/export?key=YOUR_KEY`**: download all signups as CSV (requires `ADMIN_API_KEY`)

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | Postgres connection string (Neon, Supabase, etc.) |
| `RESEND_API_KEY` | ❌ | [Resend](https://resend.com) API key for welcome emails |
| `EMAIL_FROM` | ❌ | Sender address (default: `Waitlist <onboarding@resend.dev>`) |
| `ADMIN_API_KEY` | ❌ | Secret key for `/admin/export` endpoint |
| `ALLOWED_ORIGINS` | ❌ | CORS origins (default: `*` allows all) |

### Run locally

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
$env:DATABASE_URL="postgresql://user:pass@localhost:5432/db"

# Run database migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

Open docs at **http://localhost:8000/docs**

---

## Deploy to Vercel (with Neon Postgres)

### 1. Create a Neon Database

1. Go to [neon.tech](https://neon.tech) and create a free account
2. Create a new project
3. Copy the connection string from **Dashboard → Connect**
   - Format: `postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require`

### 2. Run Migrations (one-time setup)

Before deploying, run migrations locally against your Neon database:

```powershell
# Set your Neon connection string
$env:DATABASE_URL="postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require"

# Run migrations
alembic upgrade head
```

### 3. Deploy to Vercel

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com) → Import Project
3. Select your repository
4. Add environment variables:
   - `DATABASE_URL` = your Neon connection string
   - `RESEND_API_KEY` = your Resend API key (optional)
   - `ADMIN_API_KEY` = any secure random string (optional)
5. Deploy!

Your API will be live at `https://your-project.vercel.app`

### 4. Verify Deployment

```bash
# Health check
curl https://your-project.vercel.app/health

# Test signup
curl -X POST https://your-project.vercel.app/waitlist \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"User","email":"test@example.com","phone":"08012345678"}'
```

---

## Legacy: Deploy to Render

See `RENDER.md` for Docker-based deployment to Render.

---

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Neon / Render / Supabase)
- **Email**: Resend
- **Hosting**: Vercel (serverless) or Render (Docker)
- **Migrations**: Alembic
