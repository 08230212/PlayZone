"""about.py - the "About Play Zone" page AND the "Ground Details" page.

Connected to the rest of the app:
  * registered in login.py:  PAGES["about"] = (AboutPage, "PlayZone - About Us")
                             PAGES["ground_detail"] = (GroundDetailPage, "PlayZone - Ground Details")
  * opened from the nav bar's "About Us" link (nav bar itself lives in common.py's SectionPage)
  * the "Our Facilities" cards open the Ground Details page (bottom of this file):
        app.navigate("ground_detail", ground="Football Ground")
    It shows photos, facilities and opening hours; its "Reserve this Ground" button opens the
    Reservation page with that ground selected. The live status badge comes from data.py.
Edit the text / names / image file names in the DATA blocks below - no need to touch the layout code.
Images go in the assets/ folder; a coloured placeholder shows if a file is missing.
"""
import datetime
import tkinter as tk
from tkinter import font as tkfont, messagebox

from common import *
from data import GROUNDS, STATUS_STYLE, ground_status, ground_hours

# ------------------------------------------------------------------ DATA ---
PHONE = "17593088"
EMAIL = "08230212.sce@rub.edu.bt"
GREEN_TEXT = "#059669"

INTRO = ("Play Zone is a college sports platform designed to make sports facility booking and "
         "event information easier and more accessible for students and staff. We bridge the "
         "gap between enthusiastic student athletes and varsity complex managers.")

PURPOSE_IMG = "about_purpose.jpg"
PURPOSE_TEXT = ("Our goal is to provide a simple platform where students can discover sports "
                "facilities, explore upcoming events, reserve grounds, and share their "
                "experiences. We strive to foster a vibrant campus culture centered on "
                "physical wellness, healthy teamwork and community integration.")
PURPOSE_POINTS = ["Digitalize traditional manual register bookings",
                  "Maximize physical court usage rates",
                  "Deliver transparent, equal access to all students"]

# (name, image)  - the names must match the grounds in data.py / ground_detail.py
FACILITIES = [("Football Ground", "football.jpg"),
              ("Basketball Court", "basketball.jpg"),
              ("Volleyball Court", "volleyball.jpg"),
              ("Indoor Sports Hall", "indoor.jpg")]

# (name, image)
TEAM = [("Tashi Lhamo", "team_1.jpg"), ("Pema Choden", "team_2.jpg"),
        ("Cheki Wangmo", "team_3.jpg"), ("Dechen Dorji", "team_4.jpg"),
        ("Rinchen Dorji", "team_5.jpg"), ("Ugyen Dorji", "team_6.jpg")]

# (glyph, title, description, tint, colour)
VALUES = [
    ("▤", "Accessibility",
     "Make sports facilities easier for everyone to access. Break down administrative "
     "barriers for students.",
     "#eff6ff", BLUE),
    ("⚡", "Simplicity",
     "Make reservations quick and easy. Tap twice, choose a date, and confirm your "
     "field slot automatically.",
     "#ecfdf5", GREEN),
    ("♥", "Community",
     "Encourage students to participate in sports and college events. Cultivate "
     "athletic identity together.",
     "#fef2f2", "#ef4444"),
]


