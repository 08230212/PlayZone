"""admin_event.py - admin Events screen + Add Event form."""
import calendar
import datetime
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

from common import *
from data import event_date
from reservation import RoundedPopup
from admin_shell import AdminPage, PAGE_BG
from admin_data import (all_events, add_event, delete_event,
                        approve_event, reject_event)


ADMIN_STATUS = {
    "Approved": ("#059669", "#dcfce7"),
    "Pending":  ("#d97706", "#fef3c7"),
    "Rejected": ("#dc2626", "#fee2e2"),
}

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

TIME_SLOTS = [
    "08:00 AM – 10:00 AM",
    "10:00 AM – 12:00 PM",
    "12:00 PM – 02:00 PM",
    "02:00 PM – 04:00 PM",
    "04:00 PM – 06:00 PM",
    "06:00 PM – 08:00 PM",
]


# ============================================================== the page ====
class EventPage(AdminPage):
    def build(self):
        self.body = tk.Frame(self, bg=PAGE_BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=24)
        self._header()
        self._grid_holder = tk.Frame(self.body, bg=PAGE_BG)
        self._grid_holder.pack(fill="both", expand=True)
        self._render_grid()

    def on_show(self, **kwargs):
        if getattr(self, "_built", False):
            self._render_grid()

    def _header(self):
        head = tk.Frame(self.body, bg=PAGE_BG)
        head.pack(fill="x", pady=(0, 16))
        head.grid_columnconfigure(0, weight=1)
        tk.Label(head, text="Events", font=self.f["h1"], fg=NAVY,
                 bg=PAGE_BG).grid(row=0, column=0, sticky="w")
        RoundedButton(head, "＋  Add New Event",
                      lambda: AddEventDialog(self), 170, 40, radius=8,
                      bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                      font=self.f["btn"], parent_bg=PAGE_BG
                      ).grid(row=0, column=1, sticky="e")

    def _render_grid(self):
        for w in self._grid_holder.winfo_children():
            w.destroy()
        events = sorted(all_events(self.app.events), key=event_date)
        self._event_cards = []
        self._last_cols = None
        if not events:
            tk.Label(self._grid_holder, text="No events yet.",
                     font=self.f["p"], fg=SLATE,
                     bg=PAGE_BG).pack(pady=40)
            return
        for ev in events:
            card = self._event_card(self._grid_holder, ev)
            self._event_cards.append(card)
        self.on_reflow(self.winfo_width())
        self.after(0, lambda: self.on_reflow(self._grid_holder.winfo_width()))

    def _event_card(self, parent, ev):
        c = Card(parent, PAGE_BG, pad=0, border="#e5e7eb")
        PhotoBox(c.inner, ev.get("image", "indoor.jpg"), 170,
                 radius=0).pack(fill="x")

        meta = tk.Frame(c.inner, bg=WHITE)
        meta.pack(fill="x", padx=16, pady=(12, 4))
        status = ev.get("admin_status", "Approved")
        fg, bg = ADMIN_STATUS.get(status, (SLATE, "#f1f5f9"))
        Pill(meta, status, self.f["small"], fg, bg, parent_bg=WHITE,
             padx=10, pady=3).pack(side="left")
        trash = _TrashIcon(meta, command=lambda ev=ev: self._delete(ev))
        trash.pack(side="right")

        tk.Label(c.inner, text=ev["title"], font=self.f["h3"], fg=NAVY,
                 bg=WHITE, anchor="w", justify="left",
                 wraplength=420).pack(anchor="w", padx=16, pady=(6, 4))
        tk.Label(c.inner, text=f"{ev['date']}  |  {ev['time']}",
                 font=self.f["small"], fg=SLATE, bg=WHITE,
                 anchor="w").pack(anchor="w", padx=16)
        tk.Label(c.inner, text=ev["location"], font=self.f["small"],
                 fg=BLUE, bg=WHITE, anchor="w").pack(anchor="w",
                                                     padx=16, pady=(2, 4))
        tk.Label(c.inner,
                 text=ev.get("description",
                             "A campus event designed to encourage teamwork "
                             "and healthy competition."),
                 font=self.f["small"], fg=SLATE, bg=WHITE, anchor="w",
                 justify="left", wraplength=420).pack(anchor="w", padx=16,
                                                      pady=(0, 14))

        if status == "Pending":
            actions = tk.Frame(c.inner, bg=WHITE)
            actions.pack(fill="x", padx=16, pady=(0, 16))
            actions.grid_columnconfigure(0, weight=1, uniform="act")
            actions.grid_columnconfigure(1, weight=1, uniform="act")
            WideButton(actions, "Approve", lambda e=ev: self._approve(e),
                       height=36, radius=8, bg=GREEN, hover="#0e9f6e",
                       fg=WHITE, font=self.f["btn"]
                       ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
            WideButton(actions, "Reject", lambda e=ev: self._reject(e),
                       height=36, radius=8, bg=WHITE, hover="#fee2e2",
                       fg="#dc2626", outline="#dc2626",
                       font=self.f["btn"]
                       ).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        elif status == "Rejected":
            actions = tk.Frame(c.inner, bg=WHITE)
            actions.pack(fill="x", padx=16, pady=(0, 16))
            WideButton(actions, "Approve", lambda e=ev: self._approve(e),
                       height=36, radius=8, bg=GREEN, hover="#0e9f6e",
                       fg=WHITE, font=self.f["btn"]).pack(fill="x")

        return c

    def _approve(self, ev):
        approve_event(self.app.events, ev["title"])
        self._render_grid()

    def _reject(self, ev):
        reject_event(self.app.events, ev["title"])
        self._render_grid()

    def _delete(self, ev):
        if not messagebox.askyesno("Delete event",
                                   f"Delete \"{ev['title']}\"?"):
            return
        delete_event(self.app.events, ev["title"])
        self._render_grid()

    def on_reflow(self, w):
        if not getattr(self, "_event_cards", None):
            return
        holder = self._grid_holder
        avail = holder.winfo_width()
        if avail < 50:
            avail = w or 1200
        cols = 2 if avail >= 820 else 1
        if getattr(self, "_last_cols", None) == cols:
            return
        self._last_cols = cols
        for i in range(4):
            holder.grid_columnconfigure(i, weight=0, uniform="")
        for i in range(cols):
            holder.grid_columnconfigure(i, weight=1, uniform="ev")
        for i, card in enumerate(self._event_cards):
            card.grid_configure(row=i // cols, column=i % cols,
                                sticky="nsew", padx=8, pady=8)


# ========================================================== trash icon =====
class _TrashIcon(tk.Canvas):
    def __init__(self, parent, command, size=16, bg=WHITE,
                 color="#ef4444", hover="#dc2626"):
        super().__init__(parent, width=size + 6, height=size + 6, bg=bg,
                         highlightthickness=0, cursor="hand2")
        self._command = command
        self._color = color
        self._hover = hover
        self._draw(color)
        self.bind("<Enter>", lambda e: self._draw(self._hover))
        self.bind("<Leave>", lambda e: self._draw(self._color))
        self.bind("<Button-1>", lambda e: self._command())

    def _draw(self, color):
        self.delete("all")
        s, x, y = 16, 3, 3
        self.create_line(x + 3, y + 3, x + s - 3, y + 3, fill=color, width=1.4)
        self.create_line(x + 6, y + 1, x + s - 6, y + 1, fill=color, width=1.4)
        self.create_line(x + 6, y + 1, x + 6, y + 3, fill=color, width=1.4)
        self.create_line(x + s - 6, y + 1, x + s - 6, y + 3, fill=color,
                         width=1.4)
        self.create_line(x + 4, y + 4, x + 5, y + s - 2, fill=color, width=1.4)
        self.create_line(x + s - 4, y + 4, x + s - 5, y + s - 2, fill=color,
                         width=1.4)
        self.create_line(x + 5, y + s - 2, x + s - 5, y + s - 2, fill=color,
                         width=1.4)
        self.create_line(x + 7, y + 6, x + 7, y + s - 4, fill=color, width=1.2)
        self.create_line(x + 10, y + 6, x + 10, y + s - 4, fill=color, width=1.2)


# ========================================================== field widgets ===
class DateField(tk.Canvas):
    H = 36

    def __init__(self, parent, on_change=None, width=1, font=None,
                 parent_bg=WHITE):
        super().__init__(parent, height=self.H, width=width, bg=parent_bg,
                         highlightthickness=0, cursor="hand2")
        self.value = None
        self.on_change = on_change
        self._font = font
        self.bind("<Configure>", lambda e: self._draw(e.width))
        self.bind("<Button-1>", lambda e: self._open_picker())

    def _draw(self, w):
        self.delete("all")
        round_rect(self, 1, 1, w - 1, self.H - 1, 10,
                   fill="#f8fafc", outline="#d1d5db")
        label = _pretty(self.value) if self.value else "Select date"
        colour = NAVY if self.value else PLACEHOLDER
        self.create_text(12, self.H / 2, anchor="w", text=label,
                         font=self._font, fill=colour)
        cx, cy = w - 18, self.H / 2
        self.create_rectangle(cx - 8, cy - 7, cx + 8, cy + 8,
                              outline=SLATE, width=1.4)
        self.create_line(cx - 8, cy - 2, cx + 8, cy - 2, fill=SLATE, width=1.4)
        self.create_line(cx - 4, cy - 10, cx - 4, cy - 5, fill=SLATE, width=1.4)
        self.create_line(cx + 4, cy - 10, cx + 4, cy - 5, fill=SLATE, width=1.4)

    def _open_picker(self):
        top = self.winfo_toplevel()
        try:
            top.grab_release()
        except tk.TclError:
            pass
        DatePickerPopup(self, self.value, self._set)
        # Regrab when the picker has fully destroyed.
        top.after(300, lambda: _regrab(top))

    def _set(self, d):
        self.value = d
        self._draw(self.winfo_width())
        if self.on_change:
            self.on_change(d)

    def get(self):
        return self.value


class TimeField(tk.Canvas):
    H = 36

    def __init__(self, parent, on_change=None, width=1, font=None,
                 parent_bg=WHITE):
        super().__init__(parent, height=self.H, width=width, bg=parent_bg,
                         highlightthickness=0, cursor="hand2")
        self.value = ""
        self.on_change = on_change
        self._font = font
        self.bind("<Configure>", lambda e: self._draw(e.width))
        self.bind("<Button-1>", lambda e: self._open_picker())

    def _draw(self, w):
        self.delete("all")
        round_rect(self, 1, 1, w - 1, self.H - 1, 10,
                   fill="#f8fafc", outline="#d1d5db")
        label = self.value or "Select time slot"
        colour = NAVY if self.value else PLACEHOLDER
        self.create_text(12, self.H / 2, anchor="w", text=label,
                         font=self._font, fill=colour)
        cx, cy = w - 18, self.H / 2
        self.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, outline=SLATE,
                         width=1.4)
        self.create_line(cx, cy, cx, cy - 5, fill=SLATE, width=1.4)
        self.create_line(cx, cy, cx + 4, cy + 2, fill=SLATE, width=1.4)

    def _open_picker(self):
        top = self.winfo_toplevel()
        try:
            top.grab_release()
        except tk.TclError:
            pass
        TimePickerPopup(self, self.value, self._set)
        top.after(300, lambda: _regrab(top))

    def _set(self, label):
        self.value = label
        self._draw(self.winfo_width())
        if self.on_change:
            self.on_change(label)

    def get(self):
        return self.value


