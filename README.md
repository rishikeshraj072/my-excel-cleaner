# Excel CMS / Data Management Platform

A production-ready Flask web application that serves as a Data Management Platform (CMS) for Excel files using a hybrid relational/schemaless approach. Relational attributes are indexed physically, while custom columns discovered dynamically across uploaded spreadsheets are cataloged in a `field_registry` and stored inside a MySQL 8 `JSON` column in `master_records`.

---

## Technical Stack
* **Backend**: Python 3.11, Flask, SQLAlchemy ORM, Pandas, OpenPyXL, PyMySQL
* **Database**: MySQL 8 (requires native JSON support and path indexing)
* **Frontend**: Bootstrap 5 (Dark Glassmorphic design), Fetch API (Vanilla JS AJAX)

---

## Directory Structure
```text
c:\Rishi-code\my-excel\
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Environment configurations
│   ├── extensions.py         # SQLAlchemy instance
│   ├── utils.py              # Text normalizer utility
│   ├── models/               # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── user.py           # User model (cms_users table)
│   │   ├── file.py           # UploadedFile model
│   │   ├── field.py          # FieldRegistry & FieldAlias models
│   │   └── record.py         # MasterRecord model (master_records table)
│   ├── repositories/         # Direct DB Queries & Mutations (Data Access Layer)
│   │   ├── __init__.py
│   │   ├── user_repo.py
│   │   ├── file_repo.py
│   │   ├── field_repo.py
│   │   └── record_repo.py
│   ├── services/             # Pure Business Logic Services
│   │   ├── __init__.py
│   │   ├── auth_service.py   # Hashing and User Auth verification
│   │   ├── registry_service.py # Custom fields and alias operations
│   │   └── excel_service.py  # Ingestion pipeline, mapping & batch insertion
│   ├── routes/               # Blueprints (Thin controllers)
│   │   ├── __init__.py
│   │   ├── auth.py           # Login / Register
│   │   ├── main.py           # HTML view routers
│   │   └── api.py            # JSON REST endpoints
│   ├── static/               # Assets
│   │   ├── css/
│   │   │   └── style.css     # Dark mode & glassmorphism theme styling
│   │   └── js/
│   │       └── app.js        # Search controller, Details modal & AJAX upload
│   └── templates/            # Jinja2 Layout Templates
│       ├── base.html
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html
│       ├── registry.html
│       ├── aliases.html
│       └── history.html
├── run.py                    # Entry point for development server
├── seed.py                   # Schema creation & default seeder script
├── verify_ingestion.py       # Automated testing & verification script
├── requirements.txt          # Python packages list
└── .env                      # Application environment variables
```

---

## Setup & Running Guide

### 1. Database Configuration
Ensure MySQL 8 is running. By default, the application is pre-configured to connect to the local database `excel_cleaner_db` using:
* **Host**: `localhost`
* **User**: `excel_cleaner_app`
* **Password**: `excelapppass`

You can customize this in the `.env` file at the root:
```ini
SECRET_KEY=c3be9d9a1f2e3d4c5b6a7f8e9d0c1b2a
DATABASE_URL=mysql+pymysql://excel_cleaner_app:excelapppass@localhost:3306/excel_cleaner_db
FLASK_ENV=development
```

### 2. Install Dependencies
Run:
```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations and Seeding
Initialize the database tables and populate the admin account and default column mapping configurations:
```bash
python seed.py
```
* **Default Admin Account**:
  * **Username**: `admin`
  * **Password**: `adminpassword`

### 4. Run Development Server
Boot the web interface:
```bash
python run.py
```
Access the application at `http://127.0.0.1:5000`.

---

## Verification & Automated Testing
To run the automated verification pipeline, run:
```bash
python verify_ingestion.py
```
This script will:
1. Programmatically generate a mock Excel file containing both standard and custom columns.
2. Ingest the file using the Pandas batch reader.
3. Validate that standard attributes map to structured columns and dynamic ones map into the custom JSON payload.
4. Execute SQL relational filters and native MySQL 8 JSON path extract queries to confirm complete query precision.
5. Cleanup test data automatically.
