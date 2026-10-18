"""db.py - the SQLite database layer.

Creates playzone.db on first run, defines the tables, seeds them with
sample data, and gives the rest of the app a single get_conn() to call.

If anything here fails (permissions, corruption, etc.), db_available()
returns False and data.py / admin_data.py fall back to the in-memory
lists they used before. So the app NEVER fails to start because of the DB.
"""
import os
import sqlite3
import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "playzone.db")


# ------------------------------------------------------------------ state ---
_conn = None
_available = None


def db_available():
    """True if the DB file exists AND we can open it."""
    global _conn, _available
    if _available is not None:
        return _available
    try:
        _conn = sqlite3.connect(DB_PATH)
        _conn.row_factory = sqlite3.Row       # rows behave like dicts
        _conn.execute("SELECT 1")
        _available = True
    except Exception as exc:
        print("[db] not available:", exc)
        _available = False
    return _available


def get_conn():
    """Return the SQLite connection (or None if the DB is not available)."""
    if db_available():
        return _conn
    return None


# --------------------------------------------------------------- schema ----
SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    id           INTEGER PRIMARY KEY CHECK (id = 1),
    name         TEXT NOT NULL,
    email        TEXT NOT NULL,
    phone        TEXT,
    role         TEXT,
    joined       TEXT,
    avatar       TEXT,
    email_notify   INTEGER DEFAULT 1,
    desktop_notify INTEGER DEFAULT 1,
    password     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    email        TEXT UNIQUE NOT NULL,
    student_id   TEXT,
    phone        TEXT,
    status       TEXT DEFAULT 'Active',
    bookings     INTEGER DEFAULT 0,
    password     TEXT
);

