"""reservation.py - the "Reserve Your Ground" booking page."""
import calendar
import datetime
import re
import sys
import tkinter as tk
from tkinter import font as tkfont, messagebox

from common import *
from about import PHONE, EMAIL
from data import (GROUNDS, OPEN_HOUR, CLOSE_HOUR, STATUS_STYLE, booked_slots,
                  ground_status, ground_hours, image_or, get_event_block)

STEP_LABELS = ["Select Ground", "Select Date", "Select Time", "Your Information"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
REVIEW_LABELS = ["Select Ground", "Pick Date", "Choose Time", "Confirm Details"]
SUM_W = 500
DONE_W = 520
GREEN_DARK = "#15803d"
RESERVE_IMAGES = {"Football Ground": "reserve_football.jpg",
                  "Basketball Court": "reserve_basketball.jpg",
                  "Volleyball Court": "reserve_volleyball.jpg",
                  "Indoor Sports Hall": "reserve_indoor.jpg"}
MAX_MONTHS_AHEAD = 6
CAL_W = 640
INFO_FIELDS = [("name", "Full Name", "Enter your name"),
               ("student_id", "Student ID", "e.g. 08230212"),
               ("email", "Email Address", "08230212.sce@rub.edu.bt"),
               ("phone", "Phone Number", "e.g. +975")]
PURPOSES = ["Practice", "Match", "Tournament", "Training Session", "Other"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9 \-]{6,17}$")
ID_RE = re.compile(r"^[A-Za-z0-9]+$")


def pretty_date(d):
    return f"{d.day} {calendar.month_name[d.month]} {d.year}"


def hour_label(h):
    return f"{h % 12 or 12}:00 {'AM' if h < 12 else 'PM'}"


def slot_label(h):
    return f"{hour_label(h)} – {hour_label(h + 1)}"


# ---------------------------------------------------------------- calendar day ---
class DayCell(tk.Canvas):
    SIZE = 40
    HOVER = "#93a8f5"

    def __init__(self, parent, day, command, disabled=False, today=False,
                 selected=False, font=None, has_event=False):
        super().__init__(parent, width=self.SIZE, height=self.SIZE, bg=WHITE,
                         highlightthickness=0,
                         cursor="arrow" if disabled else "hand2")
        self._command, self.disabled = command, disabled
        self.today, self.selected = today, selected
        self.has_event = has_event
        self._hover, self._anim = False, None
        s = self.SIZE
        self._shape = round_rect(self, 1, 1, s - 1, s - 1, 10, fill=WHITE,
                                 outline=WHITE)
        self._label = self.create_text(s / 2, s / 2, text=str(day), font=font,
                                       fill=NAVY)
        self._paint()
        if not disabled:
            self.bind("<Enter>", lambda e: self._set_hover(True))
            self.bind("<Leave>", lambda e: self._set_hover(False))
            self.bind("<ButtonRelease-1>", lambda e: self._command())

    def _colors(self):
        if self.disabled or self.has_event:
            return WHITE, WHITE, "#cbd5e1"
        if self.selected:
            return BLUE, BLUE, WHITE
        if self._hover:
            return self.HOVER, self.HOVER, WHITE
        return WHITE, (BLUE if self.today else WHITE), NAVY

    def _paint(self, fade=False):
        fill, outline, text = self._colors()
        self.itemconfig(self._label, fill=text)
        self.itemconfig(self._shape, outline=outline)
        if self._anim:
            self.after_cancel(self._anim)
            self._anim = None
        start = self.itemcget(self._shape, "fill")
        if not fade or start == fill:
            self.itemconfig(self._shape, fill=fill)
            return

        def step(i, steps=5):
            self.itemconfig(self._shape, fill=lerp_color(start, fill, i / steps))
            self._anim = self.after(12, lambda: step(i + 1)) if i < steps else None
        step(1)

    def _set_hover(self, on):
        self._hover = on
        self._paint(fade=True)

    def set_selected(self, flag):
        if not self.disabled and not self.has_event:
            self.selected = flag
            self._paint()


# ------------------------------------------------------------------ time slot ---
class SlotCell(tk.Canvas):
    H = 46
    HOVER = DayCell.HOVER

    def __init__(self, parent, hour, command, booked=False, past=False,
                 selected=False, fonts=None):
        self.disabled = booked or past
        super().__init__(parent, height=self.H, width=10, bg=WHITE,
                         highlightthickness=0,
                         cursor="arrow" if self.disabled else "hand2")
        self.hour, self.booked, self.selected = hour, booked, selected
        self._command, self._hover, self._fonts = command, False, fonts
        self._shape = None
        self.bind("<Configure>", lambda e: self._draw(e.width))
        if not self.disabled:
            self.bind("<Enter>", lambda e: self._set_hover(True))
            self.bind("<Leave>", lambda e: self._set_hover(False))
            self.bind("<ButtonRelease-1>", lambda e: self._command())

    def _colors(self):
        if self.disabled:
            return "#f1f5f9", "#e2e8f0", "#94a3b8"
        if self.selected:
            return BLUE, BLUE, WHITE
        if self._hover:
            return self.HOVER, self.HOVER, WHITE
        return WHITE, "#d1d5db", NAVY

    def _draw(self, w):
        if w < 20:
            return
        normal, strike, small = self._fonts
        fill, outline, text = self._colors()
        self.delete("all")
        self._shape = round_rect(self, 1, 1, w - 1, self.H - 1, 10, fill=fill,
                                 outline=outline)
        self._label = self.create_text(16, self.H / 2, anchor="w",
                                       text=slot_label(self.hour), fill=text,
                                       font=strike if self.booked else normal)
        if self.booked:
            self.create_text(w - 14, self.H / 2, anchor="e", text="Booked",
                             fill=text, font=small)

    def _paint(self):
        if self._shape is None:
            return
        fill, outline, text = self._colors()
        self.itemconfig(self._shape, fill=fill, outline=outline)
        self.itemconfig(self._label, fill=text)

    def _set_hover(self, on):
        self._hover = on
        self._paint()

    def set_selected(self, flag):
        if not self.disabled:
            self.selected = flag
            self._paint()


# ------------------------------------------------------------ form inputs ---
class LightEntry(RoundedEntry):
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


class LightSelect(tk.Canvas):
    def __init__(self, parent, options, width, height=42, radius=12, font=None,
                 value=None, parent_bg=WHITE):
        super().__init__(parent, width=width, height=height, bg=parent_bg,
                         highlightthickness=0, cursor="hand2")
        self.options = options
        self.value = value if value in options else options[0]
        self._box = round_rect(self, 1, 1, width - 1, height - 1, radius,
                               fill=WHITE, outline=LightEntry.LIGHT)
        self._text = self.create_text(16, height / 2, anchor="w",
                                      text=self.value, font=font, fill=NAVY)
        cy = height / 2
        self.create_line(width - 30, cy - 3, width - 24, cy + 3, width - 18,
                         cy - 3, fill=SLATE, width=2)
        self._menu = tk.Menu(self, tearoff=0, font=font, bg=WHITE, fg=NAVY,
                             activebackground=BLUE, activeforeground=WHITE,
                             bd=0, relief="flat")
        for option in options:
            self._menu.add_command(label=option,
                                   command=lambda o=option: self.set(o))
        self.bind("<Button-1>", self._open)

    def _open(self, _):
        self.itemconfig(self._box, outline=BLUE)
        try:
            self._menu.tk_popup(self.winfo_rootx(),
                                self.winfo_rooty() + self.winfo_height())
        finally:
            self._menu.grab_release()
            self.itemconfig(self._box, outline=LightEntry.LIGHT)

    def set(self, value):
        self.value = value
        self.itemconfig(self._text, text=value)

    def get(self):
        return self.value


# ------------------------------------------------------------ rounded pop-ups ---
class RoundedPopup(tk.Toplevel):
    KEY = "#010203"

    def __init__(self, app, width):
        super().__init__(app)
        self.withdraw()
        root = app
        while getattr(root, "master", None) is not None and \
              not hasattr(root, "family"):
            root = root.master
        self.app = root
        self.transient(app)
        self.resizable(False, False)
        self.rounded = False
        if sys.platform.startswith("win"):
            try:
                self.overrideredirect(True)
                self.wm_attributes("-transparentcolor", self.KEY)
                self.rounded = True
            except tk.TclError:
                self.overrideredirect(False)
        outer = self.KEY if self.rounded else WHITE
        self.configure(bg=outer)
        self.dw = min(width, app.winfo_screenwidth() - 40)
        self.fw = self.dw - 2 * 28 - 4
        self.card = Card(self, outer, border="#d1d5db", radius=22, pad=28)
        self.card.pack(fill="both", expand=True)
        self.body = self.card.inner
        self._fonts = []
        self._grabbed = False
        self.bind("<Escape>", lambda e: self.destroy())

    def F(self, size, bold=False):
        f = tkfont.Font(family=self.app.family, size=-size,
                        weight="bold" if bold else "normal")
        self._fonts.append(f)
        return f

    def divider(self, top, bottom):
        tk.Frame(self.body, bg="#e5e7eb", height=1).pack(fill="x",
                                                         pady=(top, bottom))

    def rows(self, pairs, key_font, val_font, bg=WHITE, parent=None):
        grid = tk.Frame(parent or self.body, bg=bg)
        grid.pack(fill="x")
        grid.grid_columnconfigure(1, weight=1)
        for i, (k, v) in enumerate(pairs):
            tk.Label(grid, text=k, font=key_font, fg=SLATE, bg=bg).grid(
                row=i, column=0, sticky="w", pady=5)
            tk.Label(grid, text=v, font=val_font, fg=NAVY, bg=bg,
                     justify="right",
                     wraplength=max(120, self.fw - 150)).grid(
                         row=i, column=1, sticky="e", pady=5, padx=(16, 0))
        return grid

    def show(self):
        self.update_idletasks()
        w, h = self.dw, self.card.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = clamp(self.app.winfo_rootx() + (self.app.winfo_width() - w) // 2,
                  0, max(0, sw - w))
        y = clamp(self.app.winfo_rooty() + (self.app.winfo_height() - h) // 2,
                  0, max(0, sh - h - 60))
        self.geometry(f"{w}x{h}+{x}+{y}")
        if self.rounded:
            for wd in [self.card._bgcanvas, self.body] + self._descendants(self.body):
                if isinstance(wd, (tk.Label, tk.Frame, tk.Canvas)) and \
                        not isinstance(wd, RoundedButton):
                    wd.bind("<ButtonPress-1>", self._drag_start, add="+")
                    wd.bind("<B1-Motion>", self._drag_move, add="+")
        self.deiconify()
        self.lift()
        self.focus_force()
        self.update_idletasks()
        try:
            self.grab_set()
            self._grabbed = True
        except tk.TclError:
            self.after(100, self._retry_grab)

    def _retry_grab(self):
        try:
            self.grab_set()
            self._grabbed = True
        except tk.TclError:
            pass

    def destroy(self):
        if getattr(self, "_grabbed", False):
            try:
                self.grab_release()
            except tk.TclError:
                pass
            self._grabbed = False
        try:
            super().destroy()
        except tk.TclError:
            pass
        try:
            self.app.focus_force()
        except tk.TclError:
            pass

    def _descendants(self, widget):
        out = []
        for child in widget.winfo_children():
            out.append(child)
            out.extend(self._descendants(child))
        return out

    def _drag_start(self, e):
        self._dx, self._dy = e.x_root - self.winfo_x(), e.y_root - self.winfo_y()

    def _drag_move(self, e):
        self.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")


class ConfirmReservationDialog(RoundedPopup):
    def __init__(self, app, booking, on_confirm, on_edit):
        super().__init__(app, 460)
        self.on_confirm, self.on_edit = on_confirm, on_edit
        f_title, f_text, f_val, f_btn = (self.F(24, True), self.F(14),
                                         self.F(14, True), self.F(14, True))

        tk.Label(self.body, text="Confirm Reservation?", font=f_title, fg=NAVY,
                 bg=WHITE).pack(anchor="w")
        tk.Label(self.body, font=f_text, fg=SLATE, bg=WHITE, justify="left",
                 wraplength=self.fw,
                 text="Your on-campus student pass will be issued immediately "
                      "upon confirmation. Please ensure your teammates arrive "
                      "on time.").pack(anchor="w", pady=(8, 0))
        self.divider(18, 12)
        self.rows((("Ground Name", booking["ground"]),
                   ("Selected Date", pretty_date(booking["date"])),
                   ("Booking Slot", booking["time"])), f_text, f_val)
        self.divider(12, 18)

        btns = tk.Frame(self.body, bg=WHITE)
        btns.pack(fill="x")
        btns.grid_columnconfigure(0, weight=1, uniform="b")
        btns.grid_columnconfigure(1, weight=1, uniform="b")
        WideButton(btns, "Edit Reservation", self._edit, height=46, radius=10,
                   bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                   font=f_btn).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        WideButton(btns, "Confirm Reservation", self._confirm, height=46,
                   radius=10, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                   font=f_btn).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.show()

    def _edit(self):
        self.destroy()
        self.on_edit()

    def _confirm(self):
        self.destroy()
        self.on_confirm()


# ------------------------------------------------------------------------ page ---
class ReservationPage(SectionPage):
    CW = 980

    def __init__(self, app):
        super().__init__(app, "reservation")

        def F(size, bold=False):
            return tkfont.Font(family=app.family, size=-size,
                               weight="bold" if bold else "normal")
        self.f.update({"h3": F(20, True), "cap": F(11, True), "err": F(11),
                       "val": F(13, True)})
        self.slot_fonts = (F(14),
                           tkfont.Font(family=app.family, size=-14,
                                       overstrike=True),
                           F(11, True))

        self.step = 1
        self.selected = None
        self.selected_date = None
        self.selected_time = None
        self.view = None
        self.booking = {}
        self.info = {}
        self.receipt = None
        self._cards = {}
        self.cal_wrap = None
        self.block_w = CAL_W
        self._curw = 1200

        self._highlight_nav()
        self._shell()
        self._footer()
        self._render()

    def on_show(self, ground=None, **kwargs):
        super().on_show(**kwargs)
        self.step, self.booking, self.info = 1, {}, {}
        self.selected_date, self.selected_time, self.view = None, None, None
        self.selected = ground if ground in [g[0] for g in GROUNDS] else None
        self._render()

    def _highlight_nav(self):
        for cell in self.links.winfo_children():
            lb, underline = cell.winfo_children()[0], cell.winfo_children()[1]
            if lb.cget("text") == "Reservation":
                lb.config(font=self.f["label_bold"], fg=BLUE)
                underline.config(bg=BLUE)
                lb.unbind("<Enter>")
                lb.unbind("<Leave>")
                lb.bind("<Button-1>", lambda e: self._nav_reservation())

    def _nav_reservation(self):
        if self.step == 6:
            self.on_show()
        else:
            self.scroll.canvas.yview_moveto(0)

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

    def _build_header(self, review):
        for w in self.head.winfo_children():
            w.destroy()
        if review:
            tk.Label(self.head, text="FINAL STEP", font=self.f["tag"], fg=BLUE,
                     bg=SOFT_BG).pack()
            tk.Label(self.head, text="Reservation Summary", font=self.f["h1"],
                     fg=NAVY, bg=SOFT_BG).pack(pady=(8, 0))
        else:
            Pill(self.head, "CAMPUS RECREATION PORTAL", self.app.f_badge,
                 BLUE, BLUE_SOFT, parent_bg=SOFT_BG).pack()
            tk.Label(self.head, text="Reserve Your Ground", font=self.f["h1"],
                     fg=NAVY, bg=SOFT_BG).pack(pady=(10, 0))
            tk.Label(self.head, font=self.f["p"], fg=SLATE, bg=SOFT_BG,
                     text="Choose a ground, date, time, and provide your "
                          "booking information.").pack(pady=(8, 0))

    def _render(self):
        for w in self.content.winfo_children():
            w.destroy()
        self.cal_wrap = None
        self.block_w = CAL_W
        self._reflows = [r for r in self._reflows if r["c"].winfo_exists()]
        done = self.step == 6
        if done:
            for w in self.head.winfo_children():
                w.destroy()
            self.head.pack_forget()
        else:
            self.head.pack(fill="x", before=self.content)
            self._build_header(review=self.step == 5)
            self._stepper()
        self.panel = tk.Frame(self.content, bg=SOFT_BG)
        self.panel.pack(fill="x", pady=(0 if done else 28, 0))
        {1: self._step_ground, 2: self._step_date, 3: self._step_time,
         4: self._step_info, 5: self._step_summary,
         6: self._step_done}[self.step]()
        self.scroll.canvas.yview_moveto(0)

    def _stepper(self):
        review = self.step == 5
        labels = REVIEW_LABELS if review else STEP_LABELS
        cur = 4 if review else self.step
        accent = GREEN if review else BLUE
        card = Card(self.content, SOFT_BG, pad=14, border="#e5e7eb")
        card.pack(fill="x")
        row = tk.Frame(card.inner, bg=WHITE)
        row.pack()
        for i, label in enumerate(labels, start=1):
            if i > 1:
                tk.Frame(row, bg=accent if i <= cur else "#d1d5db", height=1,
                         width=50).pack(side="left", padx=10)
            active, done = i == cur, i < cur
            cv = tk.Canvas(row, width=26, height=26, bg=WHITE,
                           highlightthickness=0)
            cv.create_oval(1, 1, 25, 25,
                           fill=BLUE if active else (accent if done else WHITE),
                           outline=BLUE if active else (accent if done else "#d1d5db"))
            cv.create_text(13, 13, text="✓" if done else str(i),
                           font=self.f["btn"],
                           fill=WHITE if (active or done) else SLATE)
            cv.pack(side="left")
            tk.Label(row, text=label, bg=WHITE,
                     font=self.f["label_bold"] if active else self.f["label"],
                     fg=BLUE if active else ("#334155" if done else SLATE)
                     ).pack(side="left", padx=(8, 0))

    def _step_ground(self):
        tk.Label(self.panel, text="Select a Ground", font=self.f["h3"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")
        holder = tk.Frame(self.panel, bg=SOFT_BG)
        holder.pack(fill="x", pady=(18, 0))

        self._cards, cards = {}, []
        reservations = getattr(self.app, "reservations", [])
        for name, cap, img in GROUNDS:
            status = ground_status(name, reservations)
            scolor, stint = STATUS_STYLE[status]
            sel = name == self.selected
            c = Card(holder, SOFT_BG, pad=12, border=BLUE if sel else "#e5e7eb")
            PhotoBox(c.inner, image_or(RESERVE_IMAGES.get(name, img), img),
                     150, radius=10).pack(fill="x")
            tk.Label(c.inner, text=name, font=self.f["card_t"], fg=NAVY,
                     bg=WHITE).pack(anchor="w", pady=(10, 0))
            cap_row = tk.Frame(c.inner, bg=WHITE)
            cap_row.pack(anchor="w", pady=(2, 10))
            tk.Label(cap_row, text="👥", font=self.f["small"], fg=SLATE,
                     bg=WHITE).pack(side="left")
            tk.Label(cap_row, text=cap, font=self.f["small"], fg=SLATE,
                     bg=WHITE).pack(side="left", padx=(6, 0))
            row = tk.Frame(c.inner, bg=WHITE)
            row.pack(fill="x")
            Pill(row, f"●  {status}", self.app.f_badge, scolor, stint,
                 padx=10, pady=5).pack(side="left")
            
            # Disable selection if there is an event TODAY
            btn = RoundedButton(row, "Select", lambda n=name: self._choose(n),
                                100, 32, radius=8, bg=WHITE, hover=BLUE_SOFT,
                                fg=BLUE, outline=BLUE, font=self.f["btn"])
            btn.pack(side="right")
            if sel and status != "Event":
                self._style_btn(btn, True)
                
            self._cards[name] = (c, btn)
            cards.append(c)
        self.reflow(holder, cards, lambda w: 2 if w >= 760 else 1)

        bar = tk.Frame(self.panel, bg=SOFT_BG)
        bar.pack(fill="x", pady=(22, 0))
        self.msg = tk.Label(bar, text="", font=self.f["small"], fg="#dc2626",
                            bg=SOFT_BG)
        self.msg.pack(side="left", padx=8)
        RoundedButton(bar, "Next Step", self._next, 120, 40, radius=8, bg=BLUE,
                      hover=BLUE_DARK, fg=WHITE, font=self.f["btn"],
                      parent_bg=SOFT_BG).pack(side="right", padx=8)

    def _style_btn(self, btn, selected):
        if btn._anim:
            btn.after_cancel(btn._anim)
            btn._anim = None
        btn._bg = BLUE if selected else WHITE
        btn._hover = BLUE_DARK if selected else BLUE_SOFT
        btn.itemconfig(btn._shape, fill=btn._bg, outline=BLUE)
        btn.itemconfig(btn._text_id,
                       text="Selected" if selected else "Select",
                       fill=WHITE if selected else BLUE)

    def _choose(self, name):
        # Check if there is an event today
        if get_event_block(name, datetime.date.today()):
            PlayZoneDialog(self.winfo_toplevel(), "Event Today", 
                           f"The {name} is currently hosting a college event and cannot be booked today.", 
                           type="warning")
            return
            
        self.selected = name
        self.msg.config(text="")
        for n, (card, btn) in self._cards.items():
            card.border = BLUE if n == name else "#e5e7eb"
            card.redraw()
            self._style_btn(btn, n == name)

    def _step_date(self):
        today = datetime.date.today()
        if self.view is None:
            base = self.selected_date or today
            self.view = (base.year, base.month)

        wrap = tk.Frame(self.panel, bg=SOFT_BG)
        wrap.pack(fill="x")
        self.cal_wrap = wrap
        tk.Label(wrap, text="Choose a Date", font=self.f["h3"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")

        card = Card(wrap, SOFT_BG, pad=24, border="#e5e7eb")
        card.pack(fill="x", pady=(18, 0))
        head = tk.Frame(card.inner, bg=WHITE)
        head.pack(fill="x")
        self.month_lbl = tk.Label(head, text="", font=self.f["card_t"],
                                  fg=NAVY, bg=WHITE)
        self.month_lbl.pack(side="left")
        nav = tk.Frame(head, bg=WHITE)
        nav.pack(side="right")
        self.prev_btn, self.next_btn = [
            RoundedButton(nav, glyph, (lambda d=delta: self._shift(d)), 30, 30,
                          radius=8, bg=WHITE, hover=BLUE_SOFT, fg=NAVY,
                          outline="#d1d5db", font=self.f["card_t"])
            for glyph, delta in (("‹", -1), ("›", 1))]
        self.prev_btn.pack(side="left")
        self.next_btn.pack(side="left", padx=(8, 0))
        self.days_holder = tk.Frame(card.inner, bg=WHITE)
        self.days_holder.pack(fill="x", pady=(18, 0))
        self._show_month()

        bar = tk.Frame(self.panel, bg=SOFT_BG)
        bar.pack(fill="x", pady=(22, 0))
        self.msg = tk.Label(bar, text="", font=self.f["small"], fg="#dc2626",
                            bg=SOFT_BG)
        self.msg.pack(side="left", padx=8)
        RoundedButton(bar, "Next Step", self._next, 120, 40, radius=8, bg=BLUE,
                      hover=BLUE_DARK, fg=WHITE, font=self.f["btn"],
                      parent_bg=SOFT_BG).pack(side="right", padx=8)
        RoundedButton(bar, "Back", self._back, 100, 40, radius=8, bg=WHITE,
                      hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                      font=self.f["btn"], parent_bg=SOFT_BG).pack(side="right")
        self._center_cal()

    @staticmethod
    def _month_index(year, month):
        return year * 12 + month - 1

    def _show_month(self):
        today = datetime.date.today()
        year, month = self.view
        idx = self._month_index(year, month)
        today_idx = self._month_index(today.year, today.month)
        self.month_lbl.config(text=f"{calendar.month_name[month]} {year}")
        for btn, enabled in ((self.prev_btn, idx > today_idx),
                             (self.next_btn, idx < today_idx + MAX_MONTHS_AHEAD)):
            self._style_nav(btn, enabled)

        for w in self.days_holder.winfo_children():
            w.destroy()
        for c in range(7):
            self.days_holder.grid_columnconfigure(c, weight=1, uniform="day")
        for c, name in enumerate(WEEKDAYS):
            tk.Label(self.days_holder, text=name, font=self.f["cap"],
                     fg="#334155", bg=WHITE).grid(row=0, column=c, pady=(0, 6))
        self.cells = {}
        for r, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for c, day in enumerate(week):
                if not day:
                    continue
                d = datetime.date(year, month, day)
                
                # Check if an event is happening on this date for this ground
                has_event = get_event_block(self.booking.get("ground"), d) is not None
                
                cell = DayCell(self.days_holder, day,
                               (lambda dt=d: self._pick(dt)),
                               disabled=d < today, today=d == today,
                               selected=d == self.selected_date,
                               font=self.f["label"], has_event=has_event)
                cell.grid(row=r, column=c, pady=4)
                self.cells[d] = cell

    def _style_nav(self, btn, enabled):
        if btn._anim:
            btn.after_cancel(btn._anim)
            btn._anim = None
        btn._enabled = enabled
        btn._bg = WHITE
        btn._hover = BLUE_SOFT if enabled else WHITE
        btn.itemconfig(btn._shape, fill=WHITE)
        btn.itemconfig(btn._text_id, fill=NAVY if enabled else "#cbd5e1")
        btn.config(cursor="hand2" if enabled else "arrow")

    def _shift(self, delta):
        btn = self.prev_btn if delta < 0 else self.next_btn
        if not getattr(btn, "_enabled", True):
            return
        year, month = self.view
        idx = self._month_index(year, month) + delta
        self.view = (idx // 12, idx % 12 + 1)
        self._show_month()

    def _pick(self, d):
        # Verify again just in case
        if get_event_block(self.booking.get("ground"), d):
            PlayZoneDialog(self.winfo_toplevel(), "Event Scheduled", 
                           "This date is unavailable because a college event is taking place.", 
                           type="warning")
            return
            
        self.selected_date = d
        self.msg.config(text="")
        for dt, cell in self.cells.items():
            cell.set_selected(dt == d)

    def _step_time(self):
        today, now = datetime.date.today(), datetime.datetime.now()
        ground, date = self.booking["ground"], self.booking["date"]
        taken = booked_slots(ground, date, getattr(self.app, "reservations", []))
        hours = list(range(*ground_hours(ground)))
        past = {h for h in hours if date == today and h <= now.hour}
        if self.selected_time in taken or self.selected_time in past:
            self.selected_time = None

        wrap = tk.Frame(self.panel, bg=SOFT_BG)
        wrap.pack(fill="x")
        self.cal_wrap = wrap
        tk.Label(wrap, text="Choose a Time", font=self.f["h3"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")
        tk.Label(wrap, text=f"{ground}  •  {pretty_date(date)}",
                 font=self.f["p"], fg=SLATE, bg=SOFT_BG).pack(anchor="w",
                                                              pady=(4, 0))

        card = Card(wrap, SOFT_BG, pad=24, border="#e5e7eb")
        card.pack(fill="x", pady=(18, 0))

        legend = tk.Frame(card.inner, bg=WHITE)
        legend.pack(anchor="w")
        for fill, border, text in ((WHITE, "#d1d5db", "Available"),
                                   (BLUE, BLUE, "Selected"),
                                   ("#f1f5f9", "#e2e8f0", "Booked / passed")):
            sw = tk.Canvas(legend, width=16, height=16, bg=WHITE,
                           highlightthickness=0)
            round_rect(sw, 1, 1, 15, 15, 4, fill=fill, outline=border)
            sw.pack(side="left")
            tk.Label(legend, text=text, font=self.f["small"], fg=SLATE,
                     bg=WHITE).pack(side="left", padx=(6, 18))

        self.slot_cells = []
        groups = (("MORNING", [h for h in hours if h < 12]),
                  ("AFTERNOON", [h for h in hours if 12 <= h < 16]),
                  ("EVENING", [h for h in hours if h >= 16]))
        for title, hs in groups:
            if not hs:
                continue
            tk.Label(card.inner, text=title, font=self.f["cap"], fg="#334155",
                     bg=WHITE).pack(anchor="w", pady=(20, 8))
            grid = tk.Frame(card.inner, bg=WHITE)
            grid.pack(fill="x")
            for c in range(2):
                grid.grid_columnconfigure(c, weight=1, uniform="slot")
            for i, h in enumerate(hs):
                cell = SlotCell(grid, h, (lambda hh=h: self._pick_time(hh)),
                                booked=h in taken, past=h in past,
                                selected=h == self.selected_time,
                                fonts=self.slot_fonts)
                cell.grid(row=i // 2, column=i % 2, sticky="ew",
                          padx=(0, 6) if i % 2 == 0 else (6, 0), pady=5)
                self.slot_cells.append(cell)

        if all(c.disabled for c in self.slot_cells):
            tk.Label(card.inner, font=self.f["small"], fg="#dc2626", bg=WHITE,
                     text="No time slots are available on this date. "
                          "Please go back and choose another date.").pack(
                              anchor="w", pady=(14, 0))

        bar = tk.Frame(self.panel, bg=SOFT_BG)
        bar.pack(fill="x", pady=(22, 0))
        self.msg = tk.Label(bar, text="", font=self.f["small"], fg="#dc2626",
                            bg=SOFT_BG)
        self.msg.pack(side="left", padx=8)
        RoundedButton(bar, "Next Step", self._next, 120, 40, radius=8, bg=BLUE,
                      hover=BLUE_DARK, fg=WHITE, font=self.f["btn"],
                      parent_bg=SOFT_BG).pack(side="right", padx=8)
        RoundedButton(bar, "Back", self._back, 100, 40, radius=8, bg=WHITE,
                      hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                      font=self.f["btn"], parent_bg=SOFT_BG).pack(side="right")
        self._center_cal()

    def _pick_time(self, hour):
        # Re-verify this slot is still free (someone may have booked it)
        try:
            taken = booked_slots(self.booking["ground"], self.booking["date"],
                                 getattr(self.app, "reservations", []))
        except Exception as exc:
            print("[reservation] _pick_time check failed:", exc)
            taken = set()

        if hour in taken:
            self.msg.config(text="That slot was just booked. Please pick another.")
            for cell in self.slot_cells:
                if cell.hour == hour and not cell.disabled:
                    cell.disabled = True
                    cell.booked = True
                    cell.config(cursor="arrow")
                    cell._paint()
            self.selected_time = None
            return

        self.selected_time = hour
        self.msg.config(text="")
        for cell in self.slot_cells:
            cell.set_selected(cell.hour == hour)

    def _step_info(self):
        wrap = tk.Frame(self.panel, bg=SOFT_BG)
        wrap.pack(fill="x")
        self.cal_wrap = wrap
        tk.Label(wrap, text="Your Information", font=self.f["h3"], fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")

        card = Card(wrap, SOFT_BG, pad=28, border="#e5e7eb")
        card.pack(fill="x", pady=(18, 0))
        inner, fw = card.inner, CAL_W - 2 * 28 - 4

        self.inputs, self.errors = {}, {}
        for i, (key, label, placeholder) in enumerate(INFO_FIELDS):
            tk.Label(inner, text=label, font=self.f["btn"], fg=NAVY,
                     bg=WHITE).pack(anchor="w", pady=(0 if i == 0 else 8, 6))
            entry = LightEntry(inner, placeholder, width=fw, height=42,
                               font=self.f["small"])
            entry.pack(anchor="w")
            if self.info.get(key):
                entry.var.set(self.info[key])
            err = tk.Label(inner, text="", font=self.f["err"], fg="#dc2626",
                           bg=WHITE, anchor="w", justify="left")
            err.pack(fill="x", padx=4, pady=(2, 0))
            self.inputs[key], self.errors[key] = entry, err

        tk.Label(inner, text="Purpose of Reservation", font=self.f["btn"],
                 fg=NAVY, bg=WHITE).pack(anchor="w", pady=(8, 6))
        self.purpose = LightSelect(inner, PURPOSES, fw, height=42,
                                   font=self.f["small"],
                                   value=self.info.get("purpose"))
        self.purpose.pack(anchor="w")

        bar = tk.Frame(self.panel, bg=SOFT_BG)
        bar.pack(fill="x", pady=(22, 0))
        RoundedButton(bar, "Review Reservation", self._next, 160, 40, radius=8,
                      bg=BLUE, hover=BLUE_DARK, fg=WHITE, font=self.f["btn"],
                      parent_bg=SOFT_BG).pack(side="right", padx=8)
        RoundedButton(bar, "Back", self._back, 100, 40, radius=8, bg=WHITE,
                      hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                      font=self.f["btn"], parent_bg=SOFT_BG).pack(side="right")
        self._center_cal()

    def _save_info(self):
        self.info = {k: e.get() for k, e in self.inputs.items()}
        self.info["purpose"] = self.purpose.get()

    def _check(self, key, message, ok):
        if ok:
            self.inputs[key].clear_error()
            self.errors[key].config(text="")
        else:
            self.inputs[key].set_error()
            self.errors[key].config(text=message)
        return ok

    def _review(self):
        self._save_info()
        v, ok = self.info, True
        ok &= self._check("name", "Please enter your full name.", bool(v["name"]))
        if not v["student_id"]:
            ok &= self._check("student_id", "Please enter your student ID.", False)
        else:
            ok &= self._check("student_id",
                              "Student ID can only contain letters and numbers.",
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
        if not ok:
            return
        self.booking["info"] = dict(v)
        self.step = 5
        self._render()

    def _step_summary(self):
        self.block_w = SUM_W
        b = self.booking
        wrap = tk.Frame(self.panel, bg=SOFT_BG)
        wrap.pack(fill="x")
        self.cal_wrap = wrap
        card = Card(wrap, SOFT_BG, pad=28, border="#e5e7eb")
        card.pack(fill="x")
        inner = card.inner

        tk.Label(inner, text="Verify Your Selection", font=self.f["card_t"],
                 fg=NAVY, bg=WHITE).pack(anchor="w")
        tk.Frame(inner, bg="#e5e7eb", height=1).pack(fill="x", pady=(16, 8))
        for glyph, cap, value in (("▦", "GROUND RESERVED", b["ground"]),
                                  ("🗓", "RESERVATION DATE",
                                   pretty_date(b["date"])),
                                  ("🕓", "TIME SLOT REQUESTED", b["time"]),
                                  ("🏆", "BOOKING PURPOSE",
                                   b["info"]["purpose"])):
            row = tk.Frame(inner, bg=WHITE)
            row.pack(fill="x", pady=8)
            ic = tk.Canvas(row, width=36, height=36, bg=WHITE,
                           highlightthickness=0)
            round_rect(ic, 0, 0, 36, 36, 10, fill=BLUE_HOVER,
                       outline=BLUE_HOVER)
            ic.create_text(18, 18, text=glyph, fill=BLUE, font=self.f["small"])
            ic.pack(side="left", anchor="n")
            txt = tk.Frame(row, bg=WHITE)
            txt.pack(side="left", padx=(14, 0))
            tk.Label(txt, text=cap, font=self.f["cap"], fg=SLATE,
                     bg=WHITE).pack(anchor="w")
            tk.Label(txt, text=value, font=self.f["label_bold"], fg=NAVY,
                     bg=WHITE, justify="left").pack(anchor="w", pady=(2, 0))
        tk.Frame(inner, bg="#e5e7eb", height=1).pack(fill="x", pady=(10, 18))

        btns = tk.Frame(inner, bg=WHITE)
        btns.pack(fill="x")
        btns.grid_columnconfigure(0, weight=1, uniform="b")
        btns.grid_columnconfigure(1, weight=1, uniform="b")
        WideButton(btns, "Back", self._back, height=44, radius=8, bg=WHITE,
                   hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                   font=self.f["btn"]).grid(row=0, column=0, sticky="ew",
                                            padx=(0, 6))
        WideButton(btns, "Confirm Reservation", self._open_confirm, height=44,
                   radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                   font=self.f["btn"]).grid(row=0, column=1, sticky="ew",
                                            padx=(6, 0))
        self._center_cal()

    def _open_confirm(self):
        ConfirmReservationDialog(self.app, self.booking,
                                 on_confirm=self._finalize,
                                 on_edit=self._edit_all)

    def _edit_all(self):
        self.step = 1
        self._render()

    def _finalize(self):
        b = self.booking
        info = b.get("info", {})
        if not info:
            PlayZoneDialog(self.winfo_toplevel(), "Missing details", "Your information was lost. Please re-enter it.", type="error")
            self.step = 4
            self._render()
            return
        if not all(k in b for k in ("ground", "date", "time", "start", "end")):
            PlayZoneDialog(self.winfo_toplevel(), "Incomplete booking", "The booking is missing a ground, date, or time.", type="error")
            self.step = 1
            self._render()
            return

        if not hasattr(self.app, "reservations"):
            self.app.reservations = []

        # --- 1. Re-check availability against the DB (authoritative) ---
        try:
            taken = booked_slots(b["ground"], b["date"], self.app.reservations)
        except Exception as exc:
            print("[reservation] availability check failed:", exc)
            PlayZoneDialog(self.winfo_toplevel(), "Cannot verify slot", "We couldn't check availability right now. Please try again.", type="error")
            return

        if b["start"].hour in taken:
            PlayZoneDialog(self.winfo_toplevel(), "Time slot unavailable", "Sorry, that slot has just been booked or a college event has started. Please pick another time.", type="warning")
            self.selected_time = None
            self.step = 3
            self._render()
            return

        # --- 2. Build the record ---
        try:
            k = sum(1 for r in self.app.reservations
                    if r.get("date") == b["date"]) + 1
            record = dict(
                info,
                id=f"PZ-{b['date']:%Y-%m%d}-{k:03d}",
                ground=b["ground"], date=b["date"], time=b["time"],
                start=b["start"], end=b["end"], status="Pending",
            )
        except Exception as exc:
            print("[reservation] could not build record:", exc)
            PlayZoneDialog(self.winfo_toplevel(), "Booking error", f"Could not create booking: {exc}", type="error")
            return

        # --- 3. Save to DB (unique index protects against races) ---
        saved = False
        try:
            from db import get_conn
            conn = get_conn()
            if conn is not None:
                try:
                    conn.execute(
                        "INSERT INTO bookings "
                        "(id, name, student_id, email, phone, purpose, ground, "
                        " date, start_time, end_time, time_label, status) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (record["id"], record["name"], record["student_id"],
                         record["email"], record["phone"], record["purpose"],
                         record["ground"], record["date"].isoformat(),
                         record["start"].strftime("%H:%M"),
                         record["end"].strftime("%H:%M"),
                         record["time"], record["status"]))
                    conn.execute(
                        "UPDATE users SET bookings = bookings + 1 "
                        "WHERE email = ?", (record["email"],))
                    conn.commit()
                    saved = True
                except Exception as exc:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    low = str(exc).lower()
                    if "unique" in low or "constraint" in low:
                        PlayZoneDialog(self.winfo_toplevel(), "Time slot taken", "Someone else just booked that slot. Please choose another time.", type="warning")
                        self.selected_time = None
                        self.step = 3
                        self._render()
                        return
                    print("[reservation] DB insert failed:", exc)
            else:
                print("[reservation] DB unavailable, using memory only")
        except Exception as exc:
            print("[reservation] DB layer error:", exc)

        # --- 4. Mirror into memory ---
        self.app.reservations.append(record)
        print(f"[reservation] {record} ({'db' if saved else 'memory'})")
        self.app._notif_unread = 1
        self.receipt = record
        self.booking, self.info = {}, {}
        self.selected = self.selected_date = self.selected_time = self.view = None
        self.step = 6
        self._render()

    def _step_done(self):
        self.block_w = DONE_W
        r = self.receipt
        wrap = tk.Frame(self.panel, bg=SOFT_BG)
        wrap.pack(fill="x")
        self.cal_wrap = wrap

        ic = tk.Canvas(wrap, width=76, height=76, bg=SOFT_BG,
                       highlightthickness=0)
        ic.create_oval(2, 2, 74, 74, fill="#dcfce7", outline="#dcfce7")
        ic.create_line(25, 39, 34, 48, 52, 28, fill=GREEN, width=3,
                       capstyle="round", joinstyle="round")
        ic.pack(pady=(10, 0))
        tk.Label(wrap, text="Reservation Confirmed!", font=self.f["h2"],
                 fg=NAVY, bg=SOFT_BG).pack(pady=(18, 0))
        tk.Label(wrap, font=self.f["label"], fg=SLATE, bg=SOFT_BG,
                 justify="center", wraplength=DONE_W - 20,
                 text="Your college ground has been successfully reserved. "
                      "A digital permit and instructions have been emailed to "
                      "your university account.").pack(pady=(10, 0))

        card = Card(wrap, SOFT_BG, pad=24, border="#e5e7eb")
        card.pack(fill="x", pady=(28, 0))
        inner = card.inner
        top = tk.Frame(inner, bg=WHITE)
        top.pack(fill="x")
        tk.Label(top, text="RECEIPT DETAILS", font=self.f["cap"], fg="#475569",
                 bg=WHITE).pack(side="left")
        Pill(top, "Confirmed", self.app.f_badge, GREEN_DARK, "#dcfce7",
             padx=10, pady=4).pack(side="right")
        tk.Frame(inner, bg="#e5e7eb", height=1).pack(fill="x", pady=(16, 10))

        grid = tk.Frame(inner, bg=WHITE)
        grid.pack(fill="x")
        grid.grid_columnconfigure(1, weight=1)
        for i, (k, v) in enumerate((("Reservation ID", r["id"]),
                                    ("Facility Reserved", r["ground"]),
                                    ("Reserved Date", pretty_date(r["date"])),
                                    ("Time Slot allotted", r["time"]))):
            tk.Label(grid, text=k, font=self.f["small"], fg=SLATE,
                     bg=WHITE).grid(row=i, column=0, sticky="w", pady=6)
            tk.Label(grid, text=v, font=self.f["val"], fg=NAVY,
                     bg=WHITE).grid(row=i, column=1, sticky="e", pady=6)
        tk.Frame(inner, bg="#e5e7eb", height=1).pack(fill="x", pady=(10, 18))
        WideButton(inner, "Back to Home",
                   lambda: self.app.navigate("home"), height=44, radius=8,
                   bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                   font=self.f["btn"]).pack(fill="x")
        self._center_cal()

    def _next(self):
        if self.step == 1:
            if not self.selected:
                self.msg.config(text="Please select a ground to continue.")
                return
            if self.booking.get("ground") != self.selected:
                self.selected_time = None
            self.booking["ground"] = self.selected
        elif self.step == 2:
            if not self.selected_date:
                self.msg.config(text="Please select a date to continue.")
                return
            if self.booking.get("date") != self.selected_date:
                self.selected_time = None
            self.booking["date"] = self.selected_date
        elif self.step == 3:
            if self.selected_time is None:
                self.msg.config(text="Please select a time slot to continue.")
                return
            h = self.selected_time
            self.booking.update(time=slot_label(h), start=datetime.time(h),
                                end=datetime.time(h + 1))
        elif self.step == 4:
            self._review()
            return
        if self.step < len(STEP_LABELS):
            self.step += 1
            self._render()

    def _back(self):
        if self.step == 4:
            self._save_info()
        if self.step > 1:
            self.step -= 1
            self._render()

    def _apply(self, w):
        super()._apply(w)
        self._curw = w
        if hasattr(self, "content"):
            side = max(24, (w - self.MAXW) // 2)
            self.content.pack_configure(
                padx=max(0, (w - 2 * side - self.CW) // 2))
            self._center_cal()

    def _center_cal(self):
        if self.cal_wrap is None or not self.cal_wrap.winfo_exists():
            return
        side = max(24, (self._curw - self.MAXW) // 2)
        content_w = min(self._curw - 2 * side, self.CW)
        self.cal_wrap.pack_configure(
            padx=max(0, (content_w - self.block_w) // 2))

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