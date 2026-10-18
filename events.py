"""events.py - the "Upcoming Events" browser page."""
import datetime
import tkinter as tk

from common import *
from data import event_date, event_status, all_events
from about import PHONE, EMAIL

CHIPS = ["All", "Football", "Basketball", "Volleyball", "Indoor Sports", "Upcoming", "Completed"]

CATEGORY_COLORS = {
    "Football": (GREEN, "#dcfce7"),
    "Basketball": ("#ea580c", "#ffedd5"),
    "Volleyball": (BLUE, "#dbeafe"),
    "Indoor Sports": ("#7c3aed", "#ede9fe"),
}
STATUS_COLORS = {"Upcoming": (GREEN, "#dcfce7"), "Completed": (SLATE, "#f1f5f9")}


class EventsPage(SectionPage):
    def __init__(self, app):
        super().__init__(app, "events")
        self._filter = "All"
        self._header()
        self._browser()
        self._footer()

    def on_show(self, **kwargs):
        super().on_show(**kwargs)
        self._render_cards()

    # ---- title + intro
    def _header(self):
        body = self.section(WHITE, top=40, bottom=16)
        Pill(body, "CAMPUS TOURNAMENTS", self.app.f_badge, BLUE, BLUE_SOFT).pack(anchor="w")
        tk.Label(body, text="Upcoming Events", font=self.f["h1"], fg=NAVY,
                 bg=WHITE).pack(anchor="w", pady=(8, 0))
        p = tk.Label(body, justify="left", anchor="w", font=self.f["p"], fg=SLATE, bg=WHITE,
                     text=("Discover sports tournaments, competitions, and activities "
                           "happening at our college. Join as a player, bring your team, "
                           "or come to cheer for your department!"))
        p.pack(anchor="w", pady=(10, 0))
        self.wrap(p, None, 0, 760)

    # ---- filter chips + search + the card grid
    def _browser(self):
        self.list_body = self.section(SOFT_BG, top=20, bottom=56)

        toolbar = tk.Frame(self.list_body, bg=SOFT_BG)
        toolbar.pack(fill="x")

        chips_row = tk.Frame(toolbar, bg=SOFT_BG)
        chips_row.pack(side="left")
        self._chips = {}
        for label in CHIPS:
            chip = FilterChip(chips_row, label, (lambda l=label: self._select(l)),
                              self.f["label"], active=(label == "All"), parent_bg=SOFT_BG)
            chip.pack(side="left", padx=(0, 8), pady=(0, 6))
            self._chips[label] = chip

        self.search = RoundedEntry(toolbar, "🔍  Search events...", width=230, height=34,
                                   font=self.f["small"], parent_bg=SOFT_BG)
        self.search.pack(side="right")
        self.search.var.trace_add("write", lambda *a: self._render_cards())

        self.grid_holder = tk.Frame(self.list_body, bg=SOFT_BG)
        self.grid_holder.pack(fill="x", pady=(26, 0))
        self.empty_label = tk.Label(self.list_body, text="No events match your search.",
                                    font=self.f["p"], fg=SLATE, bg=SOFT_BG)
        self._render_cards()

    def _select(self, label):
        self._filter = label
        for name, chip in self._chips.items():
            chip.set_active(name == label)
        self._render_cards()

    def _matches(self, ev):
        if self._filter in ("Upcoming", "Completed"):
            if event_status(ev) != self._filter:
                return False
        elif self._filter != "All" and ev["category"] != self._filter:
            return False
        q = self.search.get().lower()
        return (not q) or (q in ev["title"].lower())

    def _render_cards(self):
        for w in self.grid_holder.winfo_children():
            w.destroy()

        # read from the DB (falls back to in-memory)
        source = all_events(getattr(self.app, "events", []))
        shown = sorted((ev for ev in source if self._matches(ev)),
                       key=lambda e: (event_status(e) == "Completed", event_date(e)))

        if not shown:
            self.reflow(self.grid_holder, [], lambda w: 1)
            self.empty_label.pack(pady=(24, 0))
            return
        self.empty_label.pack_forget()

        cards = []
        for ev in shown:
            c = Card(self.grid_holder, SOFT_BG, pad=14)
            PhotoBox(c.inner, ev["image"], 160, radius=10).pack(fill="x")

            tags = tk.Frame(c.inner, bg=WHITE)
            tags.pack(anchor="w", pady=(10, 0))
            cat_color, cat_tint = CATEGORY_COLORS.get(ev["category"], (BLUE, BLUE_SOFT))
            Pill(tags, ev["category"], self.app.f_badge, cat_color, cat_tint,
                parent_bg=WHITE, padx=10, pady=4).pack(side="left")
            status = event_status(ev)
            st_color, st_tint = STATUS_COLORS.get(status, (SLATE, "#f1f5f9"))
            Pill(tags, status, self.app.f_badge, st_color, st_tint,
                parent_bg=WHITE, padx=10, pady=4).pack(side="left", padx=(6, 0))

            title = tk.Label(c.inner, text=ev["title"], font=self.f["card_t"], fg=NAVY,
                             bg=WHITE, anchor="w", justify="left")
            title.pack(anchor="w", pady=(10, 8), fill="x")
            c.wrap(title)

            rows = (("🗓", f"Date: {ev['date']}  •  Time: {ev['time']}"),
                    ("📍", f"Location: {ev['location']}"),
                    ("👤", f"Organized by: {ev['organizer']}"))
            for glyph, text in rows:
                row = tk.Frame(c.inner, bg=WHITE)
                row.pack(anchor="w", pady=(0, 4), fill="x")
                tk.Label(row, text=glyph, font=self.f["small"], fg=SLATE, bg=WHITE).pack(side="left")
                lb = tk.Label(row, text=text, font=self.f["small"], fg=SLATE, bg=WHITE,
                             anchor="w", justify="left")
                lb.pack(side="left", padx=(6, 0), fill="x")
                c.wrap(lb, 1.0, 30)

            WideButton(c.inner, "View Details",
                      (lambda e=ev: self.app.navigate("event_detail", event=e)),
                      height=38, radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                      font=self.f["btn"], parent_bg=WHITE).pack(fill="x", pady=(10, 0))
            cards.append(c)

        self.reflow(self.grid_holder, cards,
                   lambda w: 3 if w >= 1000 else (2 if w >= 680 else 1))

    # ---- footer
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
        tk.Label(txt, text="BOOK. PLAY. ENJOY.", font=self.app.f_tag, fg=GREEN,
                 bg=NAVY_DARK).pack(anchor="w")
        tk.Label(left, text="Your one-stop portal for booking campus sports\ngrounds and joining college events.",
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
        self.reflow(top, [left, right], lambda w: 2 if w >= 700 else 1, sticky="nw")

        tk.Frame(body, bg="#1e293b", height=1).pack(fill="x", pady=(28, 12))
        bottom = tk.Frame(body, bg=NAVY_DARK)
        bottom.pack(fill="x")
        tk.Label(bottom, text=f"© {datetime.date.today().year} Play Zone. All rights reserved.",
                 font=self.f["small"], fg="#64748b", bg=NAVY_DARK).pack(side="left")
        for text in ("Terms of Use", "Privacy Policy"):
            lb = tk.Label(bottom, text=text, font=self.f["small"], fg="#64748b", bg=NAVY_DARK)
            lb.pack(side="right", padx=(16, 0))
            hover_label(lb, "#64748b", WHITE)


if __name__ == "__main__":
    import login
    login.App().mainloop()