CREATE TABLE IF NOT EXISTS bookings (
    id           TEXT PRIMARY KEY,
    name         TEXT,
    student_id   TEXT,
    email        TEXT,
    phone        TEXT,
    purpose      TEXT,
    ground       TEXT,
    date         TEXT,               -- ISO 'YYYY-MM-DD'
    start_time   TEXT,               -- ISO 'HH:MM'
    end_time     TEXT,
    time_label   TEXT,               -- '09:00 AM – 10:00 AM'
    status       TEXT DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS events (
    title        TEXT PRIMARY KEY,
    category     TEXT,
    date         TEXT,               -- '15 September 2026'
    time         TEXT,
    location     TEXT,
    organizer    TEXT,
    image        TEXT,
    description  TEXT,
    admin_status TEXT DEFAULT 'Approved'
);

CREATE TABLE IF NOT EXISTS feedback (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user         TEXT,
    email        TEXT,
    message      TEXT,
    date         TEXT,
    rating       INTEGER,
    status       TEXT DEFAULT 'Unread'
);
"""


# --------------------------------------------------------------- seed ------
def _seed_admin(conn):
    cur = conn.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0]:
        return
    conn.execute(
        "INSERT INTO admins (id, name, email, phone, role, joined, avatar, "
        "email_notify, desktop_notify, password) "
        "VALUES (1, ?, ?, ?, ?, ?, ?, 1, 1, ?)",
        ("Tashi Lhamo", "admin@playzone.edu.bt", "+975 17 000 000",
         "Super Admin", "05 Jan 2026", "admin_avatar.jpg", "admin123"))


def _seed_users(conn):
    cur = conn.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0]:
        return
    rows = [
        ("Rinchen Dorji",  "08230178.sce@rub.edu.bt", "08230178", "Active"),
        ("Cheki Wangmo",   "08230105.sce@rub.edu.bt", "08230105", "Active"),
        ("Tashi Lhamo",    "08230212.sce@rub.edu.bt", "08230212", "Active"),
        ("Ugyen Dorji",    "08230236.sce@rub.edu.bt", "08230236", "Suspended"),
        ("Dechen Dorji",   "08230166.sce@rub.edu.bt", "08230166", "Active"),
        ("Pema Choden",    "082302154.sce@rub.edu.bt","082302154","Inactive"),
        ("Gyelyum Dema",   "082302127.sce@rub.edu.bt","082302127","Active"),
        ("Dorji Wangchuk", "082302125.sce@rub.edu.bt","082302125","Active"),
    ]
    for name, email, sid, status in rows:
        conn.execute(
            "INSERT INTO users (name, email, student_id, phone, status, "
            "bookings, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, email, sid, "+975 17 000 000", status, 0, "password123"))


def _seed_bookings(conn):
    cur = conn.execute("SELECT COUNT(*) FROM bookings")
    if cur.fetchone()[0]:
        return
    today = datetime.date.today()
    samples = [
        ("Cheki Wangmo",    "Football Ground",   0,  18, "Practice"),
        ("Ugyen Dorji",     "Basketball Court",  0,  16, "Match"),
        ("Tashi Lhamo",     "Volleyball Court",  1,  15, "Tournament"),
        ("Pema Choden",     "Indoor Sports Hall",1,  10, "Training Session"),
        ("Rinchen Dorji",   "Football Ground",   2,  14, "Practice"),
        ("Dechen Dorji",    "Basketball Court",  2,  17, "Match"),
        ("Sonam choden",    "Football Ground",   3,   9, "Practice"),
        ("Dorji Selden",    "Basketball Court",  3,  15, "Match"),
    ]
    for i, (name, ground, day_off, hour, purpose) in enumerate(samples, start=1):
        d = today + datetime.timedelta(days=day_off)
        start = f"{hour:02d}:00"
        end = f"{(hour + 1):02d}:00"
        h12 = hour % 12 or 12
        e12 = (hour + 1) % 12 or 12
        ampm = "AM" if hour < 12 else "PM"
        eampm = "AM" if hour + 1 < 12 else "PM"
        label = f"{h12:02d}:00 {ampm} – {e12:02d}:00 {eampm}"
        conn.execute(
            "INSERT OR IGNORE INTO bookings (id, name, student_id, email, "
            "phone, purpose, ground, date, start_time, end_time, time_label, "
            "status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (f"PZ-{d:%Y-%m%d}-{i:03d}", name, f"08230{100 + i:03d}",
             f"{name.split()[0].lower()}.sce@rub.edu.bt", "+975 17 000 000",
             purpose, ground, d.isoformat(), start, end, label, "Pending"))


def _seed_events(conn):
    cur = conn.execute("SELECT COUNT(*) FROM events")
    if cur.fetchone()[0]:
        return
    try:
        from data import sample_events
    except Exception:
        return
    for ev in sample_events():
        conn.execute(
            "INSERT OR IGNORE INTO events (title, category, date, time, "
            "location, organizer, image, description, admin_status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ev["title"], ev["category"], ev["date"], ev["time"],
             ev["location"], ev.get("organizer", "Sports Committee"),
             ev.get("image", "indoor.jpg"), ev.get("description", ""),
             ev.get("admin_status", "Approved")))


def _seed_feedback(conn):
    cur = conn.execute("SELECT COUNT(*) FROM feedback")
    if cur.fetchone()[0]:
        return
    rows = [
        ("Pema Choden",   "082302154.sce@rub.edu.bt",
         "Great basketball court facilities! Clean surfaces and robust hoops.",
         "10 Sep 2026", 3, "Read"),
        ("Cheki Wangmo",  "08230105.sce@rub.edu.bt",
         "Football ground needs better lighting on the east corner. We played "
         "late till 7 PM and it was really hard to track the ball during long "
         "passes. Rest is amazing!", "09 Sep 2026", 5, "Unread"),
        ("Rinchen Dorji", "08230178.sce@rub.edu.bt",
         "Booking process is very smooth. Appreciate the instant SMS confirm.",
         "08 Sep 2026", 2, "Read"),
        ("Dechen Dorji",  "08230166.sce@rub.edu.bt",
         "Volleyball nets need replacement, they are sagging near edges.",
         "08 Sep 2026", 5, "Unread"),
        ("Ugyen Dorji",   "08230236.sce@rub.edu.bt",
         "Love the new badminton hall! Excellent ventilation and mats.",
         "07 Sep 2026", 4, "Read"),
        ("Tashi Lhamo",   "08230212.sce@rub.edu.bt",
         "Sometimes difficult to find available slots after 5:00 PM.",
         "06 Sep 2026", 1, "Read"),
    ]
    for user, email, msg, date, rating, status in rows:
        conn.execute(
            "INSERT INTO feedback (user, email, message, date, rating, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user, email, msg, date, rating, status))


# --------------------------------------------------------------- init ------
def init_db(verbose=True):
    """Create the DB file + tables + seed data (only once).

    Safe to call on every startup - it does nothing if the DB already
    has data. Returns True on success, False if the DB is unavailable."""
    if not db_available():
        if verbose:
            print("[db] DB not available - the app will use in-memory data.")
        return False
    try:
        conn = get_conn()
        conn.executescript(SCHEMA)

        # --- migrations: add columns that might be missing in older DBs ---
        try:
            cols = [r[1] for r in
                    conn.execute("PRAGMA table_info(users)").fetchall()]
            if "password" not in cols:
                conn.execute("ALTER TABLE users ADD COLUMN password TEXT")
        except Exception as exc:
            print("[db] migration:", exc)

        _seed_admin(conn)
        _seed_users(conn)
        _seed_bookings(conn)
        _seed_events(conn)
        _seed_feedback(conn)

        # --- unique index so the SAME ground/date/start_time can never be
        #     double-booked while still active (cancelled rows are exempt). ---
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_slot "
                "ON bookings(ground, date, start_time) "
                "WHERE status != 'Cancelled'")
        except Exception as exc:
            print("[db] unique index:", exc)

        conn.commit()
        if verbose:
            print(f"[db] ready -> {DB_PATH}")
        return True
    except Exception as exc:
        print("[db] init failed:", exc)
        return False


# --------------------------------------------------------------- user auth ---
def find_user(email):
    """Return the users row for `email` (dict), or None."""
    conn = get_conn()
    if conn is None:
        return None
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?",
                           (email,)).fetchone()
        return dict(row) if row else None
    except Exception as exc:
        print("[db] find_user:", exc)
        return None


def create_user(name, email, password, phone="", student_id=""):
    """Insert a new user (signup). Returns (ok, message)."""
    conn = get_conn()
    if conn is None:
        return False, "Database not available."
    try:
        conn.execute(
            "INSERT INTO users (name, email, password, phone, student_id, "
            "status, bookings) VALUES (?, ?, ?, ?, ?, 'Active', 0)",
            (name, email, password, phone, student_id))
        conn.commit()
        return True, ""
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        msg = str(exc).lower()
        if "unique" in msg or "constraint" in msg:
            return False, "An account with that email already exists."
        return False, str(exc)


def check_login(email, password):
    """Return the user dict if email + password match, else None."""
    user = find_user(email)
    if user and user.get("password") == password:
        return user
    return None