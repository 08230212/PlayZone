"""my_bookings.py - the "My Bookings" page for the logged-in user.

Reads from playzone.db when available; falls back to the in-memory list.
Only shows bookings whose email matches the current user's email.
"""
import datetime
import tkinter as tk
from tkinter import messagebox

from common import *
from about import PHONE, EMAIL
from admin_data import STATUS_COLOR, CONFIRMED, PENDING, CANCELLED
from reservation import pretty_date


CANCEL_WINDOW = datetime.timedelta(hours=2)


def _row_to_booking(row):
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


class MyBookingsPage(SectionPage):
    def __init__(self, app):
        super().__init__(app, "my_bookings")

        def F(size, bold=False):
            return tkfont.Font(family=app.family, size=-size,
                               weight="bold" if bold else "normal")
        self.f.update({"h3": F(20, True), "cap": F(10, True),
                       "val": F(13, True)})

        self._header()
        self.list_body = self.section(SOFT_BG, top=20, bottom=56)
        self._cards_holder = tk.Frame(self.list_body, bg=SOFT_BG)
        self._cards_holder.pack(fill="x")
        self._footer()

    def on_show(self, **kwargs):
        super().on_show(**kwargs)
        self._render()
        self.after(50, self._render)

    def _header(self):
        body = self.section(WHITE, top=40, bottom=16)
        Pill(body, "YOUR RESERVATIONS", self.app.f_badge, BLUE,
             BLUE_SOFT).pack(anchor="w")
        tk.Label(body, text="My Bookings", font=self.f["h1"], fg=NAVY,
                 bg=WHITE).pack(anchor="w", pady=(8, 0))
        p = tk.Label(body, justify="left", anchor="w", font=self.f["p"],
                     fg=SLATE, bg=WHITE,
                     text="View and manage the grounds you have reserved. "
                          "You can cancel a pending booking up to 2 hours "
                          "before its start time. Once the sports office has "
                          "confirmed a booking, please contact them directly "
                          "to change or cancel it.")
        p.pack(anchor="w", pady=(10, 0))
        self.wrap(p, None, 0, 760)

    def _my_reservations(self):
        """Show the user's own bookings (3 most recent), matched by email only."""
        user = getattr(self.app, "user", None) or {}
        email = (user.get("email") or "").strip().lower()

        if not email:
            return []

        every = []
        try:
            from db import get_conn
            conn = get_conn()
            if conn is not None:
                every = [_row_to_booking(r) for r in
                         conn.execute("SELECT * FROM bookings").fetchall()]
        except Exception as exc:
            print("[my_bookings] db read failed:", exc)

        if not every:
            every = list(getattr(self.app, "reservations", []))

        mine = [r for r in every
                if (r.get("email") or "").strip().lower() == email]

        mine.sort(key=lambda r: r.get("date", datetime.date.min), reverse=True)
        return mine[:3]

    def _start_dt(self, r):
        d = r.get("date")
        t = r.get("start")
        if isinstance(d, datetime.date) and isinstance(t, datetime.time):
            return datetime.datetime.combine(d, t)
        return None

    def _is_past(self, r):
        dt = self._start_dt(r)
        return dt is not None and dt < datetime.datetime.now()

    def _can_cancel(self, r):
        if r.get("status") != PENDING:
            return False
        dt = self._start_dt(r)
        if dt is None:
            return False
        return dt - datetime.datetime.now() > CANCEL_WINDOW

    def _render(self):
        if not self._cards_holder.winfo_exists():
            return
        for w in self._cards_holder.winfo_children():
            w.destroy()

        rows = self._my_reservations()
        if not rows:
            tk.Label(self._cards_holder,
                     text="You have no bookings yet. Reserve a ground from "
                          "the Home or Reservation page.",
                     font=self.f["p"], fg=SLATE, bg=SOFT_BG,
                     justify="left").pack(anchor="w", pady=30)
            return

        cards = []
        for r in rows:
            cards.append(self._card(r))
        self.reflow(self._cards_holder, cards, lambda w: 2 if w >= 1000 else 1)

    def _card(self, r):
        c = Card(self._cards_holder, SOFT_BG, pad=18)
        inner = c.inner

        top = tk.Frame(inner, bg=WHITE)
        top.pack(fill="x")
        tk.Label(top, text=r.get("id", ""), font=self.f["small"], fg=BLUE,
                 bg=WHITE).pack(side="left")
        status = r.get("status", PENDING)
        shown_status = "Completed" if self._is_past(r) else status
        colour_map = dict(STATUS_COLOR)
        colour_map["Completed"] = (SLATE, "#f1f5f9")
        fg, bg = colour_map.get(shown_status, (SLATE, "#f1f5f9"))
        Pill(top, shown_status, self.f["small"], fg, bg, parent_bg=WHITE,
             padx=10, pady=4).pack(side="right")

        tk.Label(inner, text=r.get("ground", "—"), font=self.f["card_t"],
                 fg=NAVY, bg=WHITE, anchor="w").pack(anchor="w",
                                                      pady=(10, 4))

        d = r.get("date")
        date_txt = pretty_date(d) if isinstance(d, datetime.date) else "—"
        tk.Label(inner, text=f"🗓  {date_txt}  •  {r.get('time', '—')}",
                 font=self.f["small"], fg=SLATE, bg=WHITE,
                 anchor="w").pack(anchor="w")
        tk.Label(inner, text=f"🏆  {r.get('purpose', '—')}",
                 font=self.f["small"], fg=SLATE, bg=WHITE,
                 anchor="w").pack(anchor="w", pady=(2, 0))

        bottom = tk.Frame(inner, bg=WHITE)
        bottom.pack(fill="x", pady=(14, 0))

        if self._can_cancel(r):
            WideButton(bottom, "Cancel Booking",
                       lambda rr=r: self._confirm_cancel(rr),
                       height=38, radius=8, bg=WHITE, hover="#fee2e2",
                       fg="#dc2626", outline="#dc2626",
                       font=self.f["btn"]).pack(side="right")
        elif self._is_past(r):
            tk.Label(bottom, text="This booking is in the past.",
                     font=self.f["small"], fg=SLATE, bg=WHITE
                     ).pack(side="left")
        elif status == CONFIRMED:
            tk.Label(bottom,
                     text="Approved booking — contact the sports office to "
                          "change or cancel.",
                     font=self.f["small"], fg=SLATE, bg=WHITE, justify="left",
                     wraplength=420, anchor="w").pack(side="left")
        elif status == PENDING:
            tk.Label(bottom,
                     text="Too close to start — contact the sports office "
                          "to cancel.",
                     font=self.f["small"], fg=SLATE, bg=WHITE, justify="left",
                     wraplength=420, anchor="w").pack(side="left")
        elif status == CANCELLED:
            tk.Label(bottom, text="This booking has been cancelled.",
                     font=self.f["small"], fg=SLATE, bg=WHITE
                     ).pack(side="left")

        hover_card(c)
        return c

    def _confirm_cancel(self, r):
        d = r.get("date")
        date_txt = pretty_date(d) if isinstance(d, datetime.date) else "—"
        ok = messagebox.askyesno(
            "Cancel Booking",
            f"Cancel your booking for {r.get('ground', '—')}\n"
            f"{date_txt}  •  {r.get('time', '—')}?\n\n"
            "The slot will be released for others.", parent=self)
        if not ok:
            return

        saved = False
        try:
            from db import get_conn
            conn = get_conn()
            if conn is not None:
                conn.execute(
                    "UPDATE bookings SET status = 'Cancelled' WHERE id = ?",
                    (r.get("id"),))
                conn.commit()
                saved = True
        except Exception as exc:
            print("[my_bookings] cancel write failed:", exc)

        for rr in getattr(self.app, "reservations", []):
            if rr.get("id") == r.get("id"):
                rr["status"] = CANCELLED

        print(f"[cancel] {r.get('id')} cancelled by user "
              f"({'db' if saved else 'memory'})")
        self.app._notif_unread = 1
        self._render()

    def _footer(self):
        body = self.section(NAVY_DARK, top=44, bottom=22)
        top = tk.Frame(body, bg=NAVY_DARK)
        top.pack(fill="x")

        left = tk.Frame(top, bg=NAVY_DARK)
        brand = tk.Frame(left, bg=NAVY_DARK)
        brand.pack(anchor="w")
        LogoMark(brand, 36, parent_bg=NAVY_DARK).pack(side="left")
        txt = tk.Frame(brand, bg=NAVY_DARK)
        txt.pack(side="left", padx=(10, 0))
        tk.Label(txt, text="PLAY ZONE", font=self.app.f_brand, fg=WHITE,
                 bg=NAVY_DARK).pack(anchor="w")
        tk.Label(txt, text="BOOK. PLAY. ENJOY.", font=self.app.f_tag,
                 fg=GREEN, bg=NAVY_DARK).pack(anchor="w")
        tk.Label(left, text="Your one-stop portal for booking campus sports\n"
                            "grounds and joining college events.",
                 font=self.f["foot"], fg="#94a3b8", bg=NAVY_DARK,
                 justify="left").pack(anchor="w", pady=(12, 0))

        right = tk.Frame(top, bg=NAVY_DARK)
        tk.Label(right, text="CAMPUS CONTACT", font=self.f["tag"], fg=WHITE,
                 bg=NAVY_DARK).pack(anchor="w")
        for glyph, value in (("☎", PHONE), ("✉", EMAIL)):
            row = tk.Frame(right, bg=NAVY_DARK)
            row.pack(anchor="w", pady=(10, 0))
            tk.Label(row, text=glyph, font=self.f["foot"], fg=BLUE,
                     bg=NAVY_DARK).pack(side="left")
            tk.Label(row, text=value, font=self.f["foot"], fg="#94a3b8",
                     bg=NAVY_DARK).pack(side="left", padx=(8, 0))
        self.reflow(top, [left, right], lambda w: 2 if w >= 700 else 1,
                    sticky="nw")

        tk.Frame(body, bg="#1e293b", height=1).pack(fill="x", pady=(28, 12))
        bottom = tk.Frame(body, bg=NAVY_DARK)
        bottom.pack(fill="x")
        tk.Label(bottom, text=f"© {datetime.date.today().year} Play Zone. "
                              f"All rights reserved.",
                 font=self.f["small"], fg="#64748b",
                 bg=NAVY_DARK).pack(side="left")
        for text in ("Terms of Use", "Privacy Policy"):
            lb = tk.Label(bottom, text=text, font=self.f["small"],
                          fg="#64748b", bg=NAVY_DARK)
            lb.pack(side="right", padx=(16, 0))
            hover_label(lb, "#64748b", WHITE)


if __name__ == "__main__":
    import login
    login.App().mainloop()