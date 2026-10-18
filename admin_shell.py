"""admin_shell.py - the shared admin frame."""
import os
import tkinter as tk
from tkinter import font as tkfont

from common import *
from admin_data import collect_notifications, load_admin_profile


SIDEBAR_BG     = "#0f172a"
SIDEBAR_HOVER  = "#1e293b"
SIDEBAR_ACTIVE = "#2563eb"
SIDEBAR_TEXT   = "#cbd5e1"
TOPBAR_BG      = WHITE
PAGE_BG        = "#f1f5f9"
SIDEBAR_W      = 240

NAV = [
    ("dashboard", "Dashboard",      "▦", "admin_dashboard.DashboardPage"),
    ("booking",   "Court Bookings", "▤", "admin_booking.BookingPage"),
    ("events",    "Events",         "▤", "admin_event.EventPage"),
    ("users",     "Users",          "◉", "admin_users.UsersPage"),
    ("feedback",  "Feedback",       "▭", "admin_feedback.FeedbackPage"),
    ("account",   "Account",        "◍", "admin_account.AccountPage"),
]


class AdminPage(tk.Frame):
    def __init__(self, shell):
        super().__init__(shell.content_area, bg=PAGE_BG)
        self.shell = shell
        self.app = shell.app
        self.f = shell.f
        self.content = self

    def build(self):
        raise NotImplementedError

    def on_show(self, **kwargs):
        pass

    def reflow(self, w=None):
        if hasattr(self, "on_reflow"):
            self.on_reflow(w)


