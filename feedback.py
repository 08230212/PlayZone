"""feedback.py - the "Share Your Experience" feedback page and its "Thank You!" screen.

Connected to the rest of the app:
  * registered in login.py:  PAGES["feedback"] = (FeedbackPage, "PlayZone - Feedback")
  * opened from the nav bar's "Feedback" link on every page (common.py / home.py)
  * reuses a few widgets from reservation.py (LightEntry, LightSelect, DayCell, RoundedPopup)
  * every submitted feedback is appended to app.feedbacks (a list of dicts) and printed -
    plug your database / email in at FeedbackPage._submit().

Flow:  form  ->  "Submit Feedback"  ->  Thank You card  ->  "Back to Home"
"""
import calendar
import datetime
import math
import tkinter as tk
from tkinter import font as tkfont

from common import *
from about import PHONE, EMAIL
from data import GROUNDS
from reservation import (DayCell, LightEntry, LightSelect, RoundedPopup, WEEKDAYS,
                         pretty_date, ID_RE)

FB_W = 640            # width of the feedback card
TY_W = 480            # width of the thank-you card
CATEGORIES = ["Ground Condition", "Booking Process", "Facilities", "Staff",
              "Overall Experience"]
LIGHT = LightEntry.LIGHT
MONTHS_BACK = 24      # how far back "Date of Visit" can go


