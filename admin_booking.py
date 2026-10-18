"""admin_booking.py - Court Bookings screen + Booking Details modal.

Every reservation made on the user side shows up here. The admin can filter
by facility and status, search by student/facility, and Approve / Reject /
Cancel from the details modal. The status pill updates live.
"""
import tkinter as tk

from common import *
from reservation import RoundedPopup
from admin_shell import AdminPage, PAGE_BG
from admin_data import (bookings_for, set_booking_status, facility_names,
                        STATUS_COLOR, CONFIRMED, PENDING, CANCELLED)


# ============================================================= the page ====
class BookingPage(AdminPage):
    def build(self):
        self.filter_facility = "All Facilities"
        self.filter_status   = "All Statuses"

        self.body = tk.Frame(self, bg=PAGE_BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=24)
        self._header()
        self._table_holder = tk.Frame(self.body, bg=PAGE_BG)
        self._table_holder.pack(fill="both", expand=True)
        self._render_table()

    def on_show(self, **kwargs):
        if getattr(self, "_built", False):
            self._rebuild_facility_dropdown()
            self._render_table()

    # --------------------------------------------------------- header bar
    def _header(self):
        head = tk.Frame(self.body, bg=PAGE_BG)
        head.pack(fill="x", pady=(0, 18))
        head.grid_columnconfigure(0, weight=1)
        tk.Label(head, text="Court Bookings", font=self.f["h1"], fg=NAVY,
                 bg=PAGE_BG).grid(row=0, column=0, sticky="w")

        right = tk.Frame(head, bg=PAGE_BG)
        right.grid(row=0, column=1, sticky="e")

        self.search = RoundedEntry(right, "Search by student, facility...",
                                   width=240, height=36, font=self.f["small"],
                                   parent_bg=PAGE_BG)
        self.search.pack(side="left", padx=(0, 10))
        self.search.var.trace_add("write", lambda *a: self._render_table())

        self._facility_slot = tk.Frame(right, bg=PAGE_BG)
        self._facility_slot.pack(side="left", padx=(0, 10))
        self._rebuild_facility_dropdown()

        self._dropdown(right, "All Statuses",
                       ["All Statuses", CONFIRMED, PENDING, CANCELLED],
                       lambda v: self._set_status(v))

    def _rebuild_facility_dropdown(self):
        for w in self._facility_slot.winfo_children():
            w.destroy()
        self._dropdown(self._facility_slot, "All Facilities",
                       facility_names(self.app),
                       lambda v: self._set_facility(v))

    def _set_facility(self, v):
        self.filter_facility = v
        self._render_table()

    def _set_status(self, v):
        self.filter_status = v
        self._render_table()

    def _dropdown(self, parent, label, options, on_pick):
        box = tk.Canvas(parent, width=180, height=36, bg=PAGE_BG,
                        highlightthickness=0, cursor="hand2")
        box.pack(side="left")
        round_rect(box, 1, 1, 179, 35, 10, fill=WHITE, outline="#e5e7eb")
        tid = box.create_text(14, 18, anchor="w", text=label,
                              font=self.f["small"], fill=NAVY)
        box.create_line(158, 15, 163, 20, 168, 15, fill=SLATE, width=2)

        menu = tk.Menu(box, tearoff=0, font=self.f["small"], bg=WHITE,
                       fg=NAVY, activebackground=BLUE, activeforeground=WHITE,
                       bd=0)

        def pick(v):
            box.itemconfig(tid, text=v)
            on_pick(v)

        for opt in options:
            menu.add_command(label=opt, command=lambda o=opt: pick(o))

        def open_menu(_):
            try:
                menu.tk_popup(box.winfo_rootx(),
                              box.winfo_rooty() + box.winfo_height())
            finally:
                menu.grab_release()
        box.bind("<Button-1>", open_menu)
        return box

    # --------------------------------------------------------- the table
    def _render_table(self):
        for w in self._table_holder.winfo_children():
            w.destroy()

        q = getattr(self, "search", None)
        query = q.get() if q is not None else ""
        rows = bookings_for(self.app,
                            facility=self.filter_facility,
                            status=self.filter_status, query=query)

        card = Card(self._table_holder, PAGE_BG, pad=0, border="#e5e7eb")
        card.pack(fill="both", expand=True)
        inner = card.inner

        cols = ["Booking ID", "Student Name", "Facility", "Date",
                "Time Slot", "Status", "Action"]
        weights = [1, 2, 2, 2, 2, 1, 1]

        head = tk.Frame(inner, bg="#f8fafc")
        head.pack(fill="x")
        for i, (c, w) in enumerate(zip(cols, weights)):
            head.grid_columnconfigure(i, weight=w, uniform="bk")
            tk.Label(head, text=c, font=self.f["cap"], fg=SLATE,
                     bg="#f8fafc", anchor="w").grid(
                         row=0, column=i, sticky="ew", padx=14, pady=12)

        if not rows:
            tk.Label(inner, text="No bookings match your filters.",
                     font=self.f["p"], fg=SLATE, bg=WHITE).pack(pady=40)
            return

        for b in rows:
            row = tk.Frame(inner, bg=WHITE)
            row.pack(fill="x")
            for i, w in enumerate(weights):
                row.grid_columnconfigure(i, weight=w, uniform="bk")
            tk.Label(row, text=b["id"], font=self.f["small"], fg=BLUE,
                     bg=WHITE, anchor="w").grid(row=0, column=0, sticky="ew",
                                                padx=14, pady=12)
            values = [b["name"], b["ground"],
                      f"{b['date'].day} {b['date'].strftime('%b %Y')}",
                      b["time"]]
            for i, v in enumerate(values, start=1):
                tk.Label(row, text=v, font=self.f["small"], fg=NAVY,
                         bg=WHITE, anchor="w").grid(row=0, column=i,
                                                    sticky="ew", padx=14, pady=12)
            fg, bg = STATUS_COLOR.get(b["status"], (SLATE, "#f1f5f9"))
            Pill(row, b["status"], self.f["small"], fg, bg, parent_bg=WHITE,
                 padx=10, pady=4).grid(row=0, column=5, sticky="w", padx=14)
            view = tk.Label(row, text="View", font=self.f["small"], fg=BLUE,
                            bg=WHITE, cursor="hand2")
            view.grid(row=0, column=6, sticky="w", padx=14)
            view.bind("<Button-1>",
                      lambda e, bb=b: BookingDetailDialog(self, bb))
            tk.Frame(inner, bg="#f1f5f9", height=1).pack(fill="x")

        foot = tk.Frame(inner, bg=WHITE)
        foot.pack(fill="x", padx=16, pady=12)
        tk.Label(foot,
                 text=f"Showing {len(rows)} booking"
                      f"{'s' if len(rows) != 1 else ''}",
                 font=self.f["small"], fg=SLATE, bg=WHITE).pack(side="left")


