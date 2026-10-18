"""admin_users.py - the admin Users screen + User Details modal."""
import tkinter as tk
from tkinter import messagebox

from common import *
from reservation import RoundedPopup
from admin_shell import AdminPage, PAGE_BG
from admin_data import all_users, set_user_status


STATUS_COLORS = {
    "Active":    ("#059669", "#dcfce7"),
    "Inactive":  (SLATE,     "#f1f5f9"),
    "Suspended": ("#dc2626", "#fee2e2"),
}


class UsersPage(AdminPage):
    def build(self):
        self.body = tk.Frame(self, bg=PAGE_BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=24)
        self._header()
        self._table_holder = tk.Frame(self.body, bg=PAGE_BG)
        self._table_holder.pack(fill="both", expand=True)
        self._render_table()

    def on_show(self, **kwargs):
        if getattr(self, "_built", False):
            self._render_table()

    def _header(self):
        head = tk.Frame(self.body, bg=PAGE_BG)
        head.pack(fill="x", pady=(0, 16))
        head.grid_columnconfigure(0, weight=1)
        tk.Label(head, text="Users", font=self.f["h1"], fg=NAVY,
                 bg=PAGE_BG).grid(row=0, column=0, sticky="w")
        right = tk.Frame(head, bg=PAGE_BG)
        right.grid(row=0, column=1, sticky="e")
        self.search = RoundedEntry(right, "Search by name or email...",
                                   width=280, height=36, font=self.f["small"],
                                   parent_bg=PAGE_BG)
        self.search.pack(side="left")
        self.search.var.trace_add("write", lambda *a: self._render_table())

    def _render_table(self):
        for w in self._table_holder.winfo_children():
            w.destroy()
        q = self.search.get().lower() if hasattr(self, "search") else ""
        users = [u for u in all_users()
                 if not q or q in u["name"].lower() or q in u["email"].lower()]

        card = Card(self._table_holder, PAGE_BG, pad=0, border="#e5e7eb")
        card.pack(fill="both", expand=True)
        inner = card.inner

        title = tk.Frame(inner, bg=WHITE)
        title.pack(fill="x", padx=20, pady=(16, 10))
        tk.Label(title, text="Registered Students", font=self.f["h2"],
                 fg=NAVY, bg=WHITE).pack(side="left")
        export = tk.Label(title, text="Export List", font=self.f["small"],
                          fg=BLUE, bg=WHITE, cursor="hand2")
        export.pack(side="right")
        export.bind("<Button-1>", lambda e: messagebox.showinfo(
            "Export", "This would export the list as CSV/Excel."))

        cols = ["Name", "Email", "Total Bookings", "Status", "Action"]
        weights = [2, 4, 2, 1, 1]
        head = tk.Frame(inner, bg="#f8fafc")
        head.pack(fill="x")
        for i, (c, w) in enumerate(zip(cols, weights)):
            head.grid_columnconfigure(i, weight=w, uniform="us")
            tk.Label(head, text=c, font=self.f["cap"], fg=SLATE,
                     bg="#f8fafc", anchor="w").grid(
                         row=0, column=i, sticky="ew", padx=16, pady=10)

        if not users:
            tk.Label(inner, text="No users match your search.",
                     font=self.f["p"], fg=SLATE, bg=WHITE).pack(pady=40)
            return

        for u in users:
            row = tk.Frame(inner, bg=WHITE)
            row.pack(fill="x")
            for i, w in enumerate(weights):
                row.grid_columnconfigure(i, weight=w, uniform="us")
            tk.Label(row, text=u["name"], font=self.f["small"], fg=NAVY,
                     bg=WHITE, anchor="w").grid(row=0, column=0, sticky="ew",
                                                padx=16, pady=10)
            tk.Label(row, text=u["email"], font=self.f["small"], fg=SLATE,
                     bg=WHITE, anchor="w").grid(row=0, column=1, sticky="ew",
                                                padx=16, pady=10)
            tk.Label(row, text=f"{u['bookings']} bookings",
                     font=self.f["small"], fg=NAVY, bg=WHITE,
                     anchor="w").grid(row=0, column=2, sticky="ew",
                                      padx=16, pady=10)
            fg, bg = STATUS_COLORS.get(u["status"], (SLATE, "#f1f5f9"))
            Pill(row, u["status"], self.f["small"], fg, bg, parent_bg=WHITE,
                 padx=10, pady=4).grid(row=0, column=3, sticky="w", padx=16)
            view = tk.Label(row, text="View Details", font=self.f["small"],
                            fg=BLUE, bg=WHITE, cursor="hand2")
            view.grid(row=0, column=4, sticky="w", padx=16)
            view.bind("<Button-1>",
                      lambda e, uu=u: UserDetailDialog(self, uu))
            tk.Frame(inner, bg="#f1f5f9", height=1).pack(fill="x")

        foot = tk.Frame(inner, bg=WHITE)
        foot.pack(fill="x", padx=16, pady=12)
        tk.Label(foot, text=f"Showing {len(users)} student"
                            f"{'s' if len(users) != 1 else ''}",
                 font=self.f["small"], fg=SLATE,
                 bg=WHITE).pack(side="left")