# ------------------------------------------------------------- star rating ---
class StarRating(tk.Canvas):
    """Five clickable stars. Hover previews the rating, click sets it (.get() -> 0..5)."""
    def __init__(self, parent, star=30, gap=10, parent_bg=WHITE):
        w = 5 * star + 4 * gap
        super().__init__(parent, width=w, height=star, bg=parent_bg, highlightthickness=0,
                         cursor="hand2")
        self.sz, self.gap = star, gap
        self.value, self._hover = 0, 0
        self._draw()
        self.bind("<Motion>", self._move)
        self.bind("<Leave>", lambda e: self._set_hover(0))
        self.bind("<Button-1>", self._click)

    def _points(self, i):
        cx, cy = i * (self.sz + self.gap) + self.sz / 2, self.sz / 2
        big, small = self.sz / 2 - 1, (self.sz / 2 - 1) * 0.45
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            r = big if k % 2 == 0 else small
            pts += [cx + r * math.cos(ang), cy + r * math.sin(ang)]
        return pts

    def _index_at(self, x):
        i = int(x // (self.sz + self.gap))
        inside = x - i * (self.sz + self.gap) <= self.sz
        return i + 1 if 0 <= i < 5 and inside else 0

    def _draw(self):
        self.delete("all")
        shown = self._hover or self.value
        for i in range(5):
            on = i < shown
            self.create_polygon(self._points(i), fill=AMBER if on else WHITE,
                                outline=AMBER if on else "#d1d5db", width=2,
                                joinstyle="round")

    def _move(self, e):
        self._set_hover(self._index_at(e.x))

    def _set_hover(self, n):
        if n != self._hover:
            self._hover = n
            self._draw()

    def _click(self, e):
        n = self._index_at(e.x)
        if n:
            self.value = n
            self._draw()

    def get(self):
        return self.value


# ----------------------------------------------------------- category chip ---
class CategoryChip(tk.Canvas):
    """Toggle chip with a little checkbox (several can be selected)."""
    H = 32

    def __init__(self, parent, text, font, parent_bg=WHITE):
        self.w = font.measure(text) + 56
        super().__init__(parent, width=self.w, height=self.H, bg=parent_bg,
                         highlightthickness=0, cursor="hand2")
        self.text, self.font = text, font
        self.selected, self._hover = False, False
        self._draw()
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", lambda e: self._toggle())

    def _draw(self):
        self.delete("all")
        fill = BLUE_SOFT if self.selected else ("#e2e8f0" if self._hover else "#f1f5f9")
        round_rect(self, 0, 0, self.w, self.H, 8, fill=fill, outline=fill)
        cy = self.H / 2
        if self.selected:
            round_rect(self, 12, cy - 7, 26, cy + 7, 4, fill=BLUE, outline=BLUE)
            self.create_text(19, cy, text="✓", fill=WHITE, font=self.font)
        else:
            round_rect(self, 12, cy - 7, 26, cy + 7, 4, fill=WHITE, outline="#cbd5e1")
        self.create_text(36, cy, text=self.text, anchor="w", font=self.font,
                         fill=BLUE_DARK if self.selected else NAVY)

    def _set_hover(self, on):
        self._hover = on
        self._draw()

    def _toggle(self):
        self.selected = not self.selected
        self._draw()


# ------------------------------------------------------- date of visit field ---
class DatePickerPopup(RoundedPopup):
    """Small rounded calendar pop-up. Only today and earlier dates can be picked."""
    def __init__(self, app, on_pick, current=None):
        super().__init__(app, 360)
        self.on_pick, self.current = on_pick, current
        self.today = datetime.date.today()
        base = current or self.today
        self.view = (base.year, base.month)
        self.f_title, self.f_day = self.F(16, True), self.F(13)
        self.f_cap, f_btn = self.F(11, True), self.F(14, True)

        head = tk.Frame(self.body, bg=WHITE)
        head.pack(fill="x")
        self.month_lbl = tk.Label(head, text="", font=self.f_title, fg=NAVY, bg=WHITE)
        self.month_lbl.pack(side="left")
        nav = tk.Frame(head, bg=WHITE)
        nav.pack(side="right")
        self.prev_btn, self.next_btn = [
            RoundedButton(nav, glyph, (lambda d=delta: self._shift(d)), 30, 30, radius=8,
                          bg=WHITE, hover=BLUE_SOFT, fg=NAVY, outline="#d1d5db",
                          font=self.f_title) for glyph, delta in (("‹", -1), ("›", 1))]
        self.prev_btn.pack(side="left")
        self.next_btn.pack(side="left", padx=(8, 0))
        self.days = tk.Frame(self.body, bg=WHITE)
        self.days.pack(fill="x", pady=(14, 0))
        self._show_month()
        WideButton(self.body, "Cancel", self.destroy, height=40, radius=8, bg=WHITE,
                   hover=BLUE_SOFT, fg=BLUE, outline=BLUE, font=f_btn).pack(
                       fill="x", pady=(14, 0))
        self.show()

    @staticmethod
    def _idx(y, m):
        return y * 12 + m - 1

    def _style_nav(self, btn, enabled):
        if btn._anim:
            btn.after_cancel(btn._anim)
            btn._anim = None
        btn._enabled = enabled
        btn._hover = BLUE_SOFT if enabled else WHITE
        btn.itemconfig(btn._text_id, fill=NAVY if enabled else "#cbd5e1")
        btn.config(cursor="hand2" if enabled else "arrow")

    def _show_month(self):
        y, m = self.view
        idx, now_idx = self._idx(y, m), self._idx(self.today.year, self.today.month)
        self.month_lbl.config(text=f"{calendar.month_name[m]} {y}")
        self._style_nav(self.prev_btn, idx > now_idx - MONTHS_BACK)
        self._style_nav(self.next_btn, idx < now_idx)
        for w in self.days.winfo_children():
            w.destroy()
        for c in range(7):
            self.days.grid_columnconfigure(c, weight=1, uniform="d")
        for c, name in enumerate(WEEKDAYS):
            tk.Label(self.days, text=name, font=self.f_cap, fg="#334155", bg=WHITE).grid(
                row=0, column=c, pady=(0, 4))
        for r, week in enumerate(calendar.monthcalendar(y, m), start=1):
            for c, day in enumerate(week):
                if not day:
                    continue
                d = datetime.date(y, m, day)
                DayCell(self.days, day, (lambda dt=d: self._pick(dt)),
                        disabled=d > self.today, today=d == self.today,
                        selected=d == self.current, font=self.f_day).grid(
                            row=r, column=c, pady=2)

    def _shift(self, delta):
        btn = self.prev_btn if delta < 0 else self.next_btn
        if not getattr(btn, "_enabled", True):
            return
        idx = self._idx(*self.view) + delta
        self.view = (idx // 12, idx % 12 + 1)
        self._show_month()

    def _pick(self, d):
        self.destroy()
        self.on_pick(d)


class DateField(tk.Canvas):
    """Looks like LightSelect but with a calendar icon; click it to open the date pop-up."""
    def __init__(self, parent, app, width, height=40, radius=12, font=None, parent_bg=WHITE):
        super().__init__(parent, width=width, height=height, bg=parent_bg,
                         highlightthickness=0, cursor="hand2")
        self.app, self.value = app, None
        self._box = round_rect(self, 1, 1, width - 1, height - 1, radius, fill=WHITE,
                               outline=LIGHT)
        self._text = self.create_text(16, height / 2, anchor="w", text="Select Date",
                                      font=font, fill=PLACEHOLDER)
        x, cy = width - 26, height / 2          # little calendar icon
        self.create_rectangle(x - 8, cy - 7, x + 8, cy + 8, outline=SLATE, width=1.5)
        self.create_line(x - 8, cy - 2, x + 8, cy - 2, fill=SLATE, width=1.5)
        self.create_line(x - 4, cy - 10, x - 4, cy - 5, fill=SLATE, width=1.5)
        self.create_line(x + 4, cy - 10, x + 4, cy - 5, fill=SLATE, width=1.5)
        self.bind("<Button-1>", lambda e: DatePickerPopup(self.app, self.set, self.value))

    def set(self, d):
        self.value = d
        self.itemconfig(self._text, text=pretty_date(d), fill=NAVY)
        self.clear_error()

    def get(self):
        return self.value

    def set_error(self):
        self.itemconfig(self._box, outline="#dc2626")

    def clear_error(self):
        self.itemconfig(self._box, outline=LIGHT)


# ------------------------------------------------------------------- page ---
class FeedbackPage(SectionPage):
    def __init__(self, app):
        super().__init__(app, "feedback")

        def F(size, bold=False):
            return tkfont.Font(family=app.family, size=-size,
                               weight="bold" if bold else "normal")
        self.f.update({"err": F(11), "q": F(16, True), "cap": F(11, True)})

        self.stage = "form"         # "form" or "thanks"
        self.block_w = FB_W         # width of the centred card
        self.block = None           # the centred block
        self._curw = 1200

        self._highlight_nav()
        self._shell()
        self._footer()
        self._render()

    def on_show(self, **kwargs):
        """Every visit starts with a fresh, empty form."""
        super().on_show(**kwargs)
        self.stage = "form"
        self._render()

    # ---- nav bar: highlight "Feedback" while on this page
    def _highlight_nav(self):
        for cell in self.links.winfo_children():
            lb, underline = cell.winfo_children()[0], cell.winfo_children()[1]
            if lb.cget("text") == "Feedback":
                lb.config(font=self.f["label_bold"], fg=BLUE)
                underline.config(bg=BLUE)
                lb.unbind("<Enter>")
                lb.unbind("<Leave>")
                lb.bind("<Button-1>", lambda e: self.on_show())   # clicking it = a fresh form

    # ---- skeleton (built once)
    def _shell(self):
        dyn = tk.Frame(self.body, bg=SOFT_BG)
        dyn.pack(fill="x")
        self.dyn_body = tk.Frame(dyn, bg=SOFT_BG)
        self.dyn_body.pack(fill="x", padx=40, pady=(40, 56))
        self._bodies.append(self.dyn_body)
        self.head = tk.Frame(self.dyn_body, bg=SOFT_BG)
        self.head.pack(fill="x")
        self.content = tk.Frame(self.dyn_body, bg=SOFT_BG)
        self.content.pack(fill="x", pady=(26, 0))

    def _render(self):
        for w in self.head.winfo_children() + self.content.winfo_children():
            w.destroy()
        self.block = None
        # An EMPTY frame keeps the height it had before (a Tk quirk) - that was the big gap
        # above the Thank You card. So the title block is only packed when it has content.
        if self.stage == "form":
            self.head.pack(fill="x", before=self.content)
        else:
            self.head.pack_forget()
        if self.stage == "form":
            self.block_w = FB_W
            tk.Label(self.head, text="YOUR VOICE MATTERS", font=self.f["tag"], fg=BLUE,
                     bg=SOFT_BG).pack()
            tk.Label(self.head, text="Share Your Experience", font=self.f["h1"], fg=NAVY,
                     bg=SOFT_BG).pack(pady=(8, 0))
            tk.Label(self.head, font=self.f["p"], fg=SLATE, bg=SOFT_BG, justify="center",
                     wraplength=620,
                     text="Your feedback helps us improve Play Zone and our sports facilities. "
                          "Tell us what went well and what we can do better.").pack(pady=(10, 0))
            self._form()
        else:
            self.block_w = TY_W
            self._thanks()
        self._center()
        self.scroll.canvas.yview_moveto(0)

    # ---------------------------------------------------------- the form
    def _form(self):
        self.block = tk.Frame(self.content, bg=SOFT_BG)
        self.block.pack(fill="x")
        card = Card(self.block, SOFT_BG, pad=28, border="#e5e7eb")
        card.pack(fill="x")
        inner = card.inner
        colw = (FB_W - 2 * 28 - 16) // 2 - 2

        # rating
        tk.Label(inner, text="How was your experience?", font=self.f["label_bold"], fg=NAVY,
                 bg=WHITE).pack()
        self.stars = StarRating(inner)
        self.stars.pack(pady=(10, 0))
        self.err_rating = tk.Label(inner, text="", font=self.f["err"], fg="#dc2626", bg=WHITE)
        self.err_rating.pack(pady=(4, 0))
        tk.Frame(inner, bg="#e5e7eb", height=1).pack(fill="x", pady=(8, 14))

        # two-column block: name | student id, ground | date
        grid = tk.Frame(inner, bg=WHITE)
        grid.pack(fill="x")
        for c in (0, 1):
            grid.grid_columnconfigure(c, weight=1)

        def cell(row, col, label, widget_factory):
            padx = (0, 8) if col == 0 else (8, 0)
            tk.Label(grid, text=label, font=self.f["btn"], fg=NAVY, bg=WHITE).grid(
                row=row, column=col, sticky="w", padx=padx, pady=(0, 6))
            widget = widget_factory()
            widget.grid(row=row + 1, column=col, sticky="w", padx=padx)
            err = tk.Label(grid, text="", font=self.f["err"], fg="#dc2626", bg=WHITE,
                           anchor="w")
            err.grid(row=row + 2, column=col, sticky="w", padx=(padx[0] + 4, 0), pady=(2, 6))
            return widget, err

        self.in_name, self.err_name = cell(
            0, 0, "Full Name", lambda: LightEntry(grid, "Enter your name", width=colw,
                                                  height=40, font=self.f["small"]))
        self.in_id, self.err_id = cell(
            0, 1, "Student ID", lambda: LightEntry(grid, "e.g. 08230212", width=colw,
                                                   height=40, font=self.f["small"]))
        self.in_ground, _ = cell(
            3, 0, "Ground Used", lambda: LightSelect(grid, [g[0] for g in GROUNDS], colw,
                                                     height=40, font=self.f["small"],
                                                     value="Football Ground"))
        self.in_date, self.err_date = cell(
            3, 1, "Date of Visit", lambda: DateField(grid, self.app, colw, height=40,
                                                     font=self.f["small"]))

        # categories (several can be chosen)
        tk.Label(inner, text="Feedback Categories", font=self.f["btn"], fg=NAVY,
                 bg=WHITE).pack(anchor="w", pady=(6, 8))
        chips = tk.Frame(inner, bg=WHITE)
        chips.pack(anchor="w")
        self.chips, x, row, col = [], 0, 0, 0
        room = FB_W - 2 * 28 - 4
        for name in CATEGORIES:
            chip = CategoryChip(chips, name, self.f["small"])
            if x and x + chip.w > room:               # start a new row when it doesn't fit
                row, col, x = row + 1, 0, 0
            chip.grid(row=row, column=col, padx=(0, 10), pady=(0, 10))
            x += chip.w + 10
            col += 1
            self.chips.append(chip)

        # free text
        tk.Label(inner, text="Your Feedback", font=self.f["btn"], fg=NAVY, bg=WHITE).pack(
            anchor="w", pady=(4, 6))
        self.in_text = FlexInput(inner, "Tell us about your experience...",
                                 font=self.f["small"], parent_bg=WHITE, multiline=True,
                                 height=88)
        self.in_text.config(bg=LIGHT)                 # soft grey border instead of black
        self.in_text.winfo_children()[0].config(bg=WHITE)
        self.in_text.widget.config(bg=WHITE)
        self.in_text.pack(fill="x")
        for part in (self.in_text, self.in_text.winfo_children()[0], self.in_text.widget):
            part.bind("<Button-1>", lambda e: self.in_text.widget.focus_force(), add="+")
        self.err_text = tk.Label(inner, text="", font=self.f["err"], fg="#dc2626", bg=WHITE,
                                 anchor="w")
        self.err_text.pack(fill="x", padx=4, pady=(2, 0))

        tk.Frame(inner, bg="#e5e7eb", height=1).pack(fill="x", pady=(14, 16))
        WideButton(inner, "Submit Feedback", self._submit, height=44, radius=8, bg=BLUE,
                   hover=BLUE_DARK, fg=WHITE, font=self.f["btn"]).pack(fill="x")

    @staticmethod
    def _flag(widget, label, message):
        """Show `message` in red under a field (empty message clears it)."""
        label.config(text=message)
        if hasattr(widget, "set_error"):
            widget.set_error() if message else widget.clear_error()

    def _submit(self):
        name, sid = self.in_name.get(), self.in_id.get()
        date, text, rating = self.in_date.get(), self.in_text.get(), self.stars.get()

        self._flag(self.stars, self.err_rating, "" if rating else "Please rate your experience.")
        self._flag(self.in_name, self.err_name, "" if name else "Please enter your name.")
        if not sid:
            self._flag(self.in_id, self.err_id, "Please enter your student ID.")
        elif not ID_RE.match(sid):
            self._flag(self.in_id, self.err_id, "Letters and numbers only.")
        else:
            self._flag(self.in_id, self.err_id, "")
        self._flag(self.in_date, self.err_date, "" if date else "Please select the date.")
        self.err_text.config(text="" if text else "Please tell us about your experience.")
        self.in_text.config(bg="#dc2626" if not text else LIGHT)
        if not (rating and name and sid and ID_RE.match(sid) and date and text):
            return

        record = dict(name=name, student_id=sid, rating=rating, ground=self.in_ground.get(),
                      date=date, categories=[c.text for c in self.chips if c.selected],
                      message=text)
        if not hasattr(self.app, "feedbacks"):
            self.app.feedbacks = []
        self.app.feedbacks.append(record)
        print("[feedback]", record)          # <-- save it / email it here
        self.app._notif_unread = 1           # <- light up the admin bell
        self.stage = "thanks"
        self._render()

    # ------------------------------------------------------ thank-you card
    def _thanks(self):
        self.block = tk.Frame(self.content, bg=SOFT_BG)
        self.block.pack(fill="x", pady=(4, 0))
        card = Card(self.block, SOFT_BG, pad=36, border="#e5e7eb")
        card.pack(fill="x")
        inner = card.inner

        ic = tk.Canvas(inner, width=72, height=72, bg=WHITE, highlightthickness=0)
        ic.create_oval(2, 2, 70, 70, fill="#fee2e2", outline="#fee2e2")
        ic.create_text(36, 37, text="♡", fill="#ef4444",
                       font=tkfont.Font(family=self.app.family, size=-30))
        ic.pack()
        tk.Label(inner, text="Thank You!", font=self.f["h2"], fg=NAVY, bg=WHITE).pack(
            pady=(16, 0))
        wl = TY_W - 2 * 36 - 20
        tk.Label(inner, text="Thank you for sharing your experience with Play Zone.",
                 font=self.f["small"], fg=SLATE, bg=WHITE, wraplength=wl,
                 justify="center").pack(pady=(14, 0))
        tk.Label(inner, text="Your feedback has been successfully submitted and helps build "
                             "a stronger sports community.",
                 font=self.f["small"], fg=SLATE, bg=WHITE, wraplength=wl,
                 justify="center").pack(pady=(6, 0))
        tk.Frame(inner, bg="#e5e7eb", height=1).pack(fill="x", pady=(22, 20))
        RoundedButton(inner, "Back to Home", lambda: self.app.navigate("home"), 140, 40,
                      radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                      font=self.f["btn"]).pack()

    # ---- keep the card centred on wide windows
    def _apply(self, w):
        super()._apply(w)
        self._curw = w
        self._center()

    def _center(self):
        if self.block is None or not self.block.winfo_exists():
            return
        side = max(24, (self._curw - self.MAXW) // 2)
        avail = self._curw - 2 * side
        self.block.pack_configure(padx=max(0, (avail - self.block_w) // 2))

    # ---- footer (same as home / about / events / reservation)
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


if __name__ == "__main__":          # running this file directly starts the whole app
    import login
    login.App().mainloop()