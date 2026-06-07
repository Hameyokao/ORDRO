import sqlite3
import hashlib
import os
import binascii
from pathlib import Path
from datetime import datetime, date
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "assets" / "uploads"
DB_PATH = DATA_DIR / "ordro.db"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def execute(query, params=()):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return cur.lastrowid


def query_df(query, params=()):
    with connect() as conn:
        return pd.read_sql_query(query, conn, params=params)


def scalar(query, params=(), default=0):
    df = query_df(query, params)
    if df.empty:
        return default
    value = df.iloc[0, 0]
    return default if value is None else value


def _columns(table):
    with connect() as conn:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows}


def _add_column(table, col_def):
    col_name = col_def.split()[0]
    if col_name not in _columns(table):
        execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")


_PBKDF2_ITER = 120_000


def hash_password(plain: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", str(plain).encode(), salt, _PBKDF2_ITER)
    return f"pbkdf2${_PBKDF2_ITER}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"


def verify_password(stored: str, plain: str) -> bool:
    stored = stored or ""
    if stored.startswith("pbkdf2$"):
        try:
            _, iter_s, salt_hex, hash_hex = stored.split("$")
            salt = binascii.unhexlify(salt_hex)
            dk = hashlib.pbkdf2_hmac("sha256", str(plain).encode(), salt, int(iter_s))
            return binascii.hexlify(dk).decode() == hash_hex
        except Exception:
            return False
    return stored == str(plain)


def is_hashed(stored: str) -> bool:
    return bool(stored) and stored.startswith("pbkdf2$")


def record_activity(username, full_name, role, action, entity="", entity_id=None, detail=""):
    try:
        execute(
            """INSERT INTO activity_log (ts, username, full_name, role, action, entity, entity_id, detail)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                datetime.now().isoformat(timespec="seconds"),
                username or "system",
                full_name or "",
                role or "",
                action or "",
                entity or "",
                None if entity_id in (None, "") else int(entity_id),
                detail or "",
            ),
        )
    except Exception:
        pass


def today_iso() -> str:
    """Return today's local date as ISO string. Use instead of SQLite date('now') to avoid UTC drift."""
    return date.today().isoformat()

def fmt_date(dt_str, show_time: bool = True) -> str:
    """Format an ISO datetime/date string to DD-MM-YY [HH:MM]."""
    if not dt_str:
        return "—"
    s = str(dt_str).strip()
    if not s or s.lower() == "nan":
        return "—"
    try:
        if "T" in s:
            date_part, time_part = s.split("T", 1)
        elif " " in s[:19]:
            parts = s.split(" ", 1)
            date_part, time_part = parts[0], parts[1] if len(parts) > 1 else ""
        else:
            date_part, time_part = s, ""
        y, m, d = date_part[:10].split("-")
        result = f"{d}-{m}-{y[-2:]}"
        if show_time and time_part:
            result += f"  {time_part[:5]}"
        return result
    except Exception:
        return s[:16]


def init_db():
    with connect() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            full_name TEXT,
            active INTEGER DEFAULT 1
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            sku TEXT,
            cost REAL DEFAULT 0,
            price REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 5,
            image_path TEXT,
            supplier_id INTEGER,
            active INTEGER DEFAULT 1,
            created_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            city TEXT,
            address TEXT,
            notes TEXT,
            created_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            notes TEXT,
            created_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT,
            created_at TEXT,
            delivered_at TEXT,
            customer_id INTEGER,
            customer_name TEXT,
            customer_phone TEXT,
            customer_city TEXT,
            customer_address TEXT,
            order_type TEXT DEFAULT 'Delivery',
            payment_method TEXT,
            payment_status TEXT DEFAULT 'Unpaid',
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            assigned_to TEXT,
            seller TEXT,
            payment_verification_image TEXT,
            payment_slip_no TEXT,
            notes TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            product_image TEXT,
            qty INTEGER,
            unit_price REAL,
            unit_cost REAL,
            line_total REAL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            recurring INTEGER DEFAULT 0,
            created_by TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS payment_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            image_path TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            username TEXT,
            full_name TEXT,
            role TEXT,
            action TEXT,
            entity TEXT,
            entity_id INTEGER,
            detail TEXT
        )''')
        conn.commit()

    _add_column("customers", "city TEXT")
    _add_column("products", "supplier_id INTEGER")
    _add_column("orders", "customer_city TEXT")
    _add_column("orders", "payment_status TEXT DEFAULT 'Unpaid'")
    _add_column("orders", "payment_verification_image TEXT")
    _add_column("orders", "payment_slip_no TEXT")
    _add_column("orders", "seller TEXT")
    _add_column("orders", "delivered_at TEXT")
    _add_column("expenses", "created_by TEXT")
    _add_column("expenses", "recurring INTEGER DEFAULT 0")

    seed_defaults()
    _upgrade_plaintext_passwords()


def _upgrade_plaintext_passwords():
    try:
        rows = query_df("SELECT id, password FROM users")
    except Exception:
        return
    for _, r in rows.iterrows():
        pw = r["password"]
        if not is_hashed(pw or ""):
            execute("UPDATE users SET password=? WHERE id=?", (hash_password(pw or ""), int(r["id"])))


def seed_defaults():
    users = query_df("SELECT COUNT(*) AS count FROM users")['count'][0]
    if users == 0:
        # Super Admin is always seeded first with fixed username "Administrator"
        execute("INSERT INTO users (username,password,role,full_name) VALUES (?,?,?,?)",
                ("Administrator", hash_password("admin123"), "Super Admin", "Administrator"))
        execute("INSERT INTO users (username,password,role,full_name) VALUES (?,?,?,?)",
                ("admin", hash_password("admin123"), "Admin", "Admin"))
        execute("INSERT INTO users (username,password,role,full_name) VALUES (?,?,?,?)",
                ("staff", hash_password("staff123"), "Staff", "Staff User"))
        execute("INSERT INTO users (username,password,role,full_name) VALUES (?,?,?,?)",
                ("delivery", hash_password("delivery123"), "Delivery", "Delivery User"))
    else:
        # Ensure a Super Admin always exists; create one if none found
        sa = query_df("SELECT COUNT(*) AS c FROM users WHERE role='Super Admin'")
        if sa.iloc[0]['c'] == 0:
            execute("INSERT OR IGNORE INTO users (username,password,role,full_name) VALUES (?,?,?,?)",
                    ("Administrator", hash_password("admin123"), "Super Admin", "Administrator"))

    defaults = {
        "tax_percent":        "0",
        "currency":           "MVR",
        "business_name":      "Your Business Name",
        "business_logo":      "",
        "theme_name":         "Cloud White",
        "accent_color":       "Royal Blue",
        "banner_theme":       "Corner Glow",
        "business_address":   "",
        "business_phone":     "",
        "business_email":     "",
        "business_website":   "",
        "facebook_id":        "",
        "instagram_id":       "",
        "tiktok_id":          "",
        "whatsapp_contact":   "",
        "viber_contact":      "",
    }
    for k, v in defaults.items():
        if scalar("SELECT COUNT(*) FROM settings WHERE key=?", (k,), default=0) == 0:
            execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (k, v))


def get_setting(key, default=""):
    df = query_df("SELECT value FROM settings WHERE key=?", (key,))
    return default if df.empty else df.iloc[0]['value']


def set_setting(key, value):
    execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, str(value)))


def next_order_no():
    last_id = scalar("SELECT COALESCE(MAX(id),0) FROM orders", default=0)
    return f"ORD-{int(last_id) + 1:04d}-{datetime.now().strftime('%y')}"
