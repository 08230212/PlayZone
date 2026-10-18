"""home.py - the home page (shown after login) + the log-out popup."""
import datetime
import tkinter as tk
from tkinter import font as tkfont

from common import *
from data import (GROUNDS, STATUS_STYLE, ground_status, upcoming_events,
                  all_events)


HERO_IMGS = ["home_1.jpg", "home_2.jpg", "home_3.jpg", "home_4.jpg"]

QUICK = [
    ("▦", "Sports Grounds",
     "Book your preferred ground and time in just a few steps. Instantly confirm your slot online.",
     "View Grounds", "#eff6ff", BLUE, "reservation"),
    ("▤", "Easy Reservations",
     "Book your preferred ground and time in just a few steps. Instantly confirm your slot online.",
     "Reserve Now", "#ecfdf5", GREEN, "reservation"),
    ("◉", "College Events",
     "Discover upcoming tournaments, inter-college sports activities, and athletics tryouts.",
     "View Events", "#fffbeb", AMBER, "events"),
]

STEPS = [
    ("01", "Select a Ground", "Choose from our state-of-the-art campus soccer grounds, "
     "basketball courts, volleyball courts or indoor halls."),
    ("02", "Pick Date & Time", "Check live availability, select your preferred empty slot "
     "and fill in quick team details for secure reservation."),
    ("03", "Book & Enjoy", "Get instant receipt confirmation and on-campus automatic pass "
     "details. Grab your gear and hit the field!"),
]