# ========================================================== the modal ======
class BookingDetailDialog(RoundedPopup):
    """Booking Details pop-up. Buttons depend on the current status:
       Pending   -> Approve + Reject
       Confirmed -> Cancel
       Cancelled -> (no actions - already final)."""

    def __init__(self, page, booking):
        super().__init__(page.app, 400)
        self.page = page
        self.booking = booking

        f_title = self.F(22, True)
        f_cap   = self.F(10, True)
        f_val   = self.F(15, True)
        f_sub   = self.F(13)
        f_btn   = self.F(14, True)

        # ---- header: title on the left, booking id on the right
        head = tk.Frame(self.body, bg=WHITE)
        head.pack(fill="x")
        tk.Label(head, text="Booking Details", font=f_title, fg=NAVY,
                 bg=WHITE).pack(side="left")
        tk.Label(head, text=booking["id"], font=f_btn, fg=BLUE,
                 bg=WHITE).pack(side="right")

        # ---- student chip
        chip = Card(self.body, WHITE, fill=SOFT_BG, border="#eef2f7",
                    radius=12, pad=14)
        chip.pack(fill="x", pady=(16, 18))
        r = tk.Frame(chip.inner, bg=SOFT_BG)
        r.pack(fill="x")
        av = tk.Canvas(r, width=48, height=48, bg=SOFT_BG,
                       highlightthickness=0)
        av.create_oval(0, 0, 48, 48, fill=BLUE_SOFT, outline=BLUE_SOFT)
        av.create_text(24, 26, text="👤", fill=BLUE, font=f_sub)
        av.pack(side="left")
        info = tk.Frame(r, bg=SOFT_BG)
        info.pack(side="left", padx=(12, 0))
        tk.Label(info, text=booking["name"], font=f_val, fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")
        tk.Label(info, text=f"Student No: {booking['student_id']}",
                 font=f_sub, fg=SLATE, bg=SOFT_BG).pack(anchor="w", pady=(2, 0))
        tk.Label(chip.inner, text="EMAIL", font=f_cap, fg=SLATE,
                 bg=SOFT_BG).pack(anchor="w", pady=(14, 4))
        tk.Label(chip.inner, text=booking["email"], font=f_sub, fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")

        # ---- facility / date / time rows
        for cap, val in (("FACILITY", booking["ground"]),
                         ("DATE", f"{booking['date'].day} "
                                  f"{booking['date'].strftime('%b %Y')}"),
                         ("TIME SLOT", booking["time"])):
            tk.Label(self.body, text=cap, font=f_cap, fg=SLATE,
                     bg=WHITE).pack(anchor="w", pady=(12, 2))
            tk.Label(self.body, text=val, font=f_val, fg=NAVY,
                     bg=WHITE).pack(anchor="w")

        # ---- current status pill
        tk.Label(self.body, text="CURRENT STATUS", font=f_cap, fg=SLATE,
                 bg=WHITE).pack(anchor="w", pady=(14, 6))
        fg, bg = STATUS_COLOR.get(booking["status"], (SLATE, "#f1f5f9"))
        Pill(self.body, booking["status"], f_sub, fg, bg,
             padx=14, pady=5).pack(anchor="w")

        # ---- actions, tailored to the current status
        status = booking["status"]
        if status == PENDING:
            WideButton(self.body, "Approve Booking",
                       lambda: self._act(CONFIRMED), height=44, radius=8,
                       bg=GREEN, hover="#0e9f6e", fg=WHITE,
                       font=f_btn).pack(fill="x", pady=(14, 6))
            WideButton(self.body, "Reject Booking",
                       lambda: self._act(CANCELLED), height=44, radius=8,
                       bg=WHITE, hover="#fef3c7", fg="#d97706",
                       outline="#d97706", font=f_btn).pack(fill="x", pady=6)

        elif status == CONFIRMED:
            WideButton(self.body, "Cancel Booking",
                       lambda: self._act(CANCELLED), height=44, radius=8,
                       bg=WHITE, hover="#fee2e2", fg="#dc2626",
                       outline="#dc2626", font=f_btn).pack(fill="x",
                                                            pady=(14, 6))
        # CANCELLED -> no actions; the booking is already final.

        self.show()

    def _act(self, new_status):
        set_booking_status(self.app, self.booking["id"], new_status)
        print(f"[notify {self.booking['email']}] "
              f"Your booking {self.booking['id']} is now {new_status}.")
        self.destroy()
        try:
            self.page._render_table()
        except tk.TclError:
            pass