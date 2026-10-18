"""user_profile.py - the user's profile and settings page."""
import os
import shutil
import tkinter as tk
from tkinter import filedialog
from tkinter import font as tkfont

from common import *
from about import PHONE, EMAIL

# Get database connection helper
def _db():
    try:
        from db import get_conn
        return get_conn()
    except Exception:
        return None


class UserProfilePage(SectionPage):
    def __init__(self, app):
        super().__init__(app, "profile")
        
        def F(size, bold=False):
            return tkfont.Font(family=app.family, size=-size,
                               weight="bold" if bold else "normal")
        self.f.update({"h3": F(20, True), "cap": F(10, True)})

        self._header()
        self.body_area = self.section(SOFT_BG, top=20, bottom=56)
        
        self.row = tk.Frame(self.body_area, bg=SOFT_BG)
        self.row.pack(fill="x")
        self.row.grid_columnconfigure(0, weight=3, uniform="acc")
        self.row.grid_columnconfigure(1, weight=2, uniform="acc")

        self._profile_card()
        self._password_card()
        self._footer()

    def on_show(self, **kwargs):
        super().on_show(**kwargs)
        self._load_data()
        # Update the navbar icon to reflect new name/avatar
        if hasattr(self, "profile_icon"):
            self.profile_icon._draw()

    def _header(self):
        body = self.section(WHITE, top=40, bottom=16)
        Pill(body, "MY ACCOUNT", self.app.f_badge, BLUE, BLUE_SOFT).pack(anchor="w")
        tk.Label(body, text="User Profile", font=self.f["h1"], fg=NAVY,
                 bg=WHITE).pack(anchor="w", pady=(8, 0))
        tk.Label(body, text="Manage your personal information and security settings.",
                 font=self.f["p"], fg=SLATE, bg=WHITE).pack(anchor="w", pady=(8, 0))

    def _load_data(self):
        """Fetch current user data from DB or App state safely."""
        user = getattr(self.app, "user", {}) or {}
        email = user.get("email", "")
        
        name = user.get("name", "Student")
        phone = ""
        student_id = ""
        
        conn = _db()
        if conn and email:
            try:
                row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
                if row:
                    # Safely handle potential NULLs from the DB
                    name = str(row["name"] or "")
                    phone = str(row["phone"] or "")
                    student_id = str(row["student_id"] or "")
            except Exception as e:
                print("[profile] DB load error:", e)

        self.in_name.var.set(name)
        self.in_email.var.set(email)
        self.in_phone.var.set(phone)
        self.in_id.var.set(student_id)
        
        self._build_avatar()

    def _profile_card(self):
        card = Card(self.row, SOFT_BG, pad=24, border="#e5e7eb")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        inner = card.inner

        tk.Label(inner, text="Profile Information", font=self.f["h2"], fg=NAVY,
                 bg=WHITE).pack(anchor="w")

        top = tk.Frame(inner, bg=WHITE)
        top.pack(fill="x", pady=(16, 18))
        
        self._avatar_holder = tk.Frame(top, bg=WHITE)
        self._avatar_holder.pack(side="left", anchor="n")
        
        info = tk.Frame(top, bg=WHITE)
        info.pack(side="left", padx=(18, 0), anchor="nw")
        tk.Label(info, text="Profile photo", font=self.f["small"], fg=SLATE, bg=WHITE).pack(anchor="w")
        tk.Label(info, text="PNG or JPG. Recommended 200×200.", font=self.f["small"], fg=SLATE, bg=WHITE).pack(anchor="w", pady=(2, 8))
        
        RoundedButton(info, "Upload New", self._upload_avatar, 110, 34, radius=8, 
                      bg=BLUE, hover=BLUE_DARK, fg=WHITE, font=self.f["btn"], parent_bg=WHITE).pack(anchor="w")

        grid = tk.Frame(inner, bg=WHITE)
        grid.pack(fill="x")
        grid.grid_columnconfigure(0, weight=1, uniform="pf")
        grid.grid_columnconfigure(1, weight=1, uniform="pf")

        self.in_name = self._field(grid, 0, 0, "Full Name")
        
        # Email: Read-only
        self.in_email = self._field(grid, 0, 1, "Email Address")
        self.in_email.set_readonly()
        
        self.in_phone = self._field(grid, 1, 0, "Phone Number")
        self.in_id = self._field(grid, 1, 1, "Student ID")

        WideButton(inner, "Save Changes", self._save_profile, height=42,
                   radius=8, bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                   font=self.f["btn"]).pack(fill="x", pady=(14, 0))

    def _build_avatar(self):
        for w in self._avatar_holder.winfo_children():
            w.destroy()
            
        email = self.app.user.get("email", "user")
        base_name = f"user_avatar_{email.split('@')[0]}"
        
        # Find whatever extension the user uploaded (.jpg, .png, etc)
        target = None
        for ext in (".jpg", ".png", ".jpeg", ".gif", ".bmp"):
            if os.path.exists(os.path.join(ASSETS_DIR, base_name + ext)):
                target = base_name + ext
                break
                
        if target:
            PhotoBox(self._avatar_holder, target, 90, radius=45, bg=WHITE, tint=BLUE_SOFT, circular=True, width=90).pack()
        else:
            # Fallback if no picture uploaded yet
            PhotoBox(self._avatar_holder, "user_avatar.jpg", 90, radius=45, bg=WHITE, tint=BLUE_SOFT, circular=True, width=90).pack()

    def _upload_avatar(self):
        path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(), title="Choose profile photo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if not path:
            return
        
        base = os.path.basename(path)
        root, ext = os.path.splitext(base)
        email = self.app.user.get("email", "user")
        
        # Standardize the name so we never get duplicates
        target = f"user_avatar_{email.split('@')[0]}{ext.lower()}"
        
        try:
            os.makedirs(ASSETS_DIR, exist_ok=True)
            
            # Delete old avatar if it exists
            for old_ext in (".jpg", ".png", ".jpeg", ".gif", ".bmp"):
                old_path = os.path.join(ASSETS_DIR, f"user_avatar_{email.split('@')[0]}{old_ext}")
                if os.path.exists(old_path) and old_path != os.path.join(ASSETS_DIR, target):
                    try:
                        os.remove(old_path)
                    except:
                        pass
                        
            dest = os.path.join(ASSETS_DIR, target)
            if os.path.abspath(path) != os.path.abspath(dest):
                shutil.copyfile(path, dest)
            
            # Rebuild both the big avatar and the navbar icon
            self._build_avatar()
            if hasattr(self, "profile_icon"):
                self.profile_icon._draw()
                
            PlayZoneDialog(self.winfo_toplevel(), "Uploaded", "Profile photo updated! (Save changes to keep)", type="success")
        except Exception as exc:
            PlayZoneDialog(self.winfo_toplevel(), "Error", f"Could not save photo: {exc}", type="error")

    def _field(self, grid, r, c, label):
        tk.Label(grid, text=label, font=self.f["btn"], fg=NAVY, bg=WHITE).grid(
            row=r * 2, column=c, sticky="w", padx=(0 if c == 0 else 8, 8 if c == 0 else 0), pady=(0, 6))
        
        entry = RoundedEntry(grid, label, width=200, height=40, font=self.f["small"])            
        entry.grid(row=r * 2 + 1, column=c, sticky="ew", 
                   padx=(0 if c == 0 else 8, 8 if c == 0 else 0), pady=(0, 12))
        return entry

    def _save_profile(self):
        name = self.in_name.get()
        phone = self.in_phone.get()
        student_id = self.in_id.get()
        
        if not name:
            PlayZoneDialog(self.winfo_toplevel(), "Missing", "Name cannot be empty.", type="warning")
            return

        email = self.app.user.get("email", "")
        conn = _db()
        if conn and email:
            try:
                conn.execute("UPDATE users SET name = ?, phone = ?, student_id = ? WHERE email = ?", (name, phone, student_id, email))
                conn.commit()
                self.app.user["name"] = name
                PlayZoneDialog(self.winfo_toplevel(), "Saved", "Profile updated successfully.", type="success")
                self.profile_icon._draw() # Update Navbar avatar initial
            except Exception as exc:
                PlayZoneDialog(self.winfo_toplevel(), "Error", f"Could not save: {exc}", type="error")
        else:
            PlayZoneDialog(self.winfo_toplevel(), "Error", "Database not available.", type="error")

    def _password_card(self):
        card = Card(self.row, SOFT_BG, pad=24, border="#e5e7eb")
        card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        inner = card.inner

        tk.Label(inner, text="Change Password", font=self.f["h2"], fg=NAVY, bg=WHITE).pack(anchor="w")
        tk.Label(inner, text="Use a strong password of at least 6 characters.", font=self.f["small"], fg=SLATE, bg=WHITE).pack(anchor="w", pady=(4, 12))

        self.pw_cur = self._pw_row(inner, "Current Password")
        self.pw_new = self._pw_row(inner, "New Password")
        self.pw_conf = self._pw_row(inner, "Confirm New Password")

        self.pw_err = tk.Label(inner, text="", font=self.f["small"], fg="#dc2626", bg=WHITE, anchor="w")
        self.pw_err.pack(fill="x", pady=(4, 0))

        WideButton(inner, "Update Password", self._do_change_pw, height=42,
                   radius=8, bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                   font=self.f["btn"]).pack(fill="x", pady=(14, 0))

    def _pw_row(self, parent, label):
        tk.Label(parent, text=label, font=self.f["btn"], fg=NAVY, bg=WHITE).pack(anchor="w", pady=(10, 6))
        e = RoundedEntry(parent, label, width=280, height=40, font=self.f["small"], password=True)
        e.pack(fill="x")
        return e

    def _do_change_pw(self):
        cur, new, conf = self.pw_cur.get(), self.pw_new.get(), self.pw_conf.get()
        email = self.app.user.get("email", "")

        if not cur or not new or not conf:
            self.pw_err.config(text="Please fill all fields.")
            return
        if len(new) < 6:
            self.pw_err.config(text="New password must be 6+ characters.")
            return
        if new != conf:
            self.pw_err.config(text="New passwords do not match.")
            return

        conn = _db()
        if conn and email:
            try:
                row = conn.execute("SELECT password FROM users WHERE email = ?", (email,)).fetchone()
                if not row or str(row["password"]) != cur:
                    self.pw_err.config(text="Current password is incorrect.")
                    return
                
                conn.execute("UPDATE users SET password = ? WHERE email = ?", (new, email))
                conn.commit()
                self.pw_err.config(text="")
                self.pw_cur.var.set("")
                self.pw_new.var.set("")
                self.pw_conf.var.set("")
                PlayZoneDialog(self.winfo_toplevel(), "Success", "Your password has been changed.", type="success")
            except Exception as exc:
                self.pw_err.config(text=str(exc))

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
        tk.Label(txt, text="PLAY ZONE", font=self.app.f_brand, fg=WHITE, bg=NAVY_DARK).pack(anchor="w")
        tk.Label(txt, text="BOOK. PLAY. ENJOY.", font=self.app.f_tag, fg=GREEN, bg=NAVY_DARK).pack(anchor="w")
        tk.Label(left, text="Your one-stop portal for booking campus sports\ngrounds and joining college events.",
                 font=self.f["foot"], fg="#94a3b8", bg=NAVY_DARK, justify="left").pack(anchor="w", pady=(12, 0))

        right = tk.Frame(top, bg=NAVY_DARK)
        tk.Label(right, text="CAMPUS CONTACT", font=self.f["tag"], fg=WHITE, bg=NAVY_DARK).pack(anchor="w")
        for glyph, value in (("☎", PHONE), ("✉", EMAIL)):
            row = tk.Frame(right, bg=NAVY_DARK)
            row.pack(anchor="w", pady=(10, 0))
            tk.Label(row, text=glyph, font=self.f["foot"], fg=BLUE, bg=NAVY_DARK).pack(side="left")
            tk.Label(row, text=value, font=self.f["foot"], fg="#94a3b8", bg=NAVY_DARK).pack(side="left", padx=(8, 0))
        self.reflow(top, [left, right], lambda w: 2 if w >= 700 else 1, sticky="nw")

        tk.Frame(body, bg="#1e293b", height=1).pack(fill="x", pady=(28, 12))
        bottom = tk.Frame(body, bg=NAVY_DARK)
        bottom.pack(fill="x")
        tk.Label(bottom, text=f"© 2026 Play Zone. All rights reserved.", font=self.f["small"], fg="#64748b", bg=NAVY_DARK).pack(side="left")

if __name__ == "__main__":
    import login
    login.App().mainloop()