# ------------------------------------------------- DATA for the Ground Details page ---
# One entry per ground in data.GROUNDS (same name). SAMPLE TEXT - edit freely.
GROUND_INFO = {
    "Football Ground": {
        "photos": ["football.jpg", "football_2.jpg", "football_3.jpg"],
        "about": ("Our full-size football ground is the heart of campus sport. It has a "
                  "marked natural-grass pitch with goal posts and is used for inter-class "
                  "tournaments, team practice and the annual Sports Day."),
        "type": "Natural grass pitch",
        "count": "1 ground",
        "facilities": ["Goal posts", "Floodlights", "Drinking water", "Seating area",
                       "First aid", "Changing room"],
    },
    "Basketball Court": {
        "photos": ["basketball.jpg", "basketball_2.jpg", "basketball_3.jpg"],
        "about": ("We have two full-size basketball courts with smooth playing surfaces, "
                  "marked lines and hoops at each end. They are used for the Basketball "
                  "Championship, inter-house matches and daily practice."),
        "type": "Full-size courts",
        "count": "2 courts",
        "facilities": ["Hoops and backboards", "Scoreboard", "Drinking water",
                       "Seating area", "First aid"],
    },
    "Volleyball Court": {
        "photos": ["volleyball.jpg", "volleyball_2.jpg", "volleyball_3.jpg"],
        "about": ("A sand volleyball court with a net and boundary lines, perfect for "
                  "friendly matches and the Volleyball Tournament. Bring your own team "
                  "or join one of the college teams."),
        "type": "Sand court",
        "count": "1 court",
        "facilities": ["Net and poles", "Drinking water", "Seating area", "First aid"],
    },
    "Indoor Sports Hall": {
        "photos": ["indoor.jpg", "indoor_2.jpg", "indoor_3.jpg"],
        "about": ("A covered multi-purpose hall for badminton, table tennis and other "
                  "indoor games. Because it is indoors it can be used in any weather, and it "
                  "hosts the Indoor Badminton Open."),
        "type": "Indoor multi-purpose hall",
        "count": "1 hall",
        "facilities": ["Badminton courts", "Table tennis", "Lighting", "Drinking water",
                       "Seating area", "First aid"],
    },
}

# shared by every ground
RULES = ["Bring your student ID card to the ground.",
         "Arrive about 10 minutes before your booked time.",
         "Wear proper sports shoes and clothes.",
         "Leave the ground clean and tidy after use."]
BOOKING_SLOT = "1 hour per booking"
OPEN_DAYS = "Open every day"


def hour_text(h):
    """18 -> '6:00 PM'"""
    return f"{h % 12 or 12}:00 {'AM' if h < 12 else 'PM'}"