class AdminShell(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=PAGE_BG)
        self.app = app

        def F(size, bold=False):
            return tkfont.Font(family=app.family, size=-size,
                               weight="bold" if bold else "normal")
        self.f = {
            "brand":    F(18, True), "tag": F(8, True),
            "nav":      F(13),       "nav_bold": F(13, True),
            "h1":       F(26, True), "h2": F(18, True), "h3": F(15, True),
            "p":        F(13),       "small": F(11),     "cap": F(10, True),
            "btn":      F(12, True), "val": F(13, True), "icon": F(16, True),
            "num":      F(30, True),
        }

        self._pages = {}
        self._current = None
        self._reflow_job = None
        self._avatar = None
        self._chip_avatar = None
        self._avatar_photo = None
        self._chip_avatar_photo = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar()

        right = tk.Frame(self, bg=PAGE_BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._topbar(right)

        outer = tk.Frame(right, bg=PAGE_BG)
        outer.grid(row=1, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(outer, bg=PAGE_BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb = tk.Scrollbar(outer, orient="vertical",
                                command=self.canvas.yview)
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.content_area = tk.Frame(self.canvas, bg=PAGE_BG)
        self._win = self.canvas.create_window(0, 0, window=self.content_area,
                                              anchor="nw")

        def _on_content_resize(e):
            try:
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            except tk.TclError:
                return
            if self._reflow_job is not None:
                try:
                    self.after_cancel(self._reflow_job)
                except tk.TclError:
                    pass
            self._reflow_job = self.after(
                60, lambda w=e.width: self._do_reflow(w))
        self.content_area.bind("<Configure>", _on_content_resize)

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self._win, width=e.width))

        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(seq, self._wheel, add="+")

        self._refresh_avatar()
        self.after(5000, self._poll_notifications)

    def on_show(self, **kwargs):
        self._refresh_user_chip()
        self._refresh_avatar()
        self.show(self._current or "dashboard", **kwargs)
        self._poll_notifications()

    def reflow(self, w=None):
        self._do_reflow(w or self.winfo_width())

    def _do_reflow(self, w):
        self._reflow_job = None
        page = self._pages.get(self._current)
        if page is not None and hasattr(page, "on_reflow"):
            try:
                page.on_reflow(w)
            except tk.TclError:
                pass

    def _wheel(self, e):
        if not self.winfo_viewable():
            return
        num = getattr(e, "num", 0)
        d = (-1 if num == 4 else (1 if num == 5
                                   else (-1 if e.delta > 0 else 1)))
        self.canvas.yview_scroll(d * 3, "units")

    # ============================================================== sidebar
    def _sidebar(self):
        bar = tk.Frame(self, bg=SIDEBAR_BG, width=SIDEBAR_W)
        bar.grid(row=0, column=0, sticky="ns")
        bar.grid_propagate(False)
        bar.grid_rowconfigure(2, weight=1)
        bar.grid_columnconfigure(0, weight=1)

        # --- brand: same LogoMark as the user side ---
        brand = tk.Frame(bar, bg=SIDEBAR_BG)
        brand.grid(row=0, column=0, sticky="ew", padx=22, pady=(22, 26))
        LogoMark(brand, 36, parent_bg=SIDEBAR_BG).pack(side="left")
        txt = tk.Frame(brand, bg=SIDEBAR_BG)
        txt.pack(side="left", padx=(10, 0))
        tk.Label(txt, text="PLAY ZONE", font=self.f["brand"], fg=WHITE,
                 bg=SIDEBAR_BG).pack(anchor="w")
        tk.Label(txt, text="BOOK. PLAY. ENJOY.", font=self.f["tag"], fg=GREEN,
                 bg=SIDEBAR_BG).pack(anchor="w")

        links = tk.Frame(bar, bg=SIDEBAR_BG)
        links.grid(row=1, column=0, sticky="new", padx=10, pady=(14, 0))
        self._links = {}
        for key, label, glyph, _ in NAV:
            row = tk.Frame(links, bg=SIDEBAR_BG, cursor="hand2")
            row.pack(fill="x", pady=2)
            inner = tk.Frame(row, bg=SIDEBAR_BG)
            inner.pack(fill="x", padx=14, pady=11)
            ic = tk.Label(inner, text=glyph, font=self.f["nav"],
                          fg=SIDEBAR_TEXT, bg=SIDEBAR_BG, width=2)
            ic.pack(side="left")
            lb = tk.Label(inner, text=label, font=self.f["nav"],
                          fg=SIDEBAR_TEXT, bg=SIDEBAR_BG)
            lb.pack(side="left", padx=(8, 0))

            def enter(_=None, r=row, i=inner, icon=ic, lbl=lb, k=key):
                if k == self._current:
                    return
                for w in (r, i, icon, lbl):
                    w.config(bg=SIDEBAR_HOVER)

            def leave(_=None, r=row, i=inner, icon=ic, lbl=lb, k=key):
                if k == self._current:
                    return
                for w in (r, i, icon, lbl):
                    w.config(bg=SIDEBAR_BG)

            for w in (row, inner, ic, lb):
                w.bind("<Enter>", enter)
                w.bind("<Leave>", leave)
                w.bind("<Button-1>", lambda e, k=key: self.show(k))
            self._links[key] = (row, inner, ic, lb)

        bottom = tk.Frame(bar, bg=SIDEBAR_BG)
        bottom.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 14))

        chip = tk.Frame(bottom, bg=SIDEBAR_BG, cursor="hand2")
        chip.pack(fill="x", pady=(0, 10))
        self._chip_avatar = tk.Canvas(chip, width=34, height=34,
                                      bg=SIDEBAR_BG, highlightthickness=0)
        self._chip_avatar.pack(side="left")

        who = tk.Frame(chip, bg=SIDEBAR_BG)
        who.pack(side="left", padx=(8, 0))
        self._chip_name = tk.Label(who, text="—", font=self.f["nav_bold"],
                                   fg=WHITE, bg=SIDEBAR_BG)
        self._chip_name.pack(anchor="w")
        self._chip_role = tk.Label(who, text="—", font=self.f["small"],
                                   fg=SIDEBAR_TEXT, bg=SIDEBAR_BG)
        self._chip_role.pack(anchor="w")

        def chip_click(_):
            self.show("account")
        for w in (chip, self._chip_avatar, who, self._chip_name,
                  self._chip_role):
            w.bind("<Button-1>", chip_click)

        logout = tk.Frame(bottom, bg=SIDEBAR_BG, cursor="hand2")
        logout.pack(fill="x", padx=8)
        tk.Label(logout, text="⏻", font=self.f["nav"], fg=BLUE,
                 bg=SIDEBAR_BG).pack(side="left")
        lbl = tk.Label(logout, text="Logout", font=self.f["nav_bold"],
                       fg=BLUE, bg=SIDEBAR_BG)
        lbl.pack(side="left", padx=(6, 0))
        for w in (logout, lbl):
            w.bind("<Button-1>", lambda e: self._logout())

        self._refresh_user_chip()

    def _refresh_user_chip(self):
        try:
            p = load_admin_profile(self.app)
            self._chip_name.config(text=p.get("name", "Admin"))
            self._chip_role.config(text=p.get("role", "Super Admin"))
        except tk.TclError:
            pass

    def _refresh_avatar(self):
        p = getattr(self.app, "admin_profile", {}) or {}
        filename = (p.get("avatar") or "").strip()

        # ---------- topbar avatar ----------
        if self._avatar is not None:
            try:
                self._avatar.delete("all")
                self._avatar.create_oval(0, 0, 38, 38, fill=NAVY,
                                         outline=NAVY)
                drawn = False
                if filename:
                    path = (filename if os.path.isabs(filename)
                            else os.path.join(ASSETS_DIR, filename))
                    if PIL_OK and os.path.exists(path):
                        try:
                            from PIL import Image, ImageTk, ImageDraw
                            img = Image.open(path).convert("RGB").resize(
                                (38, 38), Image.LANCZOS)
                            mask = Image.new("L", (38, 38), 0)
                            ImageDraw.Draw(mask).ellipse((0, 0, 37, 37),
                                                          fill=255)
                            # backing colour = topbar's own colour (white)
                            out = Image.new("RGB", (38, 38), TOPBAR_BG)
                            out.paste(img, (0, 0), mask)
                            self._avatar_photo = ImageTk.PhotoImage(out)
                            self._avatar.create_image(
                                0, 0, image=self._avatar_photo, anchor="nw")
                            drawn = True
                        except Exception:
                            pass
                if not drawn:
                    self._avatar.create_text(19, 20, text="👤", fill=WHITE,
                                             font=self.f["small"])
            except tk.TclError:
                pass

        # ---------- sidebar chip avatar ----------
        if self._chip_avatar is not None:
            try:
                self._chip_avatar.delete("all")
                self._chip_avatar.create_oval(0, 0, 34, 34, fill=BLUE_SOFT,
                                              outline=BLUE_SOFT)
                drawn = False
                if filename:
                    path = (filename if os.path.isabs(filename)
                            else os.path.join(ASSETS_DIR, filename))
                    if PIL_OK and os.path.exists(path):
                        try:
                            from PIL import Image, ImageTk, ImageDraw
                            img = Image.open(path).convert("RGB").resize(
                                (34, 34), Image.LANCZOS)
                            mask = Image.new("L", (34, 34), 0)
                            ImageDraw.Draw(mask).ellipse((0, 0, 33, 33),
                                                          fill=255)
                            # backing colour = sidebar's own colour (navy)
                            out = Image.new("RGB", (34, 34), SIDEBAR_BG)
                            out.paste(img, (0, 0), mask)
                            self._chip_avatar_photo = ImageTk.PhotoImage(out)
                            self._chip_avatar.create_image(
                                0, 0, image=self._chip_avatar_photo,
                                anchor="nw")
                            drawn = True
                        except Exception:
                            pass
                if not drawn:
                    self._chip_avatar.create_text(17, 18, text="👤",
                                                  fill=BLUE,
                                                  font=self.f["small"])
            except tk.TclError:
                pass

    def _logout(self):
        LogoutDialog(self.app)

    # ============================================================== topbar
    def _topbar(self, parent):
        bar = tk.Frame(parent, bg=TOPBAR_BG, height=64)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)

        right = tk.Frame(bar, bg=TOPBAR_BG)
        right.grid(row=0, column=1, sticky="e", padx=22, pady=14)

        self._bell = tk.Canvas(right, width=30, height=30, bg=TOPBAR_BG,
                               highlightthickness=0, cursor="hand2")
        self._bell.pack(side="left", padx=(0, 14))
        self._bell.create_text(15, 15, text="🔔", fill=NAVY,
                               font=self.f["icon"], tags="bell")
        self._bell_dot = self._bell.create_oval(
            20, 3, 27, 10, fill="#ef4444", outline="#ef4444", tags="dot")
        self._bell.bind("<Button-1>", lambda e: self._toggle_notifications())
        self._notif_panel = None

        self._avatar = tk.Canvas(right, width=38, height=38, bg=TOPBAR_BG,
                                 highlightthickness=0)
        self._avatar.pack(side="left")

    def _poll_notifications(self):
        try:
            collect_notifications(self.app)
        except Exception:
            pass
        if getattr(self.app, "_notif_unread", 0):
            try:
                self._bell.itemconfig(self._bell_dot, state="normal")
            except tk.TclError:
                pass
        else:
            try:
                self._bell.itemconfig(self._bell_dot, state="hidden")
            except tk.TclError:
                pass
        self.after(20000, self._poll_notifications)

    def _toggle_notifications(self):
        if self._notif_panel and self._notif_panel.winfo_exists():
            self._notif_panel.destroy()
            self._notif_panel = None
            return
        self._notif_panel = NotificationsPanel(self)

    # ============================================================== routing
    def show(self, key, **kwargs):
        valid = {k for k, *_ in NAV}
        if key not in valid:
            return
        try:
            self.winfo_toplevel().grab_release()
        except tk.TclError:
            pass
        for w in self.winfo_toplevel().winfo_children():
            try:
                if isinstance(w, tk.Toplevel):
                    w.grab_release()
            except tk.TclError:
                pass

        if key not in self._pages:
            self._pages[key] = self._build_page(key)
        for page in self._pages.values():
            page.pack_forget()
        page = self._pages[key]
        page.pack(fill="both", expand=True)
        if not getattr(page, "_built", False):
            page.build()
            page._built = True
        page.on_show(**kwargs)
        self._set_active(key)
        self._current = key
        self.canvas.yview_moveto(0)

    def _build_page(self, key):
        cls_path = dict((k, p) for k, _, _, p in NAV)[key]
        mod_name, cls_name = cls_path.split(".")
        mod = __import__(mod_name, fromlist=[cls_name])
        return getattr(mod, cls_name)(self)

    def _set_active(self, key):
        for k, (row, inner, ic, lb) in self._links.items():
            active = k == key
            bg = SIDEBAR_ACTIVE if active else SIDEBAR_BG
            fg = WHITE if active else SIDEBAR_TEXT
            for w in (row, inner, ic, lb):
                w.config(bg=bg)
            lb.config(fg=fg,
                      font=self.f["nav_bold"] if active else self.f["nav"])
            ic.config(fg=fg)


