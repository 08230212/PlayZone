"""admin_dashboard.py - the admin Dashboard.

Welcome header, five stat cards, Recent Bookings (live from app.reservations,
i.e. whatever the user side booked), and a Booking Status donut.
"""
import tkinter as tk

from common import *
from admin_shell import AdminPage, PAGE_BG
from admin_data import (recent_bookings, booking_stats, STATUS_COLOR,
                        CONFIRMED, PENDING, CANCELLED)


STAT_BREAKS = [(1180, 5), (820, 3), (560, 2), (0, 1)]


class DashboardPage(AdminPage):
    def build(self):
        self.body = tk.Frame(self, bg=PAGE_BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=24)
        self._header()
        self._stats()
        self._tables()
        self.after(60, lambda: self.on_reflow(self.winfo_width()))

    def on_show(self, **kwargs):
        if getattr(self, "_built", False):
            for w in self.body.winfo_children():
                w.destroy()
            self._header()
            self._stats()
            self._tables()
            self.after(60, lambda: self.on_reflow(self.winfo_width()))

    # ------------------------------------------------------------------
    def _header(self):
        head = tk.Frame(self.body, bg=PAGE_BG)
        head.pack(fill="x", pady=(0, 22))
        tk.Label(head, text="Welcome back, Tashi!", font=self.f["h1"],
                 fg=NAVY, bg=PAGE_BG).pack(anchor="w")
        tk.Label(head, text="Here's what is happening at the sports complex today.",
                 font=self.f["p"], fg=SLATE, bg=PAGE_BG).pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------------
    def _stats(self):
        stats = booking_stats(self.app)
        pf = stats["by_facility"]
        cards = [
            ("Total Bookings",   stats["total"],                  "+12% this week", True),
            ("Basketball Court", pf.get("Basketball Court", 0),   "+4% this week",  True),
            ("Football Ground",  pf.get("Football Ground", 0),    "+18% this week", True),
            ("Volleyball Court", pf.get("Volleyball Court", 0),   "-2% this week",  False),
            ("Badminton Hall",   pf.get("Indoor Sports Hall", 0), "+8% this week",  True),
        ]
        self._stat_holder = tk.Frame(self.body, bg=PAGE_BG)
        self._stat_holder.pack(fill="x", pady=(0, 22))
        self._stat_cards = []
        for label, value, delta, up in cards:
            card = Card(self._stat_holder, PAGE_BG, pad=18, border="#e5e7eb")
            inner = card.inner
            top = tk.Frame(inner, bg=WHITE)
            top.pack(fill="x")
            tk.Label(top, text=label, font=self.f["p"], fg=SLATE,
                     bg=WHITE).pack(side="left")
            ic = tk.Canvas(top, width=24, height=24, bg=WHITE,
                           highlightthickness=0)
            round_rect(ic, 0, 0, 24, 24, 6, fill=BLUE_HOVER, outline=BLUE_HOVER)
            ic.create_text(12, 12, text="🕘", fill=BLUE, font=self.f["small"])
            ic.pack(side="right")
            tk.Label(inner, text=str(value),
                     font=("TkDefaultFont", -26, "bold"),
                     fg=NAVY, bg=WHITE).pack(anchor="w", pady=(10, 4))
            tk.Label(inner, text=delta, font=self.f["small"],
                     fg="#10b981" if up else "#ef4444",
                     bg=WHITE).pack(anchor="w")
            self._stat_cards.append(card)

    # ------------------------------------------------------------------
    def _tables(self):
        split = tk.Frame(self.body, bg=PAGE_BG)
        split.pack(fill="both", expand=True)
        split.grid_rowconfigure(0, weight=1)
        split.grid_columnconfigure(0, weight=3, uniform="dash")
        split.grid_columnconfigure(1, weight=2, uniform="dash")
        self._split = split
        self._recent_card(split)
        self._donut_card(split)

    def _recent_card(self, parent):
        card = Card(parent, PAGE_BG, pad=20, border="#e5e7eb")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        inner = card.inner

        head = tk.Frame(inner, bg=WHITE)
        head.pack(fill="x")
        tk.Label(head, text="Recent Bookings", font=self.f["h2"], fg=NAVY,
                 bg=WHITE).pack(side="left")
        view = tk.Label(head, text="View All", font=self.f["small"], fg=BLUE,
                        bg=WHITE, cursor="hand2")
        view.pack(side="right")
        view.bind("<Button-1>", lambda e: self.shell.show("booking"))

        cols = ["Booking ID", "Student Name", "Facility", "Date",
                "Time Slot", "Status"]
        weights = [1, 2, 2, 2, 2, 1]

        head_row = tk.Frame(inner, bg="#f8fafc")
        head_row.pack(fill="x", pady=(14, 0))
        for i, (c, w) in enumerate(zip(cols, weights)):
            head_row.grid_columnconfigure(i, weight=w, uniform="rc")
            tk.Label(head_row, text=c, font=self.f["cap"], fg=SLATE,
                     bg="#f8fafc", anchor="w").grid(
                         row=0, column=i, sticky="ew", padx=10, pady=10)

        rows = recent_bookings(self.app, 6)
        if not rows:
            tk.Label(inner, text="No bookings yet.", font=self.f["p"],
                     fg=SLATE, bg=WHITE).pack(pady=20)
            return
        for b in rows:
            row = tk.Frame(inner, bg=WHITE)
            row.pack(fill="x")
            for i, w in enumerate(weights):
                row.grid_columnconfigure(i, weight=w, uniform="rc")
            tk.Label(row, text=b["id"], font=self.f["small"], fg=BLUE,
                     bg=WHITE, anchor="w").grid(row=0, column=0, sticky="ew",
                                                padx=10, pady=8)
            values = [b["name"], b["ground"],
                      f"{b['date'].day} {b['date'].strftime('%b %Y')}",
                      b["time"]]
            for i, v in enumerate(values, start=1):
                tk.Label(row, text=v, font=self.f["small"], fg=NAVY,
                         bg=WHITE, anchor="w").grid(row=0, column=i,
                                                    sticky="ew", padx=10, pady=8)
            fg, bg = STATUS_COLOR.get(b["status"], (SLATE, "#f1f5f9"))
            Pill(row, b["status"], self.f["small"], fg, bg, parent_bg=WHITE,
                 padx=10, pady=3).grid(row=0, column=5, sticky="w",
                                       padx=10, pady=6)
            tk.Frame(inner, bg="#f1f5f9", height=1).pack(fill="x")

    def _donut_card(self, parent):
        card = Card(parent, PAGE_BG, pad=20, border="#e5e7eb")
        card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        inner = card.inner
        tk.Label(inner, text="Booking Status Overview", font=self.f["h2"],
                 fg=NAVY, bg=WHITE).pack(anchor="w")

        stats = booking_stats(self.app)
        canvas = tk.Canvas(inner, width=190, height=190, bg=WHITE,
                           highlightthickness=0)
        canvas.pack(pady=(18, 12))
        self._draw_donut(canvas, stats)

        legend = tk.Frame(inner, bg=WHITE)
        legend.pack(fill="x", pady=(4, 0))
        for k in (CONFIRMED, PENDING, CANCELLED):
            fg, _ = STATUS_COLOR[k]
            count = stats["by_status"].get(k, 0)
            pct = stats["percent"].get(k, 0)
            row = tk.Frame(legend, bg=WHITE)
            row.pack(fill="x", pady=4)
            dot = tk.Canvas(row, width=12, height=12, bg=WHITE,
                            highlightthickness=0)
            dot.create_oval(1, 1, 11, 11, fill=fg, outline=fg)
            dot.pack(side="left")
            tk.Label(row, text=k, font=self.f["small"], fg=NAVY,
                     bg=WHITE).pack(side="left", padx=(8, 0))
            tk.Label(row, text=f"{count} ({pct}%)", font=self.f["small"],
                     fg=SLATE, bg=WHITE).pack(side="right")

    @staticmethod
    def _draw_donut(canvas, stats):
        cx, cy, R, r = 95, 95, 78, 50
        total = max(1, stats["total"])
        start = 90.0
        for k in (CONFIRMED, PENDING, CANCELLED):
            fg, _ = STATUS_COLOR[k]
            count = stats["by_status"].get(k, 0)
            if not count:
                continue
            extent = -360.0 * count / total
            canvas.create_arc(cx - R, cy - R, cx + R, cy + R, start=start,
                              extent=extent, fill=fg, outline=fg,
                              style="pieslice")
            start += extent
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=WHITE,
                           outline=WHITE)
        canvas.create_text(cx, cy - 6, text=str(stats["total"]),
                           font=("TkDefaultFont", -24, "bold"), fill=NAVY)
        canvas.create_text(cx, cy + 16, text="Total Bookings",
                           font=("TkDefaultFont", -10), fill=SLATE)

    # ---- responsiveness: 5 / 3 / 2 / 1 stat cards
    def on_reflow(self, w):
        if not getattr(self, "_stat_cards", None):
            return
        holder = self._stat_holder
        avail = holder.winfo_width() or w
        cols = 1
        for min_w, n in STAT_BREAKS:
            if avail >= min_w:
                cols = n
                break
        for i in range(6):
            holder.grid_columnconfigure(i, weight=0, uniform="")
        for i in range(cols):
            holder.grid_columnconfigure(i, weight=1, uniform="stat")
        for i, card in enumerate(self._stat_cards):
            card.grid_configure(
                row=i // cols, column=i % cols, sticky="nsew",
                padx=(0 if i % cols == 0 else 10, 0),
                pady=(0 if i < cols else 12, 0))
        if hasattr(self, "_split"):
            for c in (0, 1):
                self._split.grid_columnconfigure(c, weight=0, uniform="")
            if avail >= 900:
                self._split.grid_columnconfigure(0, weight=3, uniform="dash")
                self._split.grid_columnconfigure(1, weight=2, uniform="dash")
                self._split.winfo_children()[0].grid_configure(
                    row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
                self._split.winfo_children()[1].grid_configure(
                    row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
            else:
                self._split.grid_columnconfigure(0, weight=1, uniform="dash")
                for i, child in enumerate(self._split.winfo_children()):
                    child.grid_configure(row=i, column=0, padx=0,
                                         pady=(0 if i == 0 else 14, 0),
                                         sticky="nsew")