def _regrab(top):
    try:
        if top.winfo_exists():
            top.grab_set()
    except tk.TclError:
        pass


# ========================================================== pop-up pickers ==
class DatePickerPopup(RoundedPopup):
    """Rounded calendar popup. Appears in front of the Add Event modal."""

    def __init__(self, parent_field, current, on_pick):
        modal = parent_field.winfo_toplevel()
        super().__init__(modal, 340)
        self.on_pick = on_pick
        self.today = datetime.date.today()
        self.view = (current.year, current.month) if current else \
                    (self.today.year, self.today.month)
        self.selected = current

        # stay on top of the Add Event modal
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass

        f_title = self.F(16, True)
        f_day   = self.F(12)
        f_cap   = self.F(10, True)
        f_btn   = self.F(13, True)

        head = tk.Frame(self.body, bg=WHITE)
        head.pack(fill="x")
        self.month_lbl = tk.Label(head, text="", font=f_title, fg=NAVY,
                                  bg=WHITE)
        self.month_lbl.pack(side="left")
        nav = tk.Frame(head, bg=WHITE)
        nav.pack(side="right")
        RoundedButton(nav, "‹", lambda: self._shift(-1), 30, 30, radius=8,
                      bg=WHITE, hover=BLUE_SOFT, fg=NAVY, outline="#d1d5db",
                      font=f_title).pack(side="left")
        RoundedButton(nav, "›", lambda: self._shift(1), 30, 30, radius=8,
                      bg=WHITE, hover=BLUE_SOFT, fg=NAVY, outline="#d1d5db",
                      font=f_title).pack(side="left", padx=(8, 0))

        self.days = tk.Frame(self.body, bg=WHITE)
        self.days.pack(fill="x", pady=(12, 0))

        WideButton(self.body, "Cancel", self.destroy, height=36, radius=8,
                   bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                   font=f_btn).pack(fill="x", pady=(12, 0))

        self._font_day = f_day
        self._font_cap = f_cap
        self._show_month()
        self.show()

    def _show_month(self):
        y, m = self.view
        self.month_lbl.config(text=f"{calendar.month_name[m]} {y}")
        for w in self.days.winfo_children():
            w.destroy()
        for c in range(7):
            self.days.grid_columnconfigure(c, weight=1, uniform="d")
        for c, name in enumerate(WEEKDAYS):
            tk.Label(self.days, text=name, font=self._font_cap,
                     fg="#334155", bg=WHITE).grid(row=0, column=c,
                                                  pady=(0, 4))
        for r, week in enumerate(calendar.monthcalendar(y, m), start=1):
            for c, day in enumerate(week):
                if not day:
                    continue
                d = datetime.date(y, m, day)
                disabled = d < self.today
                cell = tk.Canvas(self.days, width=36, height=36, bg=WHITE,
                                 highlightthickness=0,
                                 cursor="arrow" if disabled else "hand2")
                cell.grid(row=r, column=c, pady=2)
                self._draw_day(cell, day, disabled,
                               d == self.selected, d == self.today)
                if not disabled:
                    cell.bind("<Button-1>",
                              lambda e, dd=d: self._pick(dd))

    def _draw_day(self, canvas, day, disabled, selected, today):
        canvas.delete("all")
        if selected:
            fill, outline, txt = BLUE, BLUE, WHITE
        elif disabled:
            fill, outline, txt = WHITE, WHITE, "#cbd5e1"
        else:
            fill, outline, txt = WHITE, (BLUE if today else "#d1d5db"), NAVY
        round_rect(canvas, 1, 1, 35, 35, 8, fill=fill, outline=outline)
        canvas.create_text(18, 18, text=str(day), font=self._font_day,
                           fill=txt)

    def _shift(self, delta):
        y, m = self.view
        idx = y * 12 + m - 1 + delta
        new_y, new_m = idx // 12, idx % 12 + 1
        if (new_y, new_m) < (self.today.year, self.today.month):
            return
        self.view = (new_y, new_m)
        self._show_month()

    def _pick(self, d):
        self.on_pick(d)
        self.destroy()