class NotificationsPanel(tk.Frame):
    def __init__(self, shell):
        super().__init__(shell, bg=WHITE, highlightthickness=1,
                         highlightbackground="#e5e7eb")
        self.shell = shell

        shell._bell.update_idletasks()
        x = (shell._bell.winfo_rootx() - shell.winfo_rootx() - 260
             + shell._bell.winfo_width())
        y = (shell._bell.winfo_rooty() - shell.winfo_rooty()
             + shell._bell.winfo_height() + 6)
        self.place(x=max(8, x), y=y, width=360)

        header = tk.Frame(self, bg=WHITE)
        header.pack(fill="x", padx=18, pady=(16, 8))
        tk.Label(header, text="Notifications", font=shell.f["h3"], fg=NAVY,
                 bg=WHITE).pack(side="left")
        mark = tk.Label(header, text="Mark all as read",
                        font=shell.f["small"], fg=BLUE, bg=WHITE,
                        cursor="hand2")
        mark.pack(side="right")
        mark.bind("<Button-1>", lambda e: self._mark_read())
        tk.Frame(self, bg="#e5e7eb", height=1).pack(fill="x")

        items = collect_notifications(shell.app)
        if not items:
            tk.Label(self, text="You're all caught up.",
                     font=shell.f["small"], fg=SLATE, bg=WHITE,
                     pady=18).pack(fill="x")
        else:
            for n in items[:8]:
                self._row(n)

        self.after(400, self._mark_read)
        self.after(200, self._bind_outside)

    def _row(self, n):
        row = tk.Frame(self, bg=WHITE, cursor="hand2")
        row.pack(fill="x", padx=18, pady=(10, 6))
        col = tk.Frame(row, bg=WHITE, width=10)
        col.pack(side="left", anchor="n", pady=4)
        c = tk.Canvas(col, width=8, height=8, bg=WHITE, highlightthickness=0)
        c.pack()
        c.create_oval(0, 0, 8, 8, fill=n["dot"], outline=n["dot"])

        body = tk.Frame(row, bg=WHITE)
        body.pack(side="left", fill="x", expand=True, padx=(10, 0))
        tk.Label(body, text=n["text"], font=self.shell.f["small"], fg=NAVY,
                 bg=WHITE, justify="left", wraplength=250,
                 anchor="w").pack(anchor="w")
        tk.Label(body, text=n["when"], font=self.shell.f["small"],
                 fg="#94a3b8", bg=WHITE).pack(anchor="w", pady=(2, 0))

        for w in (row, col, c, body, *body.winfo_children()):
            w.bind("<Button-1>", lambda e, nn=n: self._click(nn))

    def _click(self, n):
        self.destroy()
        self.shell._notif_panel = None
        target = n.get("target")
        if target:
            page, _ = target
            self.shell.show(page)

    def _mark_read(self):
        self.shell.app._notif_unread = 0
        try:
            self.shell._bell.itemconfig(self.shell._bell_dot, state="hidden")
        except tk.TclError:
            pass

    def _bind_outside(self):
        try:
            self.winfo_toplevel().bind("<Button-1>",
                                       lambda e: self._maybe_close(e), add="+")
        except tk.TclError:
            pass

    def _maybe_close(self, e):
        w = e.widget
        if w is self or str(w).startswith(str(self)):
            return
        if w is self.shell._bell:
            return
        self.destroy()
        self.shell._notif_panel = None


if __name__ == "__main__":
    import login
    login.App().mainloop()