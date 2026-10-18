"""admin_data.py - the admin side's data source.

READ and WRITE functions now go to playzone.db when available and fall
back to in-memory lists otherwise.

Booking dicts still expose "date" as datetime.date and "start"/"end" as
datetime.time so no page has to change.
"""
import datetime

from common import AMBER


CONFIRMED = "Confirmed"
PENDING   = "Pending"
CANCELLED = "Cancelled"

STATUS_COLOR = {
    CONFIRMED: ("#059669", "#dcfce7"),
    PENDING:   ("#d97706", "#fef3c7"),
    CANCELLED: ("#dc2626", "#fee2e2"),
}


# ------------------------------------------------------- db helper --------
def _db():
    try:
        from db import get_conn
        return get_conn()
    except Exception:
        return None


def _booking_from_row(row):
    d = dict(row)
    try:
        d["date"] = datetime.datetime.strptime(d["date"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        d["date"] = datetime.date.min
    for k in ("start_time", "end_time"):
        try:
            h, m = d[k].split(":")
            d[k.replace("_time", "")] = datetime.time(int(h), int(m))
        except (ValueError, AttributeError):
            d[k.replace("_time", "")] = None
    d["time"] = d.pop("time_label", "")
    d.pop("start_time", None)
    d.pop("end_time", None)
    return d


# -------------------------------------------------- single admin account ---
ADMIN_DEFAULTS = {
    "name":       "Tashi Lhamo",
    "email":      "admin@playzone.edu.bt",
    "phone":      "+975 17 000 000",
    "role":       "Super Admin",
    "joined":     "05 Jan 2026",
    "avatar":     "admin_avatar.jpg",
    "email_notify":   True,
    "desktop_notify": True,
    "password":   "admin123",
}

ADMIN_LOGIN_EMAIL = "admin@playzone.edu.bt"
ADMIN_LOGIN_PASSWORD = "admin123"


def ensure_admin(app):
    if not hasattr(app, "admin_profile"):
        app.admin_profile = dict(ADMIN_DEFAULTS)


def load_admin_profile(app):
    conn = _db()
    if conn is not None:
        try:
            row = conn.execute("SELECT * FROM admins WHERE id = 1").fetchone()
            if row:
                p = dict(row)
                p["email_notify"] = bool(p.get("email_notify", 1))
                p["desktop_notify"] = bool(p.get("desktop_notify", 1))
                # Guarantee every expected key exists
                for k, v in ADMIN_DEFAULTS.items():
                    p.setdefault(k, v)
                return p
        except Exception as exc:
            print("[admin_data] load_admin_profile:", exc)
    ensure_admin(app)
    return dict(app.admin_profile)


def save_admin_profile(app, updates):
    conn = _db()
    if conn is not None:
        try:
            allowed = {"name", "email", "phone", "role", "joined",
                       "avatar", "email_notify", "desktop_notify",
                       "password"}
            data = {k: v for k, v in updates.items() if k in allowed}
            if data:
                if "email_notify" in data:
                    data["email_notify"] = int(bool(data["email_notify"]))
                if "desktop_notify" in data:
                    data["desktop_notify"] = int(bool(data["desktop_notify"]))
                cols = ", ".join(f"{k} = ?" for k in data)
                vals = list(data.values()) + [1]
                conn.execute(f"UPDATE admins SET {cols} WHERE id = ?", vals)
                conn.commit()
            return load_admin_profile(app)
        except Exception as exc:
            print("[admin_data] save_admin_profile:", exc)
    ensure_admin(app)
    app.admin_profile.update(updates)
    return dict(app.admin_profile)


def change_password(app, current, new, confirm):
    p = load_admin_profile(app)
    if current != p.get("password"):
        return "Current password is incorrect."
    if len(new) < 6:
        return "New password must be at least 6 characters."
    if new != confirm:
        return "The two new passwords do not match."
    save_admin_profile(app, {"password": new})
    return None


def admin_credentials_ok(email, password):
    conn = _db()
    if conn is not None:
        try:
            row = conn.execute(
                "SELECT email, password FROM admins WHERE id = 1").fetchone()
            if row:
                return email == row["email"] and password == row["password"]
        except Exception as exc:
            print("[admin_data] admin_credentials_ok:", exc)
    return email == ADMIN_LOGIN_EMAIL and password == ADMIN_LOGIN_PASSWORD


# ------------------------------------------------------- sample bookings ---
def seed_sample_reservations(app):
    if getattr(app, "_seeded", False):
        return
    app._seeded = True
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
    reservations = getattr(app, "reservations", None)
    if reservations is None:
        reservations = app.reservations = []
    for i, (name, ground, day_off, hour, purpose) in enumerate(samples, start=1):
        d = today + datetime.timedelta(days=day_off)
        start = datetime.time(hour)
        end = datetime.time(hour + 1)
        info = {"name": name, "student_id": f"08230{100 + i:03d}",
                "email": f"{name.split()[0].lower()}.sce@rub.edu.bt",
                "phone": "+975 17 000 000", "purpose": purpose}
        record = dict(
            info,
            id=f"PZ-{d:%Y-%m%d}-{i:03d}",
            ground=ground, date=d,
            time=f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'} – "
                 f"{(hour+1) % 12 or 12}:00 {'AM' if hour+1 < 12 else 'PM'}",
            start=start, end=end, status=PENDING,
        )
        reservations.append(record)
    app._seen_bookings = {r["id"] for r in reservations}


# ------------------------------------------------------------- bookings ---
def all_bookings(app):
    conn = _db()
    if conn is not None:
        try:
            rows = conn.execute("SELECT * FROM bookings").fetchall()
            return [_booking_from_row(r) for r in rows]
        except Exception as exc:
            print("[admin_data] all_bookings:", exc)
    def _ensure(r):
        r.setdefault("status", PENDING)
        return r
    return [_ensure(r) for r in getattr(app, "reservations", [])]


def recent_bookings(app, n=6):
    bookings = all_bookings(app)
    bookings.sort(key=lambda r: r.get("id", ""), reverse=True)
    return bookings[:n]


def set_booking_status(app, booking_id, status):
    """Update status in DB (or in-memory fallback), then email the user."""
    booking = None
    for r in all_bookings(app):
        if r["id"] == booking_id:
            booking = r
            break

    conn = _db()
    if conn is not None:
        try:
            conn.execute("UPDATE bookings SET status = ? WHERE id = ?",
                         (status, booking_id))
            conn.commit()
        except Exception as exc:
            print("[admin_data] set_booking_status:", exc)
    else:
        for r in getattr(app, "reservations", []):
            if r["id"] == booking_id:
                r["status"] = status
                break

    if booking is not None:
        try:
            from email_service import notify_booking_status
            notify_booking_status(app, booking, status)
        except Exception as exc:
            print("[admin_data] email notify failed:", exc)

    return booking is not None


def booking_stats(app):
    bookings = all_bookings(app)
    by_status = {CONFIRMED: 0, PENDING: 0, CANCELLED: 0}
    by_facility = {}
    for b in bookings:
        s = b.get("status", PENDING)
        by_status[s] = by_status.get(s, 0) + 1
        by_facility[b["ground"]] = by_facility.get(b["ground"], 0) + 1
    total = len(bookings) or 1
    return {
        "total": len(bookings),
        "by_status": by_status,
        "by_facility": by_facility,
        "percent": {k: round(v * 100 / total, 1) for k, v in by_status.items()},
    }


def facility_names(app):
    seen = []
    for b in all_bookings(app):
        if b["ground"] not in seen:
            seen.append(b["ground"])
    return ["All Facilities"] + sorted(seen)


def bookings_for(app, facility="All Facilities", status="All Statuses", query=""):
    q = (query or "").strip().lower()
    out = []
    for b in all_bookings(app):
        if facility != "All Facilities" and b["ground"] != facility:
            continue
        if status != "All Statuses" and b.get("status", PENDING) != status:
            continue
        if q and q not in b["name"].lower() and q not in b["ground"].lower():
            continue
        out.append(b)
    return out


# ---------------------------------------------------------------- events ---
def all_events(app_events):
    conn = _db()
    if conn is not None:
        try:
            rows = conn.execute("SELECT * FROM events").fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            print("[admin_data] all_events:", exc)
    return list(app_events)


def add_event(app_events, ev):
    conn = _db()
    if conn is not None:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO events (title, category, date, time, "
                "location, organizer, image, description, admin_status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ev["title"], ev.get("category", ""), ev.get("date", ""),
                 ev.get("time", ""), ev.get("location", ""),
                 ev.get("organizer", "Sports Committee"),
                 ev.get("image", "indoor.jpg"), ev.get("description", ""),
                 ev.get("admin_status", "Approved")))
            conn.commit()
            return ev
        except Exception as exc:
            print("[admin_data] add_event:", exc)
    ev.setdefault("admin_status", "Approved")
    app_events.append(ev)
    return ev


def delete_event(app_events, title):
    conn = _db()
    if conn is not None:
        try:
            conn.execute("DELETE FROM events WHERE title = ?", (title,))
            conn.commit()
            return
        except Exception as exc:
            print("[admin_data] delete_event:", exc)
    app_events[:] = [e for e in app_events if e["title"] != title]


def approve_event(app_events, title):
    return _set_event_status(app_events, title, "Approved")


def reject_event(app_events, title):
    return _set_event_status(app_events, title, "Rejected")


def _set_event_status(app_events, title, status):
    conn = _db()
    if conn is not None:
        try:
            conn.execute("UPDATE events SET admin_status = ? WHERE title = ?",
                         (status, title))
            conn.commit()
            return True
        except Exception as exc:
            print("[admin_data] set_event_status:", exc)
    for e in app_events:
        if e["title"] == title:
            e["admin_status"] = status
            return True
    return False


# ----------------------------------------------------------------- users ---
def _sample_users():
    rows = [
        ("Rinchen Dorji",  "08230178.sce@rub.edu.bt", 12, "Active"),
        ("Cheki Wangmo",   "08230105.sce@rub.edu.bt",  8, "Active"),
        ("Tashi Lhamo",    "08230212.sce@rub.edu.bt", 15, "Active"),
        ("Ugyen Dorji",    "08230236.sce@rub.edu.bt",  5, "Suspended"),
        ("Dechen Dorji",   "08230166.sce@rub.edu.bt",  9, "Active"),
        ("Pema Choden",    "082302154.sce@rub.edu.bt", 3, "Inactive"),
        ("Gyelyum Dema",   "082302127.sce@rub.edu.bt",11, "Active"),
        ("Dorji Wangchuk", "082302125.sce@rub.edu.bt", 7, "Active"),
    ]
    return [{"name": n, "email": e, "student_id": f"08230{100 + i:03d}",
             "bookings": b, "status": s, "phone": "+975 17 000 000"}
            for i, (n, e, b, s) in enumerate(rows)]


USERS = _sample_users()


def all_users():
    conn = _db()
    if conn is not None:
        try:
            rows = conn.execute(
                "SELECT name, email, student_id, phone, status, bookings "
                "FROM users").fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            print("[admin_data] all_users:", exc)
    return list(USERS)


def set_user_status(email, status):
    conn = _db()
    if conn is not None:
        try:
            conn.execute("UPDATE users SET status = ? WHERE email = ?",
                         (status, email))
            conn.commit()
            return True
        except Exception as exc:
            print("[admin_data] set_user_status:", exc)
    for u in USERS:
        if u["email"] == email:
            u["status"] = status
            return True
    return False


# -------------------------------------------------------------- feedback ---
def _sample_feedback():
    rows = [
        ("Pema Choden",   "Great basketball court facilities! Clean surfaces "
                          "and robust hoops.", "10 Sep 2026", "Read",   3,
         "082302154.sce@rub.edu.bt"),
        ("Cheki Wangmo",  "Football ground needs better lighting on the east "
                          "corner. We played late till 7 PM and it was really "
                          "hard to track the ball during long passes. "
                          "Rest is amazing!", "09 Sep 2026", "Unread", 5,
         "08230105.sce@rub.edu.bt"),
        ("Rinchen Dorji", "Booking process is very smooth. Appreciate the "
                          "instant SMS confirm.", "08 Sep 2026", "Read",   2,
         "08230178.sce@rub.edu.bt"),
        ("Dechen Dorji",  "Volleyball nets need replacement, they are sagging "
                          "near edges.", "08 Sep 2026", "Unread", 5,
         "08230166.sce@rub.edu.bt"),
        ("Ugyen Dorji",   "Love the new badminton hall! Excellent ventilation "
                          "and mats.", "07 Sep 2026", "Read",   4,
         "08230236.sce@rub.edu.bt"),
        ("Tashi Lhamo",   "Sometimes difficult to find available slots after "
                          "5:00 PM.", "06 Sep 2026", "Read",   1,
         "08230212.sce@rub.edu.bt"),
    ]
    return [{"user": u, "message": m, "date": d, "status": s,
             "rating": r, "email": e}
            for u, m, d, s, r, e in rows]


FEEDBACK = _sample_feedback()


def all_feedback():
    conn = _db()
    if conn is not None:
        try:
            rows = conn.execute(
                "SELECT id, user, email, message, date, rating, status "
                "FROM feedback ORDER BY id").fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            print("[admin_data] all_feedback:", exc)
    return list(FEEDBACK)


def mark_feedback_read(index):
    rows = all_feedback()
    if not (0 <= index < len(rows)):
        return
    row_id = rows[index].get("id")
    conn = _db()
    if conn is not None and row_id is not None:
        try:
            conn.execute("UPDATE feedback SET status = 'Read' WHERE id = ?",
                         (row_id,))
            conn.commit()
            return
        except Exception as exc:
            print("[admin_data] mark_feedback_read:", exc)
    if 0 <= index < len(FEEDBACK):
        FEEDBACK[index]["status"] = "Read"


# ------------------------------------------------------ notifications ------
SYSTEM_NOTIFICATIONS = [
    ("New booking request received from Jamyang Yangzom for Badminton Hall.",
     "10 mins ago", AMBER),
    ("Reminder: \"Inter-Class Basketball Tournament\" starts in 2 hours.",
     "1 hour ago", "#2563eb"),
    ("Booking #BK-8740 has been cancelled by the system (unresolved payment).",
     "3 hours ago", "#ef4444"),
    ("Scheduled Alert: Football Ground is closed tomorrow from 08:00 AM to 12:00 PM.",
     "5 hours ago", "#94a3b8"),
]


def collect_notifications(app):
    items = []
    seen = getattr(app, "_seen_bookings", set())
    for r in getattr(app, "reservations", []):
        if r["id"] in seen:
            continue
        items.append({
            "text": f"New booking request from {r['name']} for {r['ground']}.",
            "when": "just now",
            "dot":  "#2563eb",
            "kind": "booking",
            "target": ("booking", None),
        })
        seen.add(r["id"])
    app._seen_bookings = seen
    for text, when, dot in SYSTEM_NOTIFICATIONS:
        items.append({"text": text, "when": when, "dot": dot,
                      "kind": "system", "target": None})
    return items


def notifications():
    return list(SYSTEM_NOTIFICATIONS)