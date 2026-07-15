# Smart RFID Jewelry Inventory System

A professional ERP-style jewelry inventory management system built with Flask. Manages Gold and Silver inventory separately with RFID tracking, QR code generation, audit trails, and CSV export.

Live Demo: [https://smart-jewelry-rfid.onrender.com](https://smart-jewelry-rfid.onrender.com)

---

## Features

### ERP Dashboard
- Fixed sidebar navigation with active page highlighting
- Gold/Silver/Total stat cards (items, weight, value)
- Quick-action cards for inventory and adding items
- Responsive layout with collapsible sidebar on mobile

### Gold & Silver Inventory
- Separate tracking for Gold and Silver jewelry
- Filter tabs (All / Gold / Silver) on inventory page
- Metal type badges with color-coded indicators
- `/inventory/gold` and `/inventory/silver` quick-filter routes

### Jewelry Management
- Add new items with RFID ID, name, metal type, weight, purity, price
- Edit existing records with pre-selected values
- Delete items with confirmation dialog
- Duplicate RFID detection

### RFID Scanning
- Scan or enter RFID ID to look up item details
- Displays QR code, metal type, weight, purity, price, status
- "Item Not Found" feedback for invalid RFID lookups

### QR Code System
- Auto-generates QR codes when items are added
- QR thumbnails in inventory table
- Printable QR labels with metal type, purity, weight
- Bulk QR code regeneration

### Sales & Reporting
- Sales history page with sold items and timestamps
- CSV export with metal type filter support
- Audit log tracking all system actions (add, edit, delete, sold, scan, export)

### Security
- CSRF protection on all forms (Flask-WTF)
- Password hashing with Werkzeug (scrypt)
- Password change functionality
- Environment-based secret key (.env)
- Session timeout (24 hours)
- Secure file path handling

### UX
- Flash messages for all actions (success, error, warning, info)
- Confirmation dialogs on destructive actions (delete, mark sold)
- Input validation with error feedback
- Custom 404/500 error pages
- Pagination on inventory, sales, and audit pages
- Print-optimized invoice layout

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask, SQLAlchemy |
| Database | SQLite |
| Auth | Flask-Login, Werkzeug (password hashing) |
| Security | Flask-WTF (CSRF), python-dotenv |
| Frontend | HTML5, CSS3, Bootstrap Icons |
| QR Codes | qrcode, Pillow |

---

## Project Structure

```
smart-jewelry-rfid/
├── app.py                  # Flask application, routes, models
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (SECRET_KEY, FLASK_DEBUG)
├── .gitignore
│
├── static/
│   ├── css/
│   │   └── style.css       # Full theme: sidebar, ERP layout, components
│   └── qrcodes/            # Auto-generated QR code images
│
├── templates/
│   ├── base.html           # ERP layout: sidebar + topbar + content
│   ├── login.html          # Login page (standalone)
│   ├── home.html           # Dashboard with gold/silver/total stats
│   ├── inventory.html      # Inventory table with filters, pagination
│   ├── add_jewelry.html    # Add new item form
│   ├── edit.html           # Edit item form
│   ├── scan.html           # RFID scanner with lookup
│   ├── bill.html           # Invoice with print button
│   ├── print_qr.html       # Printable QR label (standalone)
│   ├── sales.html          # Sales history with pagination
│   ├── audit.html          # Audit log with pagination
│   ├── change_password.html # Password change form
│   └── error.html          # Custom 404/500 error page
│
└── instance/
    └── jewelry.db          # SQLite database (auto-created)
```

---

## Installation

### Clone

```bash
git clone https://github.com/sunilvivek/smart-jewelry-rfid.git
cd smart-jewelry-rfid
```

### Virtual Environment

```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in the project root:

```
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=true
FLASK_PORT=8000
```

### Run

```bash
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

**Default login:** `admin` / `balaji123` (change password after first login)

---

## Database Schema

### Jewelry Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| rfid_id | String(100) | Unique RFID identifier |
| ornament_name | String(100) | Item name |
| metal_type | String(20) | "Gold" or "Silver" |
| weight | Float | Weight in grams |
| purity | String(20) | e.g. 22K, 916, Silver 925 |
| price | Float | Price in INR |
| status | String(20) | "Available" or "Sold" |
| created_at | DateTime | Timestamp when added |
| updated_at | DateTime | Last modified timestamp |

### AuditLog Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| timestamp | DateTime | When the action occurred |
| user | String(100) | Username who performed action |
| action | String(50) | Action type (add_item, edit_item, delete_item, mark_sold, scan_item, export_csv, etc.) |
| details | String(500) | Human-readable description |
| item_id | Integer | Related jewelry item ID |

### Admin Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| username | String(100) | Unique username |
| password | String(255) | Hashed password (scrypt) |

---

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/login` | GET/POST | Admin login |
| `/logout` | GET | Logout |
| `/` | GET | Dashboard with stats |
| `/inventory` | GET | Inventory with filters, search, pagination |
| `/inventory/gold` | GET | Redirect to gold-filtered inventory |
| `/inventory/silver` | GET | Redirect to silver-filtered inventory |
| `/add` | GET/POST | Add new jewelry item |
| `/edit/<id>` | GET/POST | Edit existing item |
| `/delete/<id>` | POST | Delete item |
| `/sold/<id>` | POST | Mark item as sold |
| `/scan` | GET/POST | RFID scanner |
| `/bill/<id>` | GET | Invoice page |
| `/print_qr/<id>` | GET | Printable QR label |
| `/generate_all_qr` | GET | Regenerate all QR codes |
| `/export/csv` | GET | Download CSV export |
| `/sales` | GET | Sales history |
| `/audit` | GET | Audit log |
| `/change-password` | GET/POST | Change admin password |

---

## Screenshots

### ERP Sidebar Navigation
- Fixed dark sidebar with gold accents
- Section labels: Inventory, Actions, Reports, System
- Active page indicator with gold left border
- Collapsible on mobile with hamburger toggle

### Dashboard
- 3x3 grid of gold/silver/total stat cards
- Quick-action cards for Gold Inventory, Silver Inventory, Add Jewelry

### Inventory
- Filter tabs: All / Gold / Silver
- Metal type badges (gold gradient / silver gradient)
- Search by RFID, name, metal, purity, status
- Pagination (20 items per page)
- CSV export button

---

## License

This project is developed for educational and academic purposes.

---

## Author

**Sunil Vivek**

B.Tech Computer Science Engineering (Cybersecurity)

SRM Institute of Science and Technology

GitHub: [https://github.com/sunilvivek](https://github.com/sunilvivek)
