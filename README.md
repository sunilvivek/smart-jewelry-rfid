# Smart RFID Jewelry Inventory System

A production-ready, Dockerized Flask ERP for jewelry shop management. Tracks Gold & Silver inventory with RFID, QR codes, customer CRM, sales, repairs, invoices, and full audit trails.

Live Demo: [https://smart-jewelry-rfid.onrender.com](https://smart-jewelry-rfid.onrender.com)

---

## Quick Start (Docker)

```bash
git clone https://github.com/sunilvivek/smart-jewelry-rfid.git
cd smart-jewelry-rfid
cp .env.example .env
# Edit .env — set SECRET_KEY to a random string
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000)

**Default login:** `admin` / `balaji123`

---

## Quick Start (Local)

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
python app.py
```

---

## Docker

### Build & Run

```bash
docker compose up --build
```

### Background Mode

```bash
docker compose up -d
docker compose logs -f          # watch logs
docker compose down             # stop
```

### Rebuild After Changes

```bash
docker compose up --build --force-recreate
```

### Data Persistence

SQLite database and QR codes are stored in Docker volumes (`app_data`, `app_qr`). Data survives container restarts.

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (random) | Flask secret key — **change in production** |
| `FLASK_CONFIG` | `development` | Config preset: `development`, `production`, `testing` |
| `DATABASE_URL` | `sqlite:///jewelry.db` | Database URI (SQLite default, PostgreSQL-ready) |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode (dev only) |
| `SESSION_COOKIE_SECURE` | `false` | Require HTTPS for cookies (set `true` in production) |
| `SESSION_COOKIE_HTTPONLY` | `true` | Prevent JavaScript access to cookies |
| `SESSION_COOKIE_SAMESITE` | `Lax` | CSRF cookie policy |

---

## Architecture

```
smart-jewelry-rfid/
├── app.py              # Flask app factory, routes, models, helpers
├── config.py           # Dev / Prod / Test configuration classes
├── wsgi.py             # Gunicorn entry point
├── requirements.txt    # Python dependencies
├── Dockerfile          # Production Docker image
├── docker-compose.yml  # Container orchestration
├── .env.example        # Environment variable template
├── .gitignore
│
├── static/
│   ├── css/
│   │   └── style.css   # Full ERP theme (sidebar, components, responsive)
│   └── qrcodes/        # Auto-generated QR code images
│
├── templates/          # 23 Jinja2 templates
│   ├── base.html       # ERP layout: sidebar + topbar + content
│   ├── login.html
│   ├── home.html       # Dashboard with gold/silver/total stats
│   ├── inventory.html  # Inventory with filters, search, pagination
│   ├── add_jewelry.html
│   ├── edit.html
│   ├── scan.html       # RFID scanner
│   ├── sell.html       # Sale form (customer picker)
│   ├── sale_detail.html
│   ├── bill.html       # Printable invoice
│   ├── print_qr.html
│   ├── customers.html
│   ├── add_customer.html
│   ├── edit_customer.html
│   ├── customer_profile.html
│   ├── repairs.html
│   ├── add_repair.html
│   ├── edit_repair.html
│   ├── repair_detail.html
│   ├── sales.html      # Sales history
│   ├── audit.html      # Audit log
│   ├── change_password.html
│   └── error.html      # 404/500
│
└── instance/
    └── jewelry.db      # SQLite database (auto-created)
```

---

## Features

### ERP Dashboard
- Fixed sidebar with gold accents and section labels
- Gold / Silver / Total stat cards (items, weight, value)
- Quick-action navigation

### Inventory Management
- Separate Gold & Silver tracking with filter tabs
- Add / Edit / Delete with validation
- Duplicate RFID detection
- CSV export with metal filter
- Pagination (20 items/page)

### RFID & QR Codes
- RFID scanner with lookup
- Auto-generated QR codes on item creation
- Printable QR labels
- Bulk QR regeneration

### Customer CRM
- Full customer database (name, phone, email, address)
- Auto-generated customer IDs (CUST000001)
- Search across all fields
- Customer profile with purchase & repair history

### Sales & Invoices
- Customer-linked sales with invoice numbers (INV000001)
- Payment method tracking (Cash / Card / UPI / Bank Transfer)
- Printable invoices with customer details
- Sales history with search

### Repairs
- Repair tracking with status workflow (Pending → In Progress → Completed)
- Customer association, estimated vs actual cost
- Auto-completion timestamp
- Status filter tabs with counts

### Security
- CSRF protection (Flask-WTF)
- Password hashing (Werkzeug scrypt)
- Environment-based secrets
- Session timeout (24h)
- Secure file path handling
- Audit logging for all operations

### UX
- Flash messages (success / error / warning / info)
- Confirmation dialogs on destructive actions
- Custom 404/500 error pages
- Print-optimized invoice layout
- Responsive sidebar with mobile hamburger menu

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Flask, SQLAlchemy |
| Database | SQLite (PostgreSQL-ready config) |
| Auth | Flask-Login, Werkzeug password hashing |
| Security | Flask-WTF (CSRF), python-dotenv |
| Frontend | HTML5, CSS3, Bootstrap Icons |
| QR Codes | qrcode, Pillow |
| Production | Gunicorn, Docker |

---

## Database Schema

| Table | Key Columns |
|-------|------------|
| **Jewelry** | id, rfid_id, ornament_name, metal_type, weight, purity, price, status, created_at, updated_at |
| **Customer** | id, customer_id, full_name, phone_number, email, address, city, state, pincode, notes |
| **Sale** | id, invoice_number, jewelry_id (FK), customer_id (FK), sale_price, payment_method, sale_date |
| **Repair** | id, repair_id, customer_id (FK), jewelry_name, description, estimated_cost, actual_cost, status, received_date, completed_date |
| **AuditLog** | id, timestamp, user, action, details, item_id |
| **Admin** | id, username, password |

---

## Deployment

### Render (Blueprint — recommended)
1. Go to [render.com](https://render.com) → Sign in with GitHub
2. Click **"New +"** → **"Blueprint"**
3. Connect repo: `sunilvivek/smart-jewelry-rfid`
4. Render detects `render.yaml` and auto-creates:
   - **Web service** (Python 3.12 + Gunicorn)
   - **PostgreSQL database** (free tier)
   - `SECRET_KEY` auto-generated, `DATABASE_URL` auto-linked
5. Click **Deploy** — build takes ~2 minutes
6. Once live, click the service URL (e.g. `https://smart-jewelry-rfid.onrender.com`)

**Note:** Free tier spins down after 15 min idle. First request after idle takes ~30s (cold start).

### Render (Manual)
1. **New Web Service** → Connect GitHub repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn wsgi:app`
4. Set env vars:
   - `FLASK_CONFIG=production`
   - `SECRET_KEY=<random string>`
   - `DATABASE_URL=<your PostgreSQL connection string>`
5. **New PostgreSQL** database → Copy connection string → Set as `DATABASE_URL`

### Railway / DigitalOcean
1. Connect repo
2. Set `FLASK_CONFIG=production`
3. Railway auto-detects Dockerfile

### VPS (Docker)
```bash
ssh your-server
git clone https://github.com/sunilvivek/smart-jewelry-rfid.git
cd smart-jewelry-rfid
cp .env.example .env
nano .env                    # set SECRET_KEY
docker compose up -d --build
```

### PostgreSQL Migration
Change `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://user:pass@localhost:5432/jewelry_db
```
Install `psycopg2-binary` and add to requirements.txt. No code changes needed.

---

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/login` | GET/POST | Admin login |
| `/logout` | GET | Logout |
| `/` | GET | Dashboard |
| `/inventory` | GET | Inventory (search, filter, paginate) |
| `/inventory/gold` | GET | Gold-filtered inventory |
| `/inventory/silver` | GET | Silver-filtered inventory |
| `/add` | GET/POST | Add jewelry item |
| `/edit/<id>` | GET/POST | Edit item |
| `/delete/<id>` | POST | Delete item |
| `/sold/<id>` | GET/POST | Sell item (customer picker + sale form) |
| `/scan` | GET/POST | RFID scanner |
| `/bill/<id>` | GET | Invoice |
| `/print_qr/<id>` | GET | Printable QR label |
| `/generate_all_qr` | GET | Regenerate all QR codes |
| `/export/csv` | GET | CSV export |
| `/sales` | GET | Sales history |
| `/sales/<id>` | GET | Sale detail / invoice |
| `/customers` | GET | Customer list |
| `/customers/add` | GET/POST | Add customer |
| `/customers/<id>` | GET | Customer profile |
| `/customers/edit/<id>` | GET/POST | Edit customer |
| `/customers/delete/<id>` | POST | Delete customer |
| `/repairs` | GET | Repair list |
| `/repairs/add` | GET/POST | Add repair |
| `/repairs/<id>` | GET | Repair detail |
| `/repairs/edit/<id>` | GET/POST | Edit repair |
| `/repairs/delete/<id>` | POST | Delete repair |
| `/audit` | GET | Audit log |
| `/change-password` | GET/POST | Change admin password |

---

## License

This project is developed for educational and academic purposes.

---

## Author

**Sunil Vivek**

B.Tech Computer Science Engineering (Cybersecurity)

SRM Institute of Science and Technology

GitHub: [https://github.com/sunilvivek](https://github.com/sunilvivek)
