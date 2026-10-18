"""data.py - the data and simple rules the pages share (grounds, availability, events).

Reads from playzone.db when available; falls back to in-memory sample data
otherwise.
"""
import calendar
import datetime
import os

from common import GREEN, AMBER, SLATE, ASSETS_DIR

OPEN_HOUR, CLOSE_HOUR = 6, 18
HOURS = {"Indoor Sports Hall": (6, 20)}


def ground_hours(ground):
    return HOURS.get(ground, (OPEN_HOUR, CLOSE_HOUR))


GROUNDS = [
    ("Football Ground", "Capacity: 22 Players", "football.jpg"),
    ("Basketball Court", "Capacity: 10 Players", "basketball.jpg"),
    ("Volleyball Court", "Capacity: 12 Players", "volleyball.jpg"),
    ("Indoor Sports Hall", "Capacity: 20 Players", "indoor.jpg"),
]

STATUS_STYLE = {
    "Available": (GREEN, "#dcfce7"),
    "Booked": (AMBER, "#fef3c7"),
    "Event": ("#7c3aed", "#ede9fe"),  # Purple for events
    "Closed": (SLATE, "#f1f5f9"),
}


# ------------------------------------------------------------ availability ---
def _db():
    try:
        from db import get_conn
        return get_conn()
    except Exception:
        return None


def get_event_block(ground, date):
    """
    Returns the event title if this ground is booked for a college event on this date.
    Otherwise, returns None.
    """
    conn = _db()
    if conn is None:
        return None
        
    try:
        # Events are stored as '15 September 2026' (long date)
        # We convert the Python date to match this format
        date_str = f"{date.day} {calendar.month_name[date.month]} {date.year}"
        
        # We check if the location matches the ground name, or if it's a general campus event
        # (e.g., an event located at "College Football Ground" should block the "Football Ground")
        row = conn.execute(
            "SELECT title, location FROM events "
            "WHERE date = ? AND (location LIKE ? OR location = 'All Grounds' OR location = 'Campus Wide')",
            (date_str, f"%{ground}%")
        ).fetchone()
        
        if row:
            return row["title"]
    except Exception as exc:
        print("[data] get_event_block error:", exc)
        
    return None


def booked_slots(ground, date, reservations=()):
    """Start hours already taken for this ground on this date.
    Cancelled reservations are IGNORED. Reads from the DB, then unions the
    in-memory reservations (so freshly-added bookings are considered even
    before their DB row is written)."""
    if not ground or not date:
        return set()
        
    # If there is an event, the whole ground is booked all day.
    if get_event_block(ground, date):
        return {h for h in range(24)} # Return all hours as taken

    try:
        seed = date.toordinal() + sum(ord(c) for c in ground)
        taken = {h for h in range(*ground_hours(ground))
                 if (seed + h * 7) % 5 == 0}
    except Exception as exc:
        print("[data] booked_slots seed:", exc)
        taken = set()

    # DB bookings for this ground + date (skip cancelled)
    conn = _db()
    if conn is not None:
        try:
            rows = conn.execute(
                "SELECT start_time FROM bookings "
                "WHERE ground = ? AND date = ? AND status != 'Cancelled'",
                (ground, date.isoformat())).fetchall()
            for row in rows:
                try:
                    h = int(str(row["start_time"]).split(":")[0])
                    taken.add(h)
                except (ValueError, TypeError, AttributeError):
                    pass
        except Exception as exc:
            print("[data] booked_slots:", exc)

    # in-memory fallback reservations
    for r in reservations or ():
        try:
            if (r.get("ground") == ground
                    and r.get("date") == date
                    and r.get("status") != "Cancelled"
                    and r.get("start") is not None):
                taken.add(r["start"].hour)
        except Exception as exc:
            print("[data] booked_slots bad record:", exc)

    return taken


def ground_status(ground, reservations=(), now=None):
    now = now or datetime.datetime.now()
    first, last = ground_hours(ground)
    
    # 1. Check for Event first
    if get_event_block(ground, now.date()):
        return "Event"
        
    # 2. Check if closed
    if not first <= now.hour < last:
        return "Closed"
        
    # 3. Check if booked
    if now.hour in booked_slots(ground, now.date(), reservations):
        return "Booked"
        
    return "Available"


def image_or(preferred, fallback):
    return preferred if os.path.exists(os.path.join(ASSETS_DIR, preferred)) else fallback


# ------------------------------------------------------------------ events ---
def _long_date(d):
    return f"{d.day} {calendar.month_name[d.month]} {d.year}"


def sample_events():
    """Fallback / seed list. Also used by db.py to populate the events table."""
    today = datetime.date.today()
    rows = [
        ("Inter-Class Football Tournament", "Football", 6, "9:00 AM – 4:00 PM",
         "Football Ground", "event_football.jpg"),
        ("Basketball Championship", "Basketball", 11, "10:00 AM – 3:00 PM",
         "Basketball Court", "event_basketball.jpg"),
        ("Volleyball Tournament", "Volleyball", 16, "9:00 AM – 2:00 PM",
         "Volleyball Court", "event_volleyball.jpg"),
        ("Indoor Badminton Open", "Indoor Sports", 23, "1:00 PM – 6:00 PM",
         "Indoor Sports Hall", image_or("event_badminton.jpg", "indoor.jpg")),
        ("Annual Sports Day", "Indoor Sports", -14, "8:00 AM – 5:00 PM",
         "Indoor Sports Hall", image_or("event_sportsday.jpg", "indoor.jpg")),
    ]
    return [{"title": t, "category": c, "date": _long_date(today + datetime.timedelta(days=d)),
             "time": tm, "location": loc, "organizer": "Sports Committee", "image": img}
            for t, c, d, tm, loc, img in rows]


def all_events(app_events=None):
    """Events from the DB (fallback: the list passed in)."""
    conn = _db()
    if conn is not None:
        try:
            rows = conn.execute(
                "SELECT title, category, date, time, location, organizer, "
                "image, description, admin_status FROM events").fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            print("[data] all_events:", exc)
    return list(app_events or [])


def event_date(ev):
    try:
        return datetime.datetime.strptime(ev["date"], "%d %B %Y").date()
    except (KeyError, ValueError):
        return datetime.date.max


def event_status(ev):
    return "Completed" if event_date(ev) < datetime.date.today() else "Upcoming"


def upcoming_events(events, limit=None):
    soon = sorted((e for e in events if event_status(e) == "Upcoming"), key=event_date)
    return soon[:limit] if limit else soon