class AboutPage(SectionPage):
    def __init__(self, app):
        super().__init__(app, "about",
                         local={"feedback": lambda: self.scroll_to("contact")})
        self._header()
        self._purpose()
        self._facilities()
        self._team()
        self._values()
        self._contact()
        self._footer()

    # ---- title block
    def _header(self):
        body = self.section(WHITE, top=40, bottom=44)
        Pill(body, "WHO WE ARE", self.app.f_badge, GREEN_TEXT, "#dcfce7").pack(anchor="w")
        tk.Label(body, text="About Play Zone", font=self.f["h1"], fg=NAVY,
                 bg=WHITE).pack(anchor="w", pady=(10, 0))
        lab = tk.Label(body, text=INTRO, font=self.f["p"], fg=SLATE, bg=WHITE,
                       justify="left", anchor="w", wraplength=760)
        lab.pack(anchor="w", pady=(10, 0))
        self.wrap(lab, None, 0, 820)
        tk.Frame(self.body, bg="#e5e7eb", height=1).pack(fill="x")

    # ---- Our Purpose (photo left, text right)
    def _purpose(self):
        body = self.section(SOFT_BG, top=56, bottom=56)
        holder = tk.Frame(body, bg=SOFT_BG)
        holder.pack(fill="x")
        img = PhotoBox(holder, PURPOSE_IMG, 320, radius=16, bg=SOFT_BG, tint=BLUE_SOFT)

        text = tk.Frame(holder, bg=SOFT_BG)
        r = self.reflow(holder, [img, text], lambda w: 2 if w >= 900 else 1, sticky="ew")
        tk.Label(text, text="MISSION & GOAL", font=self.f["tag"], fg=BLUE,
                 bg=SOFT_BG).pack(anchor="w", padx=(12, 0))
        tk.Label(text, text="Our Purpose", font=self.f["h2"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w", padx=(12, 0), pady=(4, 0))
        p = tk.Label(text, text=PURPOSE_TEXT, font=self.f["p"], fg=SLATE, bg=SOFT_BG,
                     justify="left", anchor="w")
        p.pack(anchor="w", padx=(12, 0), pady=(14, 0))
        self.wrap(p, r, 12)
        for point in PURPOSE_POINTS:
            row = tk.Frame(text, bg=SOFT_BG)
            row.pack(anchor="w", padx=(12, 0), pady=(12, 0))
            tick = tk.Canvas(row, width=22, height=22, bg=SOFT_BG, highlightthickness=0)
            round_rect(tick, 0, 0, 22, 22, 6, fill=BLUE_SOFT, outline=BLUE_SOFT)
            tick.create_text(11, 11, text="✓", fill=BLUE, font=self.f["label"])
            tick.pack(side="left")
            lb = tk.Label(row, text=point, font=self.f["label"], fg=NAVY, bg=SOFT_BG,
                          justify="left", anchor="w")
            lb.pack(side="left", padx=(10, 0))
            self.wrap(lb, r, 60)

    # ---- Our Facilities (4 cards) - click one to read about that ground
    def _facilities(self):
        body = self.section(WHITE, top=56, bottom=40)
        self.heading(body, "CAMPUS GROUNDS", "Our Facilities", WHITE)
        holder = tk.Frame(body, bg=WHITE)
        holder.pack(fill="x", pady=(24, 0))
        cards = []
        for name, img in FACILITIES:
            c = Card(holder, WHITE, pad=10, border="#eef2f7")
            PhotoBox(c.inner, img, 130, radius=12).pack(fill="x")
            row = tk.Frame(c.inner, bg=WHITE)
            row.pack(fill="x", pady=(10, 2))
            tk.Label(row, text=name, font=self.f["label"], fg=NAVY, bg=WHITE).pack(side="left")
            tk.Label(row, text="›", font=self.f["icon"], fg=BLUE, bg=WHITE).pack(side="right")
            hover_card(c)
            bind_tree(c, "<Button-1>",
                      lambda e, n=name: self.app.navigate("ground_detail", ground=n))
            c.config(cursor="hand2")
            cards.append(c)
        self.reflow(holder, cards, lambda w: 4 if w >= 1000 else (2 if w >= 560 else 1))

    # ---- Our Teams (6 cards)
    def _team(self):
        body = self.section(WHITE, top=24, bottom=56)
        self.heading(body, None, "Our Teams", WHITE)
        holder = tk.Frame(body, bg=WHITE)
        holder.pack(fill="x", pady=(24, 0))
        cards = []
        for name, img in TEAM:
            c = Card(holder, WHITE, pad=8, border="#eef2f7")
            PhotoBox(c.inner, img, 170, radius=12, tint=TINTS[len(cards) % 4]).pack(fill="x")
            tk.Label(c.inner, text=name, font=self.f["label"], fg=NAVY,
                     bg=WHITE).pack(anchor="w", padx=4, pady=(8, 4))
            hover_card(c)
            cards.append(c)
        self.reflow(holder, cards, lambda w: 6 if w >= 1100 else (3 if w >= 640 else 2))

    # ---- Our Values (3 cards)
    def _values(self):
        body = self.section(SOFT_BG, top=56, bottom=56)
        self.heading(body, "PRINCIPLES WE STAND BY", "Our Values", SOFT_BG, anchor="center")
        holder = tk.Frame(body, bg=SOFT_BG)
        holder.pack(fill="x", pady=(30, 0))
        cards = []
        for glyph, title, desc, tint, color in VALUES:
            c = Card(holder, SOFT_BG, pad=22, border="#eef2f7")
            ic = tk.Canvas(c.inner, width=40, height=40, bg=WHITE, highlightthickness=0)
            round_rect(ic, 0, 0, 40, 40, 10, fill=tint, outline=tint)
            ic.create_text(20, 20, text=glyph, fill=color, font=self.f["icon"])
            ic.pack(anchor="w")
            tk.Label(c.inner, text=title, font=self.f["card_t"], fg=NAVY,
                     bg=WHITE).pack(anchor="w", pady=(12, 4))
            c.wrap(tk.Label(c.inner, text=desc, font=self.f["small"], fg=SLATE, bg=WHITE,
                            justify="left", anchor="w")).pack(anchor="w")
            hover_card(c)
            cards.append(c)
        self.reflow(holder, cards, lambda w: 3 if w >= 900 else 1)

    # ---- Contact Play Zone (text left, form right)
    def _contact(self):
        body = self.section(WHITE, top=56, bottom=56, key="contact")
        holder = tk.Frame(body, bg=WHITE)
        holder.pack(fill="x")

        left = tk.Frame(holder, bg=WHITE)
        form = Card(holder, WHITE, fill=SOFT_BG, border="#eef2f7", radius=16, pad=24)
        r = self.reflow(holder, [left, form], lambda w: 2 if w >= 900 else 1, sticky="new")

        tk.Label(left, text="GET IN TOUCH", font=self.f["tag"], fg=BLUE,
                 bg=WHITE).pack(anchor="w", padx=(12, 0))
        tk.Label(left, text="Contact Play Zone", font=self.f["h2"], fg=NAVY,
                 bg=WHITE).pack(anchor="w", padx=(12, 0), pady=(4, 0))
        p = tk.Label(left, justify="left", anchor="w", font=self.f["p"], fg=SLATE, bg=WHITE,
                     text=("Have any suggestions, questions about inter-college sports "
                           "reservations, or need assistance booking sports halls for "
                           "non-traditional activities? Drop us a note!"))
        p.pack(anchor="w", padx=(12, 0), pady=(14, 0))
        self.wrap(p, r, 12)
        for glyph, value in (("☎", PHONE), ("✉", EMAIL)):
            row = tk.Frame(left, bg=WHITE)
            row.pack(anchor="w", padx=(12, 0), pady=(14, 0))
            tk.Label(row, text=glyph, font=self.f["icon"], fg=BLUE, bg=WHITE).pack(side="left")
            tk.Label(row, text=value, font=self.f["label"], fg=NAVY,
                     bg=WHITE).pack(side="left", padx=(10, 0))

        # ---- the form
        inner = form.inner

        def field(label, placeholder, **kw):
            tk.Label(inner, text=label, font=self.f["label"], fg=NAVY,
                     bg=SOFT_BG).pack(anchor="w", pady=(0, 6))
            box = FlexInput(inner, placeholder, font=self.f["small"], parent_bg=SOFT_BG, **kw)
            box.pack(fill="x", pady=(0, 14))
            return box

        self.in_name = field("Full Name", "Type here")
        self.in_email = field("Email Address", "student@university.edu")
        self.in_msg = field("Message or feedback", "How can we help you?",
                            multiline=True, height=110)
        # a Tk text box asks for 80 characters of width by default, which pushed the form out of
        # its column and made the section look off - let the boxes stretch to the card instead
        for box in (self.in_name, self.in_email, self.in_msg):
            box.widget.config(width=1)
        WideButton(inner, "Send Message", self.send, height=44, radius=8, bg=BLUE,
                   hover=BLUE_DARK, fg=WHITE, font=self.f["btn"],
                   parent_bg=SOFT_BG).pack(fill="x", pady=(4, 0))

    def send(self):
        name, email, msg = self.in_name.get(), self.in_email.get(), self.in_msg.get()
        if not (name and email and msg):
            messagebox.showwarning("Missing details", "Please fill in every field.")
            return
        if "@" not in email:
            messagebox.showwarning("Invalid email", "Please enter a valid email.")
            return
        print("[feedback]", {"name": name, "email": email, "message": msg})  # <- save it / email it here
        messagebox.showinfo("Thank you", "Your message has been sent. We will get back to you soon.")
        for box in (self.in_name, self.in_email, self.in_msg):
            box.reset()

    # ---- footer (intentionally the same as home.py's footer)
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
        import datetime
        tk.Label(bottom, text=f"© {datetime.date.today().year} Play Zone. All rights reserved.",
                 font=self.f["small"], fg="#64748b", bg=NAVY_DARK).pack(side="left")
        for text in ("Terms of Use", "Privacy Policy"):
            lb = tk.Label(bottom, text=text, font=self.f["small"], fg="#64748b", bg=NAVY_DARK)
            lb.pack(side="right", padx=(16, 0))
            hover_label(lb, "#64748b", WHITE)


# ------------------------------------------------------------ Ground Details page ---
class GroundDetailPage(SectionPage):
    def __init__(self, app):
        super().__init__(app, "about")          # keeps "About Us" highlighted in the nav bar
        self.ground = None
        self._width = 1200
        self._left_labels = []                  # (label, margin) re-wrapped when the window resizes
        self.photos, self.thumbs = [], []

        def F(size, bold=False):
            return tkfont.Font(family=app.family, size=-size,
                               weight="bold" if bold else "normal")
        self.f.update({"h3": F(20, True), "cap": F(10, True), "val": F(13, True),
                       "hero": F(34, True)})

        # on this page "About Us" should go back to the About page (the base class would
        # just scroll this page to the top because it is the "current" link)
        for cell in self.links.winfo_children():
            lb = cell.winfo_children()[0]
            if lb.cget("text") == "About Us":
                lb.bind("<Button-1>", lambda e: self.app.navigate("about"))

        # the part that changes per ground lives in one persistent frame
        dyn = tk.Frame(self.body, bg=SOFT_BG)
        dyn.pack(fill="x")
        self.dyn_body = tk.Frame(dyn, bg=SOFT_BG)
        self.dyn_body.pack(fill="x", padx=40, pady=(24, 56))
        self._bodies.append(self.dyn_body)

        self._footer()

    def on_show(self, ground=None, **kwargs):
        super().on_show(**kwargs)
        if ground is not None:
            self.ground = ground
        if self.ground not in GROUND_INFO:      # opened with nothing (or an unknown name)
            self.app.navigate("about")
            return
        self._build(self.ground)

    # ---- build everything that depends on the chosen ground
    def _build(self, name):
        for w in self.dyn_body.winfo_children():
            w.destroy()
        self._left_labels = []
        info = GROUND_INFO[name]
        _, cap, _img = next(g for g in GROUNDS if g[0] == name)
        status = ground_status(name, getattr(self.app, "reservations", []))   # live
        color, tint = STATUS_STYLE[status]
        self.photos = info["photos"]
        first, last = ground_hours(name)           # this ground's own opening hours

        from event_detail import HeroBanner     # imported here (not at the top) to avoid a circular import

        class Banner(HeroBanner):
            H = 170                                  # the Event Details banner is 250 tall; this one is slimmer
        Banner(self.dyn_body, self.photos[0], name, [(f"●  {status}", color, tint)],
                   self.f["hero"], self.app.f_badge).pack(fill="x")

        self.holder = tk.Frame(self.dyn_body, bg=SOFT_BG)
        self.holder.pack(fill="x", pady=(28, 0))
        self.left = tk.Frame(self.holder, bg=SOFT_BG)
        self.right = Card(self.holder, SOFT_BG, pad=22)

        # ---- left column
        tk.Label(self.left, text="About this Ground", font=self.f["h3"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")
        about = tk.Label(self.left, text=info["about"], font=self.f["p"], fg=SLATE, bg=SOFT_BG,
                         justify="left", anchor="w")
        about.pack(anchor="w", pady=(12, 0))
        self._left_labels.append((about, 0))

        tk.Label(self.left, text="Photo Gallery", font=self.f["h3"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w", pady=(34, 0))
        self.big = tk.Frame(self.left, bg=SOFT_BG)
        self.big.pack(fill="x", pady=(12, 0))
        self.thumb_row = tk.Frame(self.left, bg=SOFT_BG)
        self.thumb_row.pack(fill="x", pady=(10, 0))
        self.thumbs = []
        for i, photo in enumerate(self.photos):
            self.thumb_row.grid_columnconfigure(i, weight=1, uniform="th")
            frame = tk.Frame(self.thumb_row, bg="#e5e7eb", cursor="hand2")
            frame.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 5, 5))
            box = PhotoBox(frame, photo, 70, radius=8, bg="#e5e7eb", tint=TINTS[i % len(TINTS)])
            box.pack(fill="x", padx=2, pady=2)
            for part in (frame, box):
                part.bind("<Button-1>", lambda e, k=i: self._show_photo(k))
            self.thumbs.append(frame)
        self._show_photo(0)

        tk.Label(self.left, text="Facilities Provided", font=self.f["h3"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w", pady=(34, 0))
        chips = tk.Frame(self.left, bg=SOFT_BG)
        chips.pack(anchor="w", pady=(12, 0))
        for n, item in enumerate(info["facilities"]):
            self._chip(chips, item).grid(row=n // 3, column=n % 3, sticky="w",
                                         padx=(0, 10), pady=(0, 10))

        tk.Label(self.left, text="Ground Rules", font=self.f["h3"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w", pady=(24, 0))
        for rule in RULES:
            lb = tk.Label(self.left, text=f"•  {rule}", font=self.f["p"], fg=SLATE, bg=SOFT_BG,
                          justify="left", anchor="w")
            lb.pack(anchor="w", pady=(8, 0))
            self._left_labels.append((lb, 0))

        # ---- right column: information card
        inner = self.right.inner
        tk.Label(inner, text="Ground Information", font=self.f["card_t"], fg=NAVY,
                 bg=WHITE).pack(anchor="w", pady=(0, 14))
        rows = (("👥", "CAPACITY", cap.replace("Capacity: ", "")),
                ("▦", "TYPE", info["type"]),
                ("📍", "ON CAMPUS", info["count"]),
                ("🕘", "OPENING HOURS", f"{hour_text(first)} – {hour_text(last)}"),
                ("📅", "OPEN DAYS", OPEN_DAYS),
                ("⏱", "BOOKING SLOT", BOOKING_SLOT))
        for glyph, caption, value in rows:
            row = tk.Frame(inner, bg=WHITE)
            row.pack(fill="x", pady=(0, 12))
            ic = tk.Canvas(row, width=30, height=30, bg=WHITE, highlightthickness=0)
            round_rect(ic, 0, 0, 30, 30, 8, fill=BLUE_HOVER, outline=BLUE_HOVER)
            ic.create_text(15, 15, text=glyph, fill=BLUE, font=self.f["small"])
            ic.pack(side="left", anchor="n")
            txt = tk.Frame(row, bg=WHITE)
            txt.pack(side="left", padx=(12, 0))
            tk.Label(txt, text=caption, font=self.f["cap"], fg=SLATE, bg=WHITE).pack(anchor="w")
            tk.Label(txt, text=value, font=self.f["val"], fg=NAVY, bg=WHITE,
                     justify="left").pack(anchor="w")
        tk.Frame(inner, bg="#e5e7eb", height=1).pack(fill="x", pady=(6, 16))
        WideButton(inner, "Reserve this Ground",
                   lambda n=name: self.app.navigate("reservation", ground=n), height=40,
                   radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE, font=self.f["btn"],
                   parent_bg=WHITE).pack(fill="x")
        WideButton(inner, "Back to About Us", lambda: self.app.navigate("about"), height=40,
                   radius=8, bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                   font=self.f["btn"], parent_bg=WHITE).pack(fill="x", pady=(10, 0))

        self._place(self._width)

    def _show_photo(self, i):
        """Show photo i large, and ring its thumbnail in blue."""
        for w in self.big.winfo_children():
            w.destroy()
        PhotoBox(self.big, self.photos[i], 260, radius=14, bg=SOFT_BG,
                 tint=TINTS[i % len(TINTS)]).pack(fill="x")
        for k, frame in enumerate(self.thumbs):
            frame.config(bg=BLUE if k == i else "#e5e7eb")

    def _chip(self, parent, text):
        outer = tk.Frame(parent, bg="#e5e7eb")
        inner = tk.Frame(outer, bg=WHITE)
        inner.pack(padx=1, pady=1)
        tk.Label(inner, text="✓", font=self.f["label_bold"], fg=BLUE,
                 bg=WHITE).pack(side="left", padx=(10, 4), pady=6)
        tk.Label(inner, text=text, font=self.f["small"], fg=NAVY,
                 bg=WHITE).pack(side="left", padx=(0, 12))
        return outer

    # ---- two columns on wide windows, stacked on narrow ones
    def _place(self, w):
        if not hasattr(self, "holder") or not self.holder.winfo_exists():
            return
        side = max(24, (w - self.MAXW) // 2)
        avail = w - 2 * side
        for it in (self.left, self.right):
            it.grid_forget()
        for i in range(2):
            self.holder.grid_columnconfigure(i, weight=0, uniform="")
        if w >= 900:
            self.holder.grid_columnconfigure(0, weight=2, uniform="gd")
            self.holder.grid_columnconfigure(1, weight=1, uniform="gd")
            self.left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
            self.right.grid(row=0, column=1, sticky="new", padx=(16, 0))
            colw = avail * 2 / 3 - 16
        else:
            self.holder.grid_columnconfigure(0, weight=1)
            self.left.grid(row=0, column=0, sticky="nsew")
            self.right.grid(row=1, column=0, sticky="new", pady=(24, 0))
            colw = avail
        for lb, margin in self._left_labels:
            lb.config(wraplength=max(120, int(colw - margin)))

    def _apply(self, w):
        super()._apply(w)
        self._width = w
        self._place(w)

    # ---- footer: exactly the About page's footer
    _footer = AboutPage._footer


if __name__ == "__main__":          # running this file directly starts the whole app
    import login
    login.App().mainloop()