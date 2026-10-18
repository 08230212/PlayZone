"""event_detail.py - the "Event Details" page.

Connected to the rest of the app:
  * registered in login.py:  PAGES["event_detail"] = (EventDetailPage, "PlayZone - Event Details")
  * opened from events.py's "View Details" button via
        app.navigate("event_detail", event=<that event's dict>)
    and read back here in on_show(self, event=None)
  * "Back to Events" goes back to the events page.
  * "Register" opens the registration pop-ups defined at the bottom of this
    file (RegisterDialog -> ConfirmDialog -> SuccessDialog); every confirmed
    registration is appended to app.registrations (plug a database in at
    RegisterDialog._save()). For events whose status is "Completed" the Register button is disabled and
    the page says the event is already completed.

Optional extra keys you can add to any event dict in events.py (sensible
defaults are used if they're missing):
    "description"  - the "About the Event" paragraph
    "facilities"   - list of strings for "Included Facilities"
    "participants" - text shown next to PARTICIPANTS
"""
import datetime
import os
import re
import tkinter as tk
from tkinter import font as tkfont, messagebox

from common import *
from about import PHONE, EMAIL   # same contact details as the About page
from data import event_status    # Upcoming / Completed, worked out from the event's date

# ------------------------------------------------------------------ DATA ---
DEFAULT_PARTICIPANTS = "College Students Only"

DESCRIPTIONS = {
    "Football": ("Join us for an exciting inter-college football tournament designed to "
                 "encourage teamwork, sportsmanship, and healthy competition among students. "
                 "Teams from different sections will converge on our premium varsity complex "
                 "to claim the autumn league trophy."),
}

FACILITIES = {
    "Football": ["Football Ground", "Drinking Water", "Seating Area", "First Aid"],
    "Basketball": ["Basketball Court", "Drinking Water", "Seating Area", "First Aid"],
    "Volleyball": ["Volleyball Court", "Drinking Water", "Seating Area", "First Aid"],
    "Indoor Sports": ["Indoor Sports Hall", "Drinking Water", "Seating Area", "First Aid"],
}


def description_for(ev):
    if ev.get("description"):
        return ev["description"]
    if ev["category"] in DESCRIPTIONS:
        return DESCRIPTIONS[ev["category"]]
    return (f"Join us for the {ev['title']}, a campus event designed to encourage teamwork, "
            "sportsmanship, and healthy competition among students. Come to play, bring "
            "your team, or cheer for your department!")