# -------------------------------------------------------- User Details modal
class UserDetailDialog(RoundedPopup):
    def __init__(self, page, user):
        super().__init__(page.app, 400)
        self.page = page
        self.user = user

        f_title = self.F(22, True)
        f_cap   = self.F(10, True)
        f_val   = self.F(15, True)
        f_sub   = self.F(13)
        f_btn   = self.F(14, True)

        tk.Label(self.body, text="User Details", font=f_title, fg=NAVY,
                 bg=WHITE).pack(anchor="w")

        # top chip
        chip = Card(self.body, WHITE, fill=SOFT_BG, border="#eef2f7",
                    radius=12, pad=14)
        chip.pack(fill="x", pady=(14, 16))
        head = tk.Frame(chip.inner, bg=SOFT_BG)
        head.pack(fill="x")
        av = tk.Canvas(head, width=48, height=48, bg=SOFT_BG,
                       highlightthickness=0)
        av.create_oval(0, 0, 48, 48, fill=BLUE_SOFT, outline=BLUE_SOFT)
        av.create_text(24, 26, text="👤", fill=BLUE, font=f_sub)
        av.pack(side="left")
        info = tk.Frame(head, bg=SOFT_BG)
        info.pack(side="left", padx=(12, 0))
        tk.Label(info, text=user["name"], font=f_val, fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")
        tk.Label(info, text=f"Student ID: {user['student_id']}", font=f_sub,
                 fg=SLATE, bg=SOFT_BG).pack(anchor="w", pady=(2, 0))
        tk.Label(chip.inner, text="EMAIL & PHONE", font=f_cap, fg=SLATE,
                 bg=SOFT_BG).pack(anchor="w", pady=(12, 4))
        tk.Label(chip.inner, text=user["email"], font=f_sub, fg=NAVY,
                 bg=SOFT_BG).pack(anchor="w")
        tk.Label(chip.inner, text=user.get("phone", "+975 17 000 000"),
                 font=f_sub, fg=NAVY, bg=SOFT_BG).pack(anchor="w",
                                                        pady=(2, 0))

        tk.Label(self.body, text="TOTAL BOOKINGS COUNT", font=f_cap,
                 fg=SLATE, bg=WHITE).pack(anchor="w", pady=(14, 4))
        tk.Label(self.body,
                 text=f"{user['bookings']} Confirmed  /  1 Cancelled",
                 font=f_val, fg=BLUE, bg=WHITE).pack(anchor="w")

        tk.Label(self.body, text="RECENT BOOKINGS", font=f_cap, fg=SLATE,
                 bg=WHITE).pack(anchor="w", pady=(14, 4))
        for line in ("• Basketball Court (Today 4–5 PM)",
                     "• Badminton Hall (08 Sep 2–3 PM)"):
            tk.Label(self.body, text=line, font=f_sub, fg=NAVY,
                     bg=WHITE).pack(anchor="w")

        # privileges toggle
        priv = tk.Frame(self.body, bg=WHITE)
        priv.pack(fill="x", pady=(18, 4))
        tk.Label(priv, text="ACCOUNT PRIVILEGES", font=f_cap, fg=SLATE,
                 bg=WHITE).pack(anchor="w")
        row = tk.Frame(self.body, bg=WHITE)
        row.pack(fill="x", pady=(6, 0))
        tk.Label(row, text="Allow Booking Grounds", font=f_btn, fg=NAVY,
                 bg=WHITE).pack(side="left")
        self.allow = tk.BooleanVar(value=user["status"] != "Suspended")
        self.switch = tk.Canvas(row, width=44, height=24, bg=WHITE,
                                highlightthickness=0, cursor="hand2")
        self.switch.pack(side="right")
        self.switch.bind("<Button-1>", lambda e: self._toggle())
        self._draw_switch()

        if user["status"] != "Suspended":
            WideButton(self.body, "Suspend Account", self._suspend,
                       height=44, radius=8, bg=WHITE, hover="#fee2e2",
                       fg="#dc2626", outline="#dc2626",
                       font=f_btn).pack(fill="x", pady=(18, 6))
        else:
            WideButton(self.body, "Reactivate Account", self._reactivate,
                       height=44, radius=8, bg=GREEN, hover="#0e9f6e",
                       fg=WHITE, font=f_btn).pack(fill="x", pady=(18, 6))

        back = tk.Label(self.body, text="Back", font=f_sub, fg=BLUE,
                        bg=WHITE, cursor="hand2")
        back.pack(anchor="w", pady=(4, 0))
        back.bind("<Button-1>", lambda e: self.destroy())

        self.show()

    def _toggle(self):
        self.allow.set(not self.allow.get())
        self._draw_switch()
        new_status = "Active" if self.allow.get() else "Inactive"
        set_user_status(self.user["email"], new_status)
        self.user["status"] = new_status

    def _draw_switch(self):
        self.switch.delete("all")
        on = self.allow.get()
        round_rect(self.switch, 1, 1, 43, 23, 12,
                   fill=BLUE if on else "#cbd5e1",
                   outline=BLUE if on else "#cbd5e1")
        cx = 32 if on else 12
        self.switch.create_oval(cx - 9, 3, cx + 9, 21, fill=WHITE,
                                outline=WHITE)

    def _suspend(self):
        if not messagebox.askyesno("Suspend",
                                   f"Suspend {self.user['name']}'s account?"):
            return
        set_user_status(self.user["email"], "Suspended")
        self.user["status"] = "Suspended"
        self.destroy()
        try:
            self.page._render_table()
        except tk.TclError:
            pass

    def _reactivate(self):
        set_user_status(self.user["email"], "Active")
        self.user["status"] = "Active"
        self.destroy()
        try:
            self.page._render_table()
        except tk.TclError:
            pass