class HomePage(BasePage):
    MAXW = 1200
    REFRESH_MS = 30000

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self._bodies, self._reflows, self.targets = [], [], {}
        self._after, self._links_on = None, True
        self._curw = self.MAXW
        self._ground_cards = {}
        self._ground_state = {}
        self._tick_job = None

        def F(size, bold=False):
            return tkfont.Font(family=app.family, size=-size,
                               weight="bold" if bold else "normal")
        self.f = {
            "h1": F(52, True), "h2": F(30, True), "tag": F(12, True),
            "lead": F(24, True), "p": F(15), "card_t": F(18, True),
            "ev_t": F(20, True), "small": F(13), "btn": F(13, True),
            "num": F(44, True), "link": F(14), "link_bold": F(14, True), "icon": F(20, True),
            "foot": F(13),
        }

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_nav()
        self.scroll = ScrollFrame(self, on_width=self._apply)
        self.scroll.grid(row=1, column=0, sticky="nsew")
        body = self.scroll.inner
        self._hero(body)
        self._quick(body)
        self._grounds(body)
        self._events(body)
        self._how(body)
        self._footer(body)

    def on_show(self, **kwargs):
        self.scroll.canvas.yview_moveto(0)
        self._set_active_link(self._nav_entries[0])
        self._refresh_grounds()
        self._fill_events()
        if hasattr(self, "profile_icon"):
            self.profile_icon._draw()
        if self._tick_job is None:
            self._tick_job = self.after(self.REFRESH_MS, self._tick)

    def _tick(self):
        self._tick_job = self.after(self.REFRESH_MS, self._tick)
        if self.winfo_viewable():
            self._refresh_grounds()

    def _section(self, parent, bg, top=56, bottom=56):
        outer = tk.Frame(parent, bg=bg)
        outer.pack(fill="x")
        body = tk.Frame(outer, bg=bg)
        body.pack(fill="x", padx=40, pady=(top, bottom))
        self._bodies.append(body)
        return body

    def _heading(self, body, small, title, bg, align="center"):
        anchor = "w" if align == "left" else "center"
        tk.Label(body, text=small, font=self.f["tag"], fg=BLUE, bg=bg).pack(anchor=anchor)
        tk.Label(body, text=title, font=self.f["h2"], fg=NAVY, bg=bg).pack(anchor=anchor, pady=(4, 0))

    def _reflow(self, container, items, fn, sticky="nsew"):
        r = {"c": container, "items": items, "fn": fn, "n": fn(self._curw), "sticky": sticky}
        self._reflows = [x for x in self._reflows if x["c"] is not container]
        self._reflows.append(r)
        self._regrid(r)
        return r

    def _regrid(self, r):
        c, n = r["c"], r["n"]
        for it in r["items"]:
            it.grid_forget()
        for i in range(8):
            c.grid_columnconfigure(i, weight=0, uniform="")
        for i in range(n):
            c.grid_columnconfigure(i, weight=1, uniform=f"g{id(c)}")
        for i, it in enumerate(r["items"]):
            it.grid(row=i // n, column=i % n, sticky=r["sticky"], padx=8, pady=8)

    def scroll_to(self, key):
        self.update_idletasks()
        total = max(1, self.scroll.inner.winfo_height())
        y = 0 if key == "home" else self.targets[key].winfo_y()
        self.scroll.canvas.yview_moveto(y / total)

    # ---- navigation bar
    def _build_nav(self):
        app = self.app
        bar = tk.Frame(self, bg=WHITE)
        bar.grid(row=0, column=0, sticky="ew")
        row = tk.Frame(bar, bg=WHITE)
        row.pack(fill="x", padx=40, pady=12)

        brand = tk.Frame(row, bg=WHITE)
        brand.pack(side="left")
        LogoMark(brand, 36).pack(side="left")
        txt = tk.Frame(brand, bg=WHITE)
        txt.pack(side="left", padx=(10, 0))
        tk.Label(txt, text="PLAY ZONE", font=app.f_brand, fg=NAVY, bg=WHITE).pack(anchor="w")
        tk.Label(txt, text="BOOK. PLAY. ENJOY.", font=app.f_tag, fg=GREEN, bg=WHITE).pack(anchor="w")

        # ---- top-right buttons -----------------------------------------
        right = tk.Frame(row, bg=WHITE)
        right.pack(side="right")
        
        RoundedButton(right, "Reserve Now", lambda: self.app.navigate("reservation"), 110, 36,
                      radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                      font=self.f["btn"]).pack(side="left", padx=(0, 12))
                      
        self.profile_icon = ProfileMenu(right, app, 36)
        self.profile_icon.pack(side="left")

        self.links = tk.Frame(row, bg=WHITE)
        self.links.pack(side="left", expand=True)
        nav_items = (("Home", "scroll", "home"), ("About Us", "page", "about"),
                     ("Events", "page", "events"), ("Reservation", "page", "reservation"),
                     ("Feedback", "page", "feedback"))
        self._nav_entries = []
        self._nav_active = None
        for text, kind, target in nav_items:
            cmd = (lambda t=target: self.scroll_to(t)) if kind == "scroll" else \
                  (lambda t=target: self.app.navigate(t))
            cell = tk.Frame(self.links, bg=WHITE)
            cell.pack(side="left", padx=10)
            lb = tk.Label(cell, text=text, font=self.f["link"], fg="#334155",
                          bg=WHITE, cursor="hand2")
            lb.pack()
            underline = tk.Frame(cell, bg=WHITE, height=2)
            underline.pack(fill="x", pady=(5, 0))
            entry = {"lb": lb, "underline": underline}
            lb.bind("<Enter>", lambda e, en=entry: en["lb"].config(fg=BLUE))
            lb.bind("<Leave>", lambda e, en=entry: en["lb"].config(
                fg=BLUE if en is self._nav_active else "#334155"))
            lb.bind("<Button-1>", lambda e, c=cmd, en=entry, k=kind: (
                self._set_active_link(en) if k == "scroll" else None, c()))
            self._nav_entries.append(entry)
        self._set_active_link(self._nav_entries[0])
        tk.Frame(bar, bg="#e5e7eb", height=1).pack(fill="x")

    def _set_active_link(self, entry):
        if self._nav_active is entry:
            return
        if self._nav_active:
            self._nav_active["lb"].config(fg="#334155", font=self.f["link"])
            self._nav_active["underline"].config(bg=WHITE)
        entry["lb"].config(fg=BLUE, font=self.f["link_bold"])
        entry["underline"].config(bg=BLUE)
        self._nav_active = entry

    # ---- hero
    def _hero(self, parent):
        body = self._section(parent, WHITE, top=36, bottom=56)
        self.targets["home"] = body.master
        left = tk.Frame(body, bg=WHITE)
        Pill(left, "CAMPUS RECREATION PORTAL", self.app.f_badge, BLUE, BLUE_SOFT).pack(anchor="w")
        tk.Label(left, text="PLAY ZONE", font=self.f["h1"], fg=NAVY, bg=WHITE).pack(anchor="w", pady=(8, 0))
        tk.Label(left, text="Your Space. Your Game. Your Time.", font=self.f["lead"],
                 fg=BLUE, bg=WHITE).pack(anchor="w")
        self.hero_p = tk.Label(
            left, justify="left", anchor="w", font=self.f["p"], fg=SLATE, bg=WHITE,
            wraplength=480,
            text=("Reserve college sports grounds, discover upcoming tournaments, and "
                  "coordinate instantly with your teammates. Elevate your physical "
                  "training and make the absolute most of your time on the field."))
        self.hero_p.pack(anchor="w", pady=(18, 0))
        btns = tk.Frame(left, bg=WHITE)
        btns.pack(anchor="w", pady=(22, 0))
        RoundedButton(btns, "Reserve a Ground", lambda: self.app.navigate("reservation"), 155, 42,
                      radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                      font=self.f["btn"]).pack(side="left")
        RoundedButton(btns, "Explore Events", lambda: self.app.navigate("events"), 135, 42,
                      radius=8, bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                      font=self.f["btn"]).pack(side="left", padx=(10, 0))

        right = tk.Frame(body, bg=WHITE)
        right.grid_columnconfigure(0, weight=1, uniform="hero")
        right.grid_columnconfigure(1, weight=1, uniform="hero")
        for i, name in enumerate(HERO_IMGS):
            PhotoBox(right, name, 150, radius=14, tint=TINTS[i % len(TINTS)]).grid(
                row=i // 2, column=i % 2, sticky="ew", padx=5, pady=5)
        self._hero_r = self._reflow(body, [left, right], lambda w: 2 if w >= 900 else 1,
                                    sticky="ew")

    # ---- "Get Moving in Seconds" (quick actions)
    def _quick(self, parent):
        body = self._section(parent, SOFT_BG)
        self._heading(body, "QUICK ACTIONS", "Get Moving in Seconds", SOFT_BG)
        holder = tk.Frame(body, bg=SOFT_BG)
        holder.pack(fill="x", pady=(30, 0))
        cards = []
        for glyph, title, desc, btn, tint, color, page in QUICK:
            go = lambda p=page: self.app.navigate(p)
            c = Card(holder, SOFT_BG)
            ic = tk.Canvas(c.inner, width=44, height=44, bg=WHITE, highlightthickness=0)
            round_rect(ic, 0, 0, 44, 44, 12, fill=tint, outline=tint)
            ic.create_text(22, 22, text=glyph, fill=color, font=self.f["icon"])
            ic.pack(anchor="w")
            tk.Label(c.inner, text=title, font=self.f["card_t"], fg=NAVY,
                     bg=WHITE).pack(anchor="w", pady=(12, 4))
            c.wrap(tk.Label(c.inner, text=desc, font=self.f["small"], fg=SLATE, bg=WHITE,
                            justify="left", anchor="w")).pack(anchor="w")
            WideButton(c.inner, btn, go, height=36,
                       radius=8, bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                       font=self.f["btn"]).pack(fill="x", pady=(16, 0))
            hover_card(c)
            cards.append(c)
        self._reflow(holder, cards, lambda w: 3 if w >= 900 else 1)

    # ---- featured grounds
    def _grounds(self, parent):
        body = self._section(parent, WHITE)
        self.targets["grounds"] = body.master
        self._heading(body, "BOOKING STATUS", "Featured Grounds", WHITE, align="left")
        holder = tk.Frame(body, bg=WHITE)
        holder.pack(fill="x", pady=(30, 0))
        cards = []
        for name, cap, img in GROUNDS:
            go = lambda n=name: self.app.navigate("reservation", ground=n)
            c = Card(holder, WHITE, pad=12)
            PhotoBox(c.inner, img, 150, radius=10).pack(fill="x")
            tk.Label(c.inner, text=name, font=self.f["card_t"], fg=NAVY,
                     bg=WHITE).pack(anchor="w", pady=(10, 0))
            cap_row = tk.Frame(c.inner, bg=WHITE)
            cap_row.pack(anchor="w", pady=(2, 10))
            tk.Label(cap_row, text="👥", font=self.f["small"], fg=SLATE, bg=WHITE).pack(side="left")
            tk.Label(cap_row, text=cap, font=self.f["small"], fg=SLATE,
                     bg=WHITE).pack(side="left", padx=(6, 0))
            row = tk.Frame(c.inner, bg=WHITE)
            row.pack(fill="x")
            self._ground_cards[name] = (c, row)
            self._fill_ground_row(name)
            hover_card(c)
            cards.append(c)
        self._reflow(holder, cards, lambda w: 4 if w >= 1100 else (2 if w >= 620 else 1))

    def _fill_ground_row(self, name, rebind=False):
        card, row = self._ground_cards[name]
        status = ground_status(name, getattr(self.app, "reservations", []))
        self._ground_state[name] = status
        for w in row.winfo_children():
            w.destroy()
        color, tint = STATUS_STYLE[status]
        Pill(row, f"●  {status}", self.app.f_badge, color, tint, padx=10, pady=5).pack(side="left")
        free = status == "Available"
        RoundedButton(row, "Reserve Now" if free else "View Slots",
                      lambda n=name: self.app.navigate("reservation", ground=n), 100, 32,
                      radius=8, bg=BLUE if free else WHITE,
                      hover=BLUE_DARK if free else BLUE_SOFT,
                      fg=WHITE if free else BLUE, outline=BLUE,
                      font=self.f["btn"]).pack(side="right")
        if rebind:
            for child in row.winfo_children():
                hover_card(card, widget=child)

    def _refresh_grounds(self):
        reservations = getattr(self.app, "reservations", [])
        for name in self._ground_cards:
            if ground_status(name, reservations) != self._ground_state.get(name):
                self._fill_ground_row(name, rebind=True)

    # ---- upcoming events
    def _events(self, parent):
        body = self._section(parent, WHITE, top=24)
        self.targets["events"] = body.master
        self._heading(body, "CAMPUS TOURNAMENTS", "Upcoming Events", WHITE, align="left")
        self.events_holder = tk.Frame(body, bg=WHITE)
        self.events_holder.pack(fill="x", pady=(30, 0))
        self._fill_events()
        more = tk.Label(body, text="View All Events  →", font=self.f["link"], fg=BLUE,
                        bg=WHITE, cursor="hand2")
        more.pack(pady=(18, 0))
        more.bind("<Button-1>", lambda e: self.app.navigate("events"))

    def _fill_events(self):
        holder = self.events_holder
        for w in holder.winfo_children():
            w.destroy()
        self._reflows = [r for r in self._reflows if r["c"] is not holder]
        source = all_events(getattr(self.app, "events", []))
        shown = upcoming_events(source, 2)
        if not shown:
            tk.Label(holder, text="No upcoming events right now - please check back soon.",
                     font=self.f["p"], fg=SLATE, bg=WHITE).pack(pady=20)
            return
        cards = []
        for ev in shown:
            go = lambda e=ev: self.app.navigate("event_detail", event=e)
            c = Card(holder, WHITE, pad=14)
            row = tk.Frame(c.inner, bg=WHITE)
            row.pack(fill="x")
            row.grid_columnconfigure(0, weight=2, uniform="ev")
            row.grid_columnconfigure(1, weight=3, uniform="ev")
            PhotoBox(row, ev["image"], 270, radius=10, tint="#1e293b").grid(row=0, column=0, sticky="ew")
            info = tk.Frame(row, bg=WHITE)
            info.grid(row=0, column=1, sticky="w", padx=(16, 0))
            Pill(info, ev["category"].upper(), self.app.f_badge, BLUE, BLUE_SOFT).pack(anchor="w")
            c.wrap(tk.Label(info, text=ev["title"], font=self.f["ev_t"], fg=NAVY, bg=WHITE,
                            justify="left", anchor="w"), 0.6, 30).pack(anchor="w", pady=(8, 6))
            for glyph, text in (("🗓", f"Date: {ev['date']}  •  Time: {ev['time']}"),
                                ("📍", f"Location: {ev['location']}")):
                line = tk.Frame(info, bg=WHITE)
                line.pack(anchor="w", pady=(0, 2))
                tk.Label(line, text=glyph, font=self.f["small"], fg=SLATE, bg=WHITE).pack(side="left")
                c.wrap(tk.Label(line, text=text, font=self.f["small"], fg=SLATE, bg=WHITE,
                                justify="left", anchor="w"), 0.6, 50).pack(side="left", padx=(6, 0))
            RoundedButton(info, "View Event", go, 120, 36, radius=8,
                          bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                          font=self.f["btn"]).pack(anchor="w", pady=(10, 0))
            hover_card(c)
            cards.append(c)
        self._reflow(holder, cards, lambda w: 2 if w >= 1000 else 1)

    # ---- how it works
    def _how(self, parent):
        body = self._section(parent, SOFT_BG)
        self.targets["how"] = body.master
        self._heading(body, "PROCESS GUIDE", "How It Works", SOFT_BG)
        holder = tk.Frame(body, bg=SOFT_BG)
        holder.pack(fill="x", pady=(30, 0))
        cards = []
        for num, title, desc in STEPS:
            c = Card(holder, SOFT_BG, pad=22)
            tk.Label(c.inner, text=num, font=self.f["num"], fg=BLUE, bg=WHITE).pack(anchor="w")
            tk.Label(c.inner, text=title, font=self.f["card_t"], fg=NAVY,
                     bg=WHITE).pack(anchor="w", pady=(6, 4))
            c.wrap(tk.Label(c.inner, text=desc, font=self.f["small"], fg=SLATE, bg=WHITE,
                            justify="left", anchor="w")).pack(anchor="w")
            cards.append(c)
        self._reflow(holder, cards, lambda w: 3 if w >= 900 else 1)

    # ---- footer
    def _footer(self, parent):
        body = self._section(parent, NAVY_DARK, top=44, bottom=22)
        self.targets["contact"] = body.master
        top = tk.Frame(body, bg=NAVY_DARK)
        top.pack(fill="x")
        left = tk.Frame(top, bg=NAVY_DARK)
        left.pack(side="left", anchor="n")
        brand = tk.Frame(left, bg=NAVY_DARK)
        brand.pack(anchor="w")
        LogoMark(brand, 36, parent_bg=NAVY_DARK).pack(side="left")
        txt = tk.Frame(brand, bg=NAVY_DARK)
        txt.pack(side="left", padx=(10, 0))
        tk.Label(txt, text="PLAY ZONE", font=self.app.f_brand, fg=WHITE, bg=NAVY_DARK).pack(anchor="w")
        tk.Label(txt, text="BOOK. PLAY. ENJOY.", font=self.app.f_tag, fg=GREEN, bg=NAVY_DARK).pack(anchor="w")
        tk.Label(left, justify="left", anchor="w", wraplength=340,
                 text=("Leveling up your campus sports experience with simplified "
                       "ground reservation and vibrant athletics community events."),
                 font=self.f["foot"], fg="#94a3b8", bg=NAVY_DARK).pack(anchor="w", pady=(12, 0))

        right = tk.Frame(top, bg=NAVY_DARK)
        right.pack(side="right", anchor="n")
        for glyph, line in (("☎", "17593088"), ("✉", "info@playzone.edu.bt")):
            row = tk.Frame(right, bg=NAVY_DARK)
            row.pack(anchor="e", pady=(0, 8))
            tk.Label(row, text=glyph, font=self.f["foot"], fg=BLUE, bg=NAVY_DARK).pack(side="left", padx=(0, 8))
            tk.Label(row, text=line, font=self.f["foot"], fg="#94a3b8", bg=NAVY_DARK).pack(side="left")

        tk.Frame(body, bg="#1e293b", height=1).pack(fill="x", pady=(28, 16))
        bottom = tk.Frame(body, bg=NAVY_DARK)
        bottom.pack(fill="x")
        tk.Label(bottom, text=f"© {datetime.date.today().year} PLAY ZONE. All rights reserved.",
                 font=self.f["small"], fg="#64748b", bg=NAVY_DARK).pack(side="left")
        links = tk.Frame(bottom, bg=NAVY_DARK)
        links.pack(side="right")
        for i, text in enumerate(("Designed for Campus Excellence", "Terms of Use", "Privacy Policy")):
            if i:
                tk.Label(links, text="  •  ", font=self.f["small"], fg="#475569",
                         bg=NAVY_DARK).pack(side="left")
            tk.Label(links, text=text, font=self.f["small"], fg="#64748b",
                     bg=NAVY_DARK).pack(side="left")

    # ---- responsiveness
    def _apply(self, w):
        self._curw = w
        side = max(24, (w - self.MAXW) // 2)
        for b in self._bodies:
            b.pack_configure(padx=side)
        for r in self._reflows:
            n = r["fn"](w)
            if n != r["n"]:
                r["n"] = n
                self._regrid(r)
        want = w >= 860
        if want != self._links_on:
            self._links_on = want
            if want:
                self.links.pack(side="left", expand=True)
            else:
                self.links.pack_forget()
        avail = w - 2 * side
        colw = avail / 2 - 20 if self._hero_r["n"] == 2 else avail
        self.hero_p.config(wraplength=max(240, int(colw * 0.95)))


# ------------------------------------------------------------ logout popup ---
class LogoutDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Log out")
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(app)
        w, h = 420, 230
        x = app.winfo_rootx() + (app.winfo_width() - w) // 2
        y = app.winfo_rooty() + (app.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

        f_msg = tkfont.Font(family=app.family, size=-22)
        self._fonts = (f_msg,)
        tk.Label(self, text="Are you sure you want to log out?", font=f_msg,
                 fg="#64748b", bg=WHITE, wraplength=320,
                 justify="center").pack(pady=(44, 26))
        RoundedButton(self, "Log Out", self.confirm, 170, 58, radius=16,
                      bg=PURPLE, hover=PURPLE_DARK, fg=WHITE, outline="#8e8e9f",
                      font=f_msg).pack()
        self.bind("<Return>", lambda e: self.confirm())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def confirm(self):
        self.destroy()
        self.app.logout()