# ------------------------------------------------------------ hero banner ---
class HeroBanner(tk.Canvas):
    """Wide rounded event photo, darkened towards the bottom, with badge(s)
    and the event title drawn on top (like the Figma design)."""
    H = 250

    def __init__(self, parent, filename, title, badges, title_font, badge_font):
        super().__init__(parent, height=self.H, bg=SOFT_BG, highlightthickness=0)
        self.title_text, self.badges = title, badges      # badges: [(text, fg, fill)]
        self.title_font, self.badge_font = title_font, badge_font
        self._src, self._photo, self._last = None, None, 0
        path = os.path.join(ASSETS_DIR, filename)
        if PIL_OK and os.path.exists(path):
            self._src = Image.open(path).convert("RGB")
        self.bind("<Configure>", self._on_cfg)

    def _on_cfg(self, e):
        if e.width < 20 or e.width == self._last:
            return
        self._last = e.width
        self._draw(e.width)

    def _draw(self, w):
        h, r = self.H, 16
        self.delete("all")
        if self._src is None:
            round_rect(self, 0, 0, w, h, r, fill=NAVY, outline=NAVY)
        else:
            img = ImageOps.fit(self._src, (w, h), Image.LANCZOS)
            grad = Image.new("L", (1, h))
            for y in range(h):
                t = max(0.0, (y - h * 0.3) / (h * 0.7))
                grad.putpixel((0, y), int(190 * t))
            img.paste(Image.new("RGB", (w, h), (15, 23, 42)), (0, 0), grad.resize((w, h)))
            mask = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
            out = Image.new("RGB", (w, h), ImageColor.getrgb(SOFT_BG))
            out.paste(img, (0, 0), mask)
            self._photo = ImageTk.PhotoImage(out)
            self.create_image(0, 0, image=self._photo, anchor="nw")

        pad = 28
        title_h = self.title_font.metrics("linespace")
        self.create_text(pad, h - pad, text=self.title_text, fill=WHITE,
                         font=self.title_font, anchor="sw")
        bh = self.badge_font.metrics("linespace") + 10
        by = h - pad - title_h - 12 - bh
        x = pad
        for text, fg, fill in self.badges:
            bw = self.badge_font.measure(text) + 24
            round_rect(self, x, by, x + bw, by + bh, bh // 2, fill=fill, outline=fill)
            self.create_text(x + bw / 2, by + bh / 2, text=text, fill=fg, font=self.badge_font)
            x += bw + 8


# ------------------------------------------------------------------ page ---
class EventDetailPage(SectionPage):
    def __init__(self, app):
        super().__init__(app, "events")        # keeps "Events" highlighted in the nav bar
        self._event = None
        self._width = 1200
        self._left_labels = []

        def F(size, bold=False):
            return tkfont.Font(family=app.family, size=-size,
                               weight="bold" if bold else "normal")
        self.f.update({"h3": F(20, True), "cap": F(10, True), "val": F(13, True),
                       "hero": F(34, True)})

        # on this page "Events" should go back to the events LIST (the base class
        # would just scroll this page to the top because it is the "current" link)
        for cell in self.links.winfo_children():
            lb = cell.winfo_children()[0]
            if lb.cget("text") == "Events":
                lb.bind("<Button-1>", lambda e: self.app.navigate("events"))

        # the part that changes per event lives in one persistent frame
        dyn = tk.Frame(self.body, bg=SOFT_BG)
        dyn.pack(fill="x")
        self.dyn_body = tk.Frame(dyn, bg=SOFT_BG)
        self.dyn_body.pack(fill="x", padx=40, pady=(32, 56))
        self._bodies.append(self.dyn_body)

        self._footer()

    def on_show(self, event=None, **kwargs):
        super().on_show(**kwargs)
        if event is not None:
            self._event = event
        if self._event is None:                 # opened with nothing to show
            self.app.navigate("events")
            return
        self._build(self._event)

    # ---- build everything that depends on the chosen event
    def _build(self, ev):
        for w in self.dyn_body.winfo_children():
            w.destroy()
        self._left_labels = []
        completed = event_status(ev) == "Completed"

        badges = [(ev["category"], WHITE, GREEN)]
        if completed:
            badges.append(("Completed", WHITE, SLATE))
        HeroBanner(self.dyn_body, ev["image"], ev["title"], badges,
                   self.f["hero"], self.app.f_badge).pack(fill="x")

        self.holder = tk.Frame(self.dyn_body, bg=SOFT_BG)
        self.holder.pack(fill="x", pady=(28, 0))
        self.left = tk.Frame(self.holder, bg=SOFT_BG)
        self.right = Card(self.holder, SOFT_BG, pad=22)

        # ---- left column: notice (if completed), about, facilities
        if completed:
            note = tk.Frame(self.left, bg="#fef3c7")
            note.pack(fill="x", pady=(0, 22))
            lb = tk.Label(note, text="This event has already been completed. "
                                     "Registration is closed.",
                          font=self.f["label_bold"], fg="#92400e", bg="#fef3c7",
                          justify="left", anchor="w")
            lb.pack(anchor="w", padx=16, pady=12)
            self._left_labels.append((lb, 32))

        tk.Label(self.left, text="About the Event", font=self.f["h3"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")
        about = tk.Label(self.left, text=description_for(ev), font=self.f["p"], fg=SLATE,
                         bg=SOFT_BG, justify="left", anchor="w")
        about.pack(anchor="w", pady=(12, 0))
        self._left_labels.append((about, 0))

        tk.Label(self.left, text="Included Facilities", font=self.f["card_t"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w", pady=(40, 0))
        chips = tk.Frame(self.left, bg=SOFT_BG)
        chips.pack(anchor="w", pady=(12, 0))
        for item in ev.get("facilities") or FACILITIES.get(ev["category"], []):
            self._chip(chips, item).pack(side="left", padx=(0, 10))

        # ---- right column: event information card
        inner = self.right.inner
        tk.Label(inner, text="Event Information", font=self.f["card_t"], fg=NAVY,
                 bg=WHITE).pack(anchor="w", pady=(0, 14))
        rows = (("🗓", "DATE", ev["date"]), ("🕘", "TIME", ev["time"]),
                ("📍", "LOCATION", ev["location"]), ("👤", "ORGANIZER", ev["organizer"]),
                ("👥", "PARTICIPANTS", ev.get("participants", DEFAULT_PARTICIPANTS)))
        for glyph, cap, value in rows:
            row = tk.Frame(inner, bg=WHITE)
            row.pack(fill="x", pady=(0, 12))
            ic = tk.Canvas(row, width=30, height=30, bg=WHITE, highlightthickness=0)
            round_rect(ic, 0, 0, 30, 30, 8, fill=BLUE_HOVER, outline=BLUE_HOVER)
            ic.create_text(15, 15, text=glyph, fill=BLUE, font=self.f["small"])
            ic.pack(side="left", anchor="n")
            txt = tk.Frame(row, bg=WHITE)
            txt.pack(side="left", padx=(12, 0))
            tk.Label(txt, text=cap, font=self.f["cap"], fg=SLATE, bg=WHITE).pack(anchor="w")
            tk.Label(txt, text=value, font=self.f["val"], fg=NAVY, bg=WHITE,
                     justify="left").pack(anchor="w")

        tk.Frame(inner, bg="#e5e7eb", height=1).pack(fill="x", pady=(6, 16))

        if completed:
            btn = WideButton(inner, "Event Completed", lambda: None, height=40, radius=8,
                             bg="#e2e8f0", hover="#e2e8f0", fg="#94a3b8",
                             font=self.f["btn"], parent_bg=WHITE)
            btn.config(cursor="arrow")
            btn.pack(fill="x")
            tk.Label(inner, text="Registration is closed for this event.",
                     font=self.f["small"], fg=SLATE, bg=WHITE).pack(pady=(8, 0))
        else:
            WideButton(inner, "Register", lambda e=ev: self._register(e), height=40, radius=8,
                       bg=BLUE, hover=BLUE_DARK, fg=WHITE, font=self.f["btn"],
                       parent_bg=WHITE).pack(fill="x")
        WideButton(inner, "Back to Events", lambda: self.app.navigate("events"), height=40,
                   radius=8, bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                   font=self.f["btn"], parent_bg=WHITE).pack(fill="x", pady=(10, 0))

        self._place(self._width)

    def _chip(self, parent, text):
        outer = tk.Frame(parent, bg="#e5e7eb")
        inner = tk.Frame(outer, bg=WHITE)
        inner.pack(padx=1, pady=1)
        tk.Label(inner, text="✓", font=self.f["label_bold"], fg=BLUE,
                 bg=WHITE).pack(side="left", padx=(10, 4), pady=6)
        tk.Label(inner, text=text, font=self.f["small"], fg=NAVY,
                 bg=WHITE).pack(side="left", padx=(0, 12))
        return outer

    def _register(self, ev):
        RegisterDialog(self.app, ev)      # form -> confirm -> success (defined below)

    # ---- two columns on wide windows, stacked on narrow ones
    def _place(self, w):
        if not hasattr(self, "holder") or not self.holder.winfo_exists():
            return
        side = max(24, (w - self.MAXW) // 2)
        avail = w - 2 * side
        wide = w >= 900
        for it in (self.left, self.right):
            it.grid_forget()
        for i in range(2):
            self.holder.grid_columnconfigure(i, weight=0, uniform="")
        if wide:
            self.holder.grid_columnconfigure(0, weight=2, uniform="dt")
            self.holder.grid_columnconfigure(1, weight=1, uniform="dt")
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

    # ---- footer (same as about.py / events.py)
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


# ======================================================================
#  REGISTRATION POP-UPS   RegisterDialog -> ConfirmDialog -> SuccessDialog
#  Screen-responsive: every pop-up caps its width to the screen, sizes its
#  height to its content, and shows a scrollbar (mouse-wheel works too) when
#  the content is taller than the screen.
# ======================================================================
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^A-Za-z]*[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9 \-]{6,17}$")
ID_RE = re.compile(r"^[A-Za-z0-9]+$")
GREEN_DARK = "#15803d"


def short_date(date_text):
    """'15 September 2026' -> '15 Sept 2026' (other months -> first 3 letters)."""
    parts = date_text.split()
    if len(parts) == 3:
        month = "Sept" if parts[1] == "September" else parts[1][:3]
        return f"{parts[0]} {month} {parts[2]}"
    return date_text


def make_reg_id(app, ev):
    """e.g. PZ-EVENT-2026-001 (counter = how many registrations so far + 1)."""
    year = ev["date"].split()[-1] if ev["date"].split()[-1].isdigit() else "2026"
    n = len(getattr(app, "registrations", [])) + 1
    return f"PZ-EVENT-{year}-{n:03d}"


class _PopupBase(tk.Toplevel):
    """Shared set-up for all three pop-ups.
    * `max_w`   - the width it wants on a big screen (shrinks on a small one)
    * `self.dw` - the actual width, `self.fw` - width available for content
    * put your widgets in `self.body`, then call `self.fit()` once, then `self.modal()`
    """
    PAD = 30

    def __init__(self, app, max_w, window_title, parent=None):
        super().__init__(app)
        self.withdraw()                       # stay hidden until fit() has sized it
        self.app = app
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(parent or app)
        self.wm_title(window_title)
        self.sw, self.sh = app.winfo_screenwidth(), app.winfo_screenheight()
        self.dw = min(max_w, self.sw - 40)
        self.fw = self.dw - 2 * self.PAD

        # scrollable area (the scrollbar only appears if the content is too tall)
        self.canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=WHITE)
        self._body_win = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._body_win, width=e.width))
        self._scrolling = False
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind(seq, self._wheel)
        self.bind("<Escape>", lambda e: self.destroy())

    def _wheel(self, e):
        if self._scrolling:
            num = getattr(e, "num", 0)
            d = -1 if num == 4 else 1 if num == 5 else (-1 if e.delta > 0 else 1)
            self.canvas.yview_scroll(d * 3, "units")
        return "break"          # never let the page behind the pop-up scroll

    def F(self, size, bold=False):
        f = tkfont.Font(family=self.app.family, size=-size,
                        weight="bold" if bold else "normal")
        self.__dict__.setdefault("_fonts", []).append(f)     # keep references
        return f

    def max_height(self):
        """Tallest the pop-up may be: it has to fit inside the app window
        (and the screen), so it never hangs off the page behind it."""
        return max(300, min(self.sh - 100, self.app.winfo_height() - 40))

    def fit(self):
        """Size the window to its content (capped to the screen), centre it
        over the main window, then show it."""
        self.update_idletasks()
        need = self.body.winfo_reqheight()
        max_h = self.max_height()
        h = min(need, max_h)
        self._scrolling = need > max_h
        if self._scrolling:
            self.vsb.pack(side="right", fill="y")
        x = self.app.winfo_rootx() + (self.app.winfo_width() - self.dw) // 2
        y = self.app.winfo_rooty() + (self.app.winfo_height() - h) // 2
        x = clamp(x, 0, max(0, self.sw - self.dw))
        y = clamp(y, 0, max(0, self.sh - h - 60))
        self.geometry(f"{self.dw}x{h}+{x}+{y}")
        self.deiconify()

    def modal(self):
        self.update_idletasks()
        try:
            self.grab_set()
        except tk.TclError:
            self.after(100, self._retry_grab)

    def _retry_grab(self):
        try:
            self.grab_set()
        except tk.TclError:
            pass


# ----------------------------------------------------------- 1. the form ---
class _LightEntry(RoundedEntry):
    """RoundedEntry restyled for the pop-up: white fill + soft grey border
    (blue while focused, red on error) instead of the heavy black outline."""
    LIGHT = "#d1d5db"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.itemconfig(self._box, fill=WHITE, outline=self.LIGHT)
        self.entry.config(bg=WHITE)
        self.placeholder.config(bg=WHITE)

    def _focus_out(self, _):
        if not self._error:
            self.itemconfig(self._box, outline=self.LIGHT)

    def clear_error(self):
        if self._error:
            self._error = False
            focused = self.focus_get() is self.entry
            self.itemconfig(self._box, outline=BLUE if focused else self.LIGHT)


class RegisterDialog(_PopupBase):
    FIELDS = [("student_id", "Student ID", "Enter your student ID"),
              ("email", "Email Address", "08230212.sce@rub.edu.bt"),
              ("phone", "Phone Number", "e.g. +975"),
              ("team", "Team / Group Name", "Enter your team name")]

    def __init__(self, app, ev):
        super().__init__(app, 460, "Register for Event")
        self.ev = ev
        self._build(compact=False)
        self.update_idletasks()
        if self.body.winfo_reqheight() > self.max_height():
            self._build(compact=True)       # not enough room -> tighter spacing
        self.bind("<Return>", lambda e: self.submit())
        self.fit()
        self.modal()
        self.inputs["student_id"].entry.focus_set()

    def _build(self, compact):
        for w in self.body.winfo_children():
            w.destroy()
        ev, pad, fw = self.ev, self.PAD, self.fw
        if compact:
            s = dict(title=22, label=13, err=10, eh=38, top=18, gap=2,
                     divider=(10, 4), lab=4, btn=40, bottom=18, errpad=0)
        else:
            s = dict(title=26, label=14, err=11, eh=44, top=28, gap=4,
                     divider=(16, 10), lab=6, btn=44, bottom=28, errpad=2)
        f_title, f_sub = self.F(s["title"], True), self.F(14 if not compact else 13)
        f_label, f_input = self.F(s["label"], True), self.F(14 if not compact else 13)
        f_err, f_btn = self.F(s["err"]), self.F(15, True)

        tk.Label(self.body, text="Register for Event", font=f_title, fg=NAVY,
                 bg=WHITE).pack(anchor="w", padx=pad, pady=(s["top"], 0))
        tk.Label(self.body, text=f"{ev['title']}  •  {short_date(ev['date'])}", font=f_sub,
                 fg=SLATE, bg=WHITE, wraplength=fw, justify="left").pack(
                     anchor="w", padx=pad, pady=(4, 0))
        tk.Frame(self.body, bg="#e5e7eb", height=1).pack(fill="x", padx=pad, pady=s["divider"])

        self.inputs, self.errors = {}, {}
        for key, label, placeholder in self.FIELDS:
            wrap = tk.Frame(self.body, bg=WHITE)
            wrap.pack(fill="x", padx=pad, pady=(s["gap"], 0))
            tk.Label(wrap, text=label, font=f_label, fg=NAVY, bg=WHITE).pack(
                anchor="w", pady=(0, s["lab"]))
            entry = _LightEntry(wrap, placeholder, width=fw, height=s["eh"], font=f_input)
            entry.pack(anchor="w")
            err = tk.Label(wrap, text="", font=f_err, fg="#dc2626", bg=WHITE,
                           anchor="w", justify="left", wraplength=fw)
            err.pack(fill="x", padx=4, pady=(s["errpad"], 0))
            self.inputs[key], self.errors[key] = entry, err

        RoundedButton(self.body, "Register", self.submit, fw, s["btn"], radius=10, bg=BLUE,
                      hover=BLUE_DARK, fg=WHITE, font=f_btn).pack(
                          padx=pad, anchor="w", pady=(10, s["bottom"]))

    def _check(self, key, message, ok):
        if ok:
            self.inputs[key].clear_error()
            self.errors[key].config(text="")
        else:
            self.inputs[key].set_error()
            self.errors[key].config(text=message)
        return ok

    def submit(self):
        v = {k: self.inputs[k].get() for k in self.inputs}
        ok = True
        if not v["student_id"]:
            ok &= self._check("student_id", "Please enter your student ID.", False)
        else:
            ok &= self._check("student_id", "Student ID can only contain letters and numbers.",
                              bool(ID_RE.match(v["student_id"])))
        if not v["email"]:
            ok &= self._check("email", "Please enter your email.", False)
        else:
            ok &= self._check("email", "Please enter a valid email address.",
                              bool(EMAIL_RE.match(v["email"])))
        if not v["phone"]:
            ok &= self._check("phone", "Please enter your phone number.", False)
        else:
            ok &= self._check("phone", "Please enter a valid phone number.",
                              bool(PHONE_RE.match(v["phone"])))
        ok &= self._check("team", "Please enter your team or group name.", bool(v["team"]))
        if not ok:
            return

        already = any(r["email"].lower() == v["email"].lower() and r["event"] == self.ev["title"]
                      for r in getattr(self.app, "registrations", []))
        if already:
            messagebox.showwarning("Already registered",
                                   "This email is already registered for this event.",
                                   parent=self)
            return

        ConfirmDialog(self.app, self.ev, lambda: self._save(v), parent=self)

    def _save(self, values):
        """Called after the user presses 'Confirm Registration'."""
        if not hasattr(self.app, "registrations"):
            self.app.registrations = []
        reg_id = make_reg_id(self.app, self.ev)
        record = dict(values, id=reg_id, event=self.ev["title"], date=self.ev["date"])
        self.app.registrations.append(record)
        print("[registration]", record)      # <-- save to your database here
        self.destroy()
        SuccessDialog(self.app, self.ev, reg_id)


# ------------------------------------------------------- 2. confirm popup ---
class ConfirmDialog(_PopupBase):
    def __init__(self, app, ev, on_confirm, parent):
        super().__init__(app, 560, "Confirm Registration", parent=parent)
        self.parent_dialog, self.on_confirm = parent, on_confirm
        pad, fw = self.PAD, self.fw
        f_title, f_sub = self.F(22, True), self.F(14)
        f_cap, f_ev, f_small, f_btn = self.F(12, True), self.F(17, True), self.F(14), self.F(15, True)

        top = tk.Frame(self.body, bg=WHITE)
        top.pack(fill="x", padx=pad, pady=(30, 0))
        icon = tk.Canvas(top, width=64, height=64, bg=WHITE, highlightthickness=0)
        round_rect(icon, 0, 0, 64, 64, 20, fill=BLUE_HOVER, outline=BLUE_HOVER)
        icon.create_oval(20, 20, 44, 44, outline=BLUE, width=2)
        icon.create_text(32, 32, text="?", fill=BLUE, font=self.F(16, True))
        icon.pack(side="left", anchor="n")
        txt = tk.Frame(top, bg=WHITE)
        txt.pack(side="left", padx=(16, 0), anchor="n")
        tk.Label(txt, text="Confirm Registration?", font=f_title, fg=NAVY,
                 bg=WHITE).pack(anchor="w")
        tk.Label(txt, text="Are you sure you want to register for this event?", font=f_sub,
                 fg=SLATE, bg=WHITE, wraplength=max(120, fw - 80),
                 justify="left").pack(anchor="w", pady=(2, 0))

        card = Card(self.body, WHITE, fill=SOFT_BG, border="#eef2f7", radius=12, pad=18)
        card.pack(fill="x", padx=pad, pady=(22, 0))
        inner_w = max(120, fw - 40)
        tk.Label(card.inner, text="EVENT SUMMARY", font=f_cap, fg=SLATE,
                 bg=SOFT_BG).pack(anchor="w")
        tk.Label(card.inner, text=ev["title"], font=f_ev, fg=NAVY, bg=SOFT_BG,
                 wraplength=inner_w, justify="left").pack(anchor="w", pady=(8, 6))
        tk.Label(card.inner, text=f"Date: {ev['date']}  •  {ev['location']}", font=f_small,
                 fg=SLATE, bg=SOFT_BG, wraplength=inner_w, justify="left").pack(anchor="w")

        btns = tk.Frame(self.body, bg=WHITE)
        btns.pack(anchor="e", padx=pad, pady=(22, 28))
        RoundedButton(btns, "Cancel", self.cancel, 110, 44, radius=10, bg=WHITE,
                      hover=BLUE_SOFT, fg=NAVY, outline="#d1d5db",
                      font=f_btn).pack(side="left")
        RoundedButton(btns, "Confirm Registration", self.confirm,
                      max(140, min(200, fw - 110 - 12)), 44, radius=10,
                      bg=BLUE, hover=BLUE_DARK, fg=WHITE, font=f_btn).pack(
                          side="left", padx=(12, 0))

        self.bind("<Escape>", lambda e: self.cancel())
        self.bind("<Return>", lambda e: self.confirm())
        self.fit()
        self.modal()

    def cancel(self):
        self.destroy()
        try:
            self.parent_dialog.grab_set()      # hand control back to the form
        except tk.TclError:
            pass

    def confirm(self):
        self.destroy()
        self.on_confirm()


# ------------------------------------------------------- 3. success popup ---
class SuccessDialog(_PopupBase):
    def __init__(self, app, ev, reg_id):
        super().__init__(app, 480, "Registration Successful")
        pad, fw = self.PAD, self.fw
        f_title, f_msg = self.F(28, True), self.F(14)
        f_cap, f_val, f_btn = self.F(11, True), self.F(13, True), self.F(14, True)

        # green circle with a hand-drawn trophy
        ic = tk.Canvas(self.body, width=76, height=76, bg=WHITE, highlightthickness=0)
        ic.create_oval(2, 2, 74, 74, fill="#dcfce7", outline="#dcfce7")
        g = GREEN_DARK
        ic.create_polygon(27, 22, 49, 22, 49, 34, 43, 43, 33, 43, 27, 34,
                          outline=g, fill="", width=2)
        ic.create_arc(18, 25, 29, 38, start=90, extent=180, style="arc", outline=g, width=2)
        ic.create_arc(47, 25, 58, 38, start=270, extent=180, style="arc", outline=g, width=2)
        ic.create_line(38, 43, 38, 51, fill=g, width=2)
        ic.create_line(30, 52, 46, 52, fill=g, width=2)
        ic.pack(pady=(30, 0))

        tk.Label(self.body, text="Registration Successful!", font=f_title, fg=GREEN_DARK,
                 bg=WHITE, wraplength=fw, justify="center").pack(pady=(14, 0))
        tk.Label(self.body, text=(f"You have successfully registered for the {ev['title']}. "
                                  "A confirmation email has been sent to your university account."),
                 font=f_msg, fg=SLATE, bg=WHITE, wraplength=fw - 20,
                 justify="center").pack(pady=(10, 0))

        card = Card(self.body, WHITE, fill=SOFT_BG, border="#eef2f7", radius=12, pad=18)
        card.pack(fill="x", padx=pad, pady=(20, 0))
        tk.Label(card.inner, text="BOOKING RECEIPT DETAILS", font=f_cap, fg=SLATE,
                 bg=SOFT_BG).pack(anchor="w", pady=(0, 10))
        grid = tk.Frame(card.inner, bg=SOFT_BG)
        grid.pack(fill="x")
        grid.grid_columnconfigure(1, weight=1)
        for i, (k, v) in enumerate((("Event", ev["title"]), ("Date", ev["date"]),
                                    ("Registration ID", reg_id))):
            tk.Label(grid, text=k, font=f_msg, fg=SLATE, bg=SOFT_BG).grid(
                row=i, column=0, sticky="w", pady=4)
            tk.Label(grid, text=v, font=f_val, fg=NAVY, bg=SOFT_BG,
                     wraplength=max(100, fw - 36 - 120),
                     justify="right").grid(row=i, column=1, sticky="e", pady=4, padx=(16, 0))

        WideButton(self.body, "Back to Events", self.back, height=44, radius=10, bg=BLUE,
                   hover=BLUE_DARK, fg=WHITE, font=f_btn).pack(
                       fill="x", padx=pad, pady=(22, 28))

        self.bind("<Return>", lambda e: self.back())
        self.fit()
        self.modal()

    def back(self):
        self.destroy()
        self.app.navigate("events")


if __name__ == "__main__":          # running this file directly starts the whole app
    import login
    login.App().mainloop()