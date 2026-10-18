"""admin_account.py - the single admin's profile & settings page."""
import os
import shutil
import tkinter as tk
from tkinter import filedialog

from common import *
from admin_shell import AdminPage, PAGE_BG
from admin_data import (load_admin_profile, save_admin_profile,
                        change_password)


class AccountPage(AdminPage):
    def build(self):
        self.outer = tk.Frame(self, bg=PAGE_BG)
        self.outer.pack(fill="both", expand=True, padx=28, pady=24)

        head = tk.Frame(self.outer, bg=PAGE_BG)
        head.pack(fill="x", pady=(0, 22))
        tk.Label(head, text="Account", font=self.f["h1"], fg=NAVY,
                 bg=PAGE_BG).pack(anchor="w")
        tk.Label(head, text="Manage your profile and security settings.",
                 font=self.f["p"], fg=SLATE, bg=PAGE_BG).pack(anchor="w",
                                                              pady=(4, 0))

        row = tk.Frame(self.outer, bg=PAGE_BG)
        row.pack(fill="x", pady=(0, 18))
        row.grid_columnconfigure(0, weight=3, uniform="acc")
        row.grid_columnconfigure(1, weight=2, uniform="acc")

        self._profile_card(row)
        self._password_card(row)

        self._preferences_card()

    # ---------------------------------------------------------- profile
    def _profile_card(self, parent):
        p = load_admin_profile(self.app)

        card = Card(parent, PAGE_BG, pad=24, border="#e5e7eb")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        inner = card.inner

        tk.Label(inner, text="Profile", font=self.f["h2"], fg=NAVY,
                 bg=WHITE).pack(anchor="w")

        # ---------- avatar + upload/remove ----------
        top = tk.Frame(inner, bg=WHITE)
        top.pack(fill="x", pady=(16, 18))

        self._avatar_holder = tk.Frame(top, bg=WHITE)
        self._avatar_holder.pack(side="left", anchor="n")
        self._build_avatar()

        info = tk.Frame(top, bg=WHITE)
        info.pack(side="left", padx=(18, 0), anchor="nw")
        tk.Label(info, text="Profile photo", font=self.f["small"], fg=SLATE,
                 bg=WHITE).pack(anchor="w")
        tk.Label(info, text="PNG or JPG. Recommended 200×200.",
                 font=self.f["small"], fg=SLATE, bg=WHITE).pack(anchor="w",
                                                                pady=(2, 8))
        btn_row = tk.Frame(info, bg=WHITE)
        btn_row.pack(anchor="w")
        RoundedButton(btn_row, "Upload New", self._upload_avatar,
                      110, 34, radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                      font=self.f["btn"], parent_bg=WHITE).pack(side="left")
        RoundedButton(btn_row, "Remove", self._remove_avatar,
                      90, 34, radius=8, bg=WHITE, hover=BLUE_SOFT, fg=BLUE,
                      outline=BLUE, font=self.f["btn"], parent_bg=WHITE
                      ).pack(side="left", padx=(10, 0))

        # ---------- editable fields ----------
        grid = tk.Frame(inner, bg=WHITE)
        grid.pack(fill="x")
        grid.grid_columnconfigure(0, weight=1, uniform="pf")
        grid.grid_columnconfigure(1, weight=1, uniform="pf")

        self.in_name = self._field(grid, 0, 0, "Full Name", p.get("name", ""))
        self.in_email = self._field(grid, 0, 1, "Email Address",
                                    p.get("email", ""))
        self.in_phone = self._field(grid, 1, 0, "Phone", p.get("phone", ""))
        self._readonly(grid, 1, 1, "Role", p.get("role", "Super Admin"))
        self._readonly(grid, 2, 0, "Joined", p.get("joined", "05 Jan 2026"))

        WideButton(inner, "Save Changes", self._save_profile, height=42,
                   radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                   font=self.f["btn"]).pack(fill="x", pady=(14, 0))

    def _build_avatar(self):
        """Rebuild the avatar PhotoBox from the current profile.
        Fixed 90×90 square and circular mask."""
        for w in self._avatar_holder.winfo_children():
            w.destroy()
        p = load_admin_profile(self.app)
        filename = p.get("avatar") or "admin_avatar.jpg"
        PhotoBox(self._avatar_holder, filename, 90, radius=45,
                 bg=WHITE, tint=BLUE_SOFT, circular=True,
                 width=90).pack()

    # ---- avatar upload / remove ---------------------------------------------
    def _upload_avatar(self, _event=None):
        try:
            self.grab_release()
        except tk.TclError:
            pass

        path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title="Choose profile photo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                       ("All files", "*.*")])
        if not path:
            return

        base = os.path.basename(path)
        root, ext = os.path.splitext(base)
        target = f"admin_avatar{ext.lower()}"
        try:
            os.makedirs(ASSETS_DIR, exist_ok=True)
            dest = os.path.join(ASSETS_DIR, target)
            if os.path.abspath(path) != os.path.abspath(dest):
                shutil.copyfile(path, dest)
        except Exception as exc:
            PlayZoneDialog(self.winfo_toplevel(), "Error", f"Could not save photo: {exc}", type="error")
            return

        save_admin_profile(self.app, {"avatar": target})
        self._build_avatar()
        try:
            self.shell._refresh_user_chip()
        except tk.TclError:
            pass
        try:
            self.shell._refresh_avatar()
        except Exception:
            pass
        PlayZoneDialog(self.winfo_toplevel(), "Uploaded", "Admin photo updated successfully.", type="success")

    def _remove_avatar(self):
        p = load_admin_profile(self.app)
        current = p.get("avatar", "")
        if current and current not in ("", "admin_avatar.jpg"):
            try:
                os.remove(os.path.join(ASSETS_DIR, current))
            except OSError:
                pass
        save_admin_profile(self.app, {"avatar": ""})
        self._build_avatar()
        try:
            self.shell._refresh_user_chip()
        except tk.TclError:
            pass

    def _field(self, grid, r, c, label, value):
        tk.Label(grid, text=label, font=self.f["btn"], fg=NAVY, bg=WHITE
                 ).grid(row=r * 2, column=c, sticky="w",
                        padx=(0 if c == 0 else 8, 8 if c == 0 else 0),
                        pady=(0, 6))
        entry = RoundedEntry(grid, label, width=200, height=40,
                             font=self.f["small"])
        entry.var.set(value or "")
        entry.grid(row=r * 2 + 1, column=c, sticky="ew",
                   padx=(0 if c == 0 else 8, 8 if c == 0 else 0),
                   pady=(0, 12))
        return entry

    def _readonly(self, grid, r, c, label, value):
        tk.Label(grid, text=label, font=self.f["btn"], fg=NAVY, bg=WHITE
                 ).grid(row=r * 2, column=c, sticky="w",
                        padx=(0 if c == 0 else 8, 8 if c == 0 else 0),
                        pady=(0, 6))
        box = tk.Frame(grid, bg=SOFT_BG)
        box.grid(row=r * 2 + 1, column=c, sticky="ew",
                 padx=(0 if c == 0 else 8, 8 if c == 0 else 0),
                 pady=(0, 12))
        tk.Label(box, text=value or "", font=self.f["small"], fg=SLATE,
                 bg=SOFT_BG, anchor="w").pack(fill="x", padx=12, pady=11)

    def _save_profile(self):
        try:
            existing = load_admin_profile(self.app)
            save_admin_profile(self.app, {
                "name":  self.in_name.get() or existing.get("name", ""),
                "email": self.in_email.get() or existing.get("email", ""),
                "phone": self.in_phone.get() or existing.get("phone", ""),
            })
        except Exception as exc:
            PlayZoneDialog(self.winfo_toplevel(), "Error", f"{type(exc).__name__}: {exc}", type="error")
            return
        
        PlayZoneDialog(self.winfo_toplevel(), "Saved", "Your profile has been updated.", type="success")
        try:
            self.shell._refresh_user_chip()
        except tk.TclError:
            pass

    # -------------------------------------------------------- password
    def _password_card(self, parent):
        card = Card(parent, PAGE_BG, pad=24, border="#e5e7eb")
        card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        inner = card.inner

        tk.Label(inner, text="Change Password", font=self.f["h2"], fg=NAVY,
                 bg=WHITE).pack(anchor="w")
        tk.Label(inner, text="Use a strong password of at least 6 characters.",
                 font=self.f["small"], fg=SLATE, bg=WHITE).pack(anchor="w",
                                                                pady=(4, 12))

        self.pw_cur = self._pw_row(inner, "Current Password")
        self.pw_new = self._pw_row(inner, "New Password")
        self.pw_conf = self._pw_row(inner, "Confirm New Password")

        self.pw_err = tk.Label(inner, text="", font=self.f["small"],
                               fg="#dc2626", bg=WHITE, anchor="w")
        self.pw_err.pack(fill="x", pady=(4, 0))

        WideButton(inner, "Update Password", self._do_change_pw, height=42,
                   radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                   font=self.f["btn"]).pack(fill="x", pady=(14, 0))

    def _pw_row(self, parent, label):
        tk.Label(parent, text=label, font=self.f["btn"], fg=NAVY, bg=WHITE
                 ).pack(anchor="w", pady=(10, 6))
        e = RoundedEntry(parent, label, width=280, height=40,
                         font=self.f["small"], password=True)
        e.pack(fill="x")
        return e

    def _do_change_pw(self):
        try:
            msg = change_password(self.app,
                                  self.pw_cur.get(), self.pw_new.get(),
                                  self.pw_conf.get())
        except Exception as exc:
            self.pw_err.config(text=f"{type(exc).__name__}: {exc}")
            return
        if msg:
            self.pw_err.config(text=msg)
            return
        self.pw_err.config(text="")
        for e in (self.pw_cur, self.pw_new, self.pw_conf):
            e.var.set("")
        PlayZoneDialog(self.winfo_toplevel(), "Success", "Your admin password has been changed.", type="success")

    # ----------------------------------------------------- preferences
    def _preferences_card(self):
        p = load_admin_profile(self.app)

        card = Card(self.outer, PAGE_BG, pad=24, border="#e5e7eb")
        card.pack(fill="x", pady=(0, 18))
        inner = card.inner

        tk.Label(inner, text="Preferences", font=self.f["h2"], fg=NAVY,
                 bg=WHITE).pack(anchor="w")
        tk.Label(inner, text="Choose how Play Zone notifies you.",
                 font=self.f["small"], fg=SLATE, bg=WHITE).pack(anchor="w",
                                                                pady=(4, 12))

        self.pref_email = tk.BooleanVar(value=p.get("email_notify", True))
        self.pref_desktop = tk.BooleanVar(value=p.get("desktop_notify", True))
        self._toggle_row(inner, "Email me about new bookings", self.pref_email)
        self._toggle_row(inner, "Show desktop alerts for new feedback",
                         self.pref_desktop)

        WideButton(inner, "Save Preferences", self._save_prefs, height=42,
                   radius=8, bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                   font=self.f["btn"]).pack(fill="x", pady=(16, 0))

    def _toggle_row(self, parent, label, var):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", pady=(8, 0))
        tk.Label(row, text=label, font=self.f["btn"], fg=NAVY,
                 bg=WHITE).pack(side="left")
        cv = tk.Canvas(row, width=44, height=24, bg=WHITE,
                       highlightthickness=0, cursor="hand2")
        cv.pack(side="right")

        def draw():
            cv.delete("all")
            on = var.get()
            round_rect(cv, 1, 1, 43, 23, 12,
                       fill=BLUE if on else "#cbd5e1",
                       outline=BLUE if on else "#cbd5e1")
            cx = 32 if on else 12
            cv.create_oval(cx - 9, 3, cx + 9, 21, fill=WHITE, outline=WHITE)

        def toggle(_):
            var.set(not var.get())
            draw()

        cv.bind("<Button-1>", toggle)
        draw()

    def _save_prefs(self):
        try:
            save_admin_profile(self.app, {
                "email_notify": self.pref_email.get(),
                "desktop_notify": self.pref_desktop.get(),
            })
        except Exception as exc:
            PlayZoneDialog(self.winfo_toplevel(), "Error", f"{type(exc).__name__}: {exc}", type="error")
            return
        PlayZoneDialog(self.winfo_toplevel(), "Saved", "Preferences saved.", type="success")