class TimePickerPopup(RoundedPopup):
    def __init__(self, parent_field, current, on_pick):
        modal = parent_field.winfo_toplevel()
        super().__init__(modal, 300)
        self.on_pick = on_pick

        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass

        f_title = self.F(16, True)
        f_slot  = self.F(13)
        f_btn   = self.F(13, True)

        tk.Label(self.body, text="Choose a time slot", font=f_title,
                 fg=NAVY, bg=WHITE).pack(anchor="w", pady=(0, 12))

        for label in TIME_SLOTS:
            active = label == current
            RoundedButton(self.body, label,
                          lambda l=label: self._pick(l),
                          240, 38, radius=8,
                          bg=BLUE if active else WHITE,
                          hover=BLUE_DARK if active else BLUE_SOFT,
                          fg=WHITE if active else NAVY,
                          outline=BLUE if active else "#d1d5db",
                          font=f_slot).pack(fill="x", pady=3)

        WideButton(self.body, "Cancel", self.destroy, height=36, radius=8,
                   bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                   font=f_btn).pack(fill="x", pady=(12, 0))

        self.show()

    def _pick(self, label):
        self.on_pick(label)
        self.destroy()


# ========================================================== Add Event form ==
class AddEventDialog(RoundedPopup):
    def __init__(self, page):
        super().__init__(page.app, 620)
        self.event_page = page            # renamed for safety
        self.image_path = ""

        f_title = self.F(20, True)
        f_cap   = self.F(10, True)
        f_input = self.F(13)
        f_btn   = self.F(13, True)

        tk.Label(self.body, text="Add Event Form", font=f_title, fg=NAVY,
                 bg=WHITE).pack(anchor="w", pady=(0, 10))

        grid = tk.Frame(self.body, bg=WHITE)
        grid.pack(fill="x")
        grid.grid_columnconfigure(0, weight=1, uniform="fld")
        grid.grid_columnconfigure(1, weight=1, uniform="fld")

        self.inputs = {}

        tk.Label(grid, text="EVENT NAME", font=f_cap, fg=SLATE, bg=WHITE
                 ).grid(row=0, column=0, columnspan=2, sticky="w",
                        pady=(4, 4))
        self.in_title = _light_entry(grid, "Football League Finals", f_input)
        self.in_title.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.inputs["title"] = self.in_title

        tk.Label(grid, text="DATE", font=f_cap, fg=SLATE, bg=WHITE
                 ).grid(row=2, column=0, sticky="w", pady=(10, 4))
        tk.Label(grid, text="TIME", font=f_cap, fg=SLATE, bg=WHITE
                 ).grid(row=2, column=1, sticky="w", padx=(10, 0),
                        pady=(10, 4))
        self.in_date = DateField(grid, font=f_input)
        self.in_date.grid(row=3, column=0, sticky="ew")
        self.in_time = TimeField(grid, font=f_input)
        self.in_time.grid(row=3, column=1, sticky="ew", padx=(10, 0))

        tk.Label(grid, text="LOCATION (FACILITY)", font=f_cap, fg=SLATE,
                 bg=WHITE).grid(row=4, column=0, columnspan=2, sticky="w",
                                pady=(10, 4))
        self.in_location = _light_entry(grid, "Football Ground", f_input)
        self.in_location.grid(row=5, column=0, columnspan=2, sticky="ew")
        self.inputs["location"] = self.in_location

        tk.Label(grid, text="DESCRIPTION", font=f_cap, fg=SLATE, bg=WHITE
                 ).grid(row=6, column=0, columnspan=2, sticky="w",
                        pady=(10, 4))
        desc = FlexInput(grid, "The grand finale of the internal college "
                               "league. Standard rules apply.",
                         font=f_input, parent_bg=WHITE, multiline=True,
                         height=64)
        desc.config(bg="#e5e7eb")
        desc.winfo_children()[0].config(bg="#f8fafc")
        desc.widget.config(bg="#f8fafc")
        desc.grid(row=7, column=0, columnspan=2, sticky="ew")
        self.inputs["description"] = desc

        # ---------- cover image ----------
        tk.Label(self.body, text="UPLOAD COVER IMAGE", font=f_cap, fg=SLATE,
                 bg=WHITE).pack(anchor="w", pady=(12, 4))
        self.picker = tk.Frame(self.body, bg="#eff6ff", cursor="hand2")
        self.picker.pack(fill="x")
        self.pick_icon = tk.Label(self.picker, text="🖼", font=f_btn,
                                  fg=BLUE, bg="#eff6ff")
        self.pick_icon.pack(side="left", padx=(10, 6), pady=8)
        self.pick_label = tk.Label(self.picker, text="Choose an image…",
                                   font=f_input, fg=BLUE, bg="#eff6ff")
        self.pick_label.pack(side="left", pady=8)
        browse = tk.Label(self.picker, text="Browse…", font=f_btn, fg=WHITE,
                          bg=BLUE, cursor="hand2", padx=10, pady=3)
        browse.pack(side="right", padx=8, pady=5)
        for w in (self.picker, self.pick_icon, self.pick_label, browse):
            w.bind("<Button-1>", self._pick_image)

        # ---------- publish + buttons on one row ----------
        row = tk.Frame(self.body, bg=WHITE)
        row.pack(fill="x", pady=(14, 0))

        left = tk.Frame(row, bg=WHITE)
        left.pack(side="left")
        tk.Label(left, text="Publish Immediately", font=f_btn, fg=NAVY,
                 bg=WHITE).pack(side="left")
        self.publish = tk.BooleanVar(value=True)
        self.switch = tk.Canvas(left, width=44, height=24, bg=WHITE,
                                highlightthickness=0, cursor="hand2")
        self.switch.pack(side="left", padx=(10, 0))
        self.switch.bind("<Button-1>", lambda e: self._toggle_publish())
        self._draw_switch()

        right = tk.Frame(row, bg=WHITE)
        right.pack(side="right")
        WideButton(right, "Cancel", self.destroy, height=38, radius=8,
                   bg=WHITE, hover=BLUE_SOFT, fg=NAVY, outline="#d1d5db",
                   font=f_btn).pack(side="left", padx=(0, 8))
        WideButton(right, "Save Event", self._save, height=38, radius=8,
                   bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                   font=f_btn).pack(side="left")

        self.show()
        # NOTE: no -topmost on the modal. Only the picker popups go topmost
        # so they can appear in front of this modal.

    # ---- cover image --------------------------------------------------------
    def _pick_image(self, _event=None):
        try:
            self.grab_release()
        except tk.TclError:
            pass

        was_rounded = getattr(self, "rounded", False)
        if was_rounded:
            try:
                self.overrideredirect(False)
                self.attributes("-transparentcolor", "")
            except tk.TclError:
                pass

        try:
            path = filedialog.askopenfilename(
                parent=self,
                title="Choose cover image",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                           ("All files", "*.*")])
        finally:
            if was_rounded:
                try:
                    self.overrideredirect(True)
                    self.attributes("-transparentcolor", self.KEY)
                except tk.TclError:
                    pass
            try:
                self.lift()
                self.focus_force()
            except tk.TclError:
                pass
            try:
                self.grab_set()
            except tk.TclError:
                pass

        if not path:
            return

        base = os.path.basename(path)
        try:
            dest = os.path.join(ASSETS_DIR, base)
            if os.path.abspath(path) != os.path.abspath(dest):
                shutil.copyfile(path, dest)
            self.image_path = base
        except Exception:
            self.image_path = path

        # preview goes into the small icon slot - the modal height never grows
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).convert("RGB")
            img.thumbnail((28, 28))
            self._preview = ImageTk.PhotoImage(img)
            self.pick_icon.config(image=self._preview, text="")
        except Exception:
            pass

        self.pick_label.config(text=base)

    # ---- publish toggle -----------------------------------------------------
    def _toggle_publish(self):
        self.publish.set(not self.publish.get())
        self._draw_switch()

    def _draw_switch(self):
        self.switch.delete("all")
        on = self.publish.get()
        round_rect(self.switch, 1, 1, 43, 23, 12,
                   fill=BLUE if on else "#cbd5e1",
                   outline=BLUE if on else "#cbd5e1")
        cx = 32 if on else 12
        self.switch.create_oval(cx - 9, 3, cx + 9, 21, fill=WHITE,
                                outline=WHITE)

    # ---- save ---------------------------------------------------------------
    def _save(self):
        title = self.inputs["title"].get()
        location = self.inputs["location"].get()
        date = self.in_date.get()
        time_label = self.in_time.get()
        desc = self.inputs["description"].get()

        if not title or not date or not time_label or not location:
            messagebox.showwarning(
                "Missing details",
                "Please fill in the event name, pick a date and time, and "
                "enter the location.", parent=self)
            return

        ev = {
            "title":        title,
            "category":     "Indoor Sports",
            "date":         _pretty(date),
            "time":         time_label,
            "location":     location,
            "organizer":    "Sports Committee",
            "image":        self.image_path or "indoor.jpg",
            "description":  desc or
                            "A campus event designed to encourage teamwork "
                            "and healthy competition.",
            "admin_status": "Approved" if self.publish.get() else "Pending",
        }
        add_event(self.app.events, ev)
        self.destroy()
        try:
            self.event_page._render_grid()
        except tk.TclError:
            pass


# ---- helpers --------------------------------------------------------------
def _pretty(d):
    months = ["", "January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November",
              "December"]
    return f"{d.day} {months[d.month]} {d.year}"


def _light_entry(parent, placeholder, font):
    box = RoundedEntry(parent, placeholder, width=1, height=36, font=font)
    box.itemconfig(box._box, fill="#f8fafc", outline="#d1d5db")
    box.entry.config(bg="#f8fafc")
    box.placeholder.config(bg="#f8fafc")
    return box