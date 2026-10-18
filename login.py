"""login.py - START HERE.  Run this file:   python login.py"""
import os
import re
import traceback
import tkinter as tk
from tkinter import font as tkfont, messagebox

from common import *
from home import HomePage
from about import AboutPage, GroundDetailPage
from events import EventsPage
from event_detail import EventDetailPage
from reservation import ReservationPage
from feedback import FeedbackPage
from data import sample_events
from admin_shell import AdminShell
from my_bookings import MyBookingsPage
from user_profile import UserProfilePage
from db import create_user, check_login

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthDialog(tk.Toplevel):
    SIZES = {"user": (420, 560), "admin": (420, 460), "signup": (420, 560)}

    def __init__(self, app, mode):
        super().__init__(app)
        self.app, self.mode = app, mode
        self.title("Admin Login" if mode == "admin" else "PlayZone")
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(app)

        w, h = self.SIZES[mode]
        x = app.winfo_rootx() + (app.winfo_width() - w) // 2
        y = app.winfo_rooty() + (app.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

        fam = app.family
        f_title = tkfont.Font(family=fam, size=-24, weight="bold")
        f_sub = tkfont.Font(family=fam, size=-14)
        f_input = tkfont.Font(family=fam, size=-15)
        f_err = tkfont.Font(family=fam, size=-11)
        f_btn = tkfont.Font(family=fam, size=-15)
        f_small = tkfont.Font(family=fam, size=-14)
        self._fonts = (f_title, f_sub, f_input, f_err, f_btn, f_small)

        if mode == "admin":
            tk.Label(self, text="Admin Login", font=f_title, fg=BLUE,
                     bg=WHITE).pack(pady=(30, 0))
            tk.Label(self, text="Sign in with your admin account", font=f_sub,
                     fg=SLATE, bg=WHITE).pack(pady=(2, 20))
        else:
            tk.Label(self, text="Welcome to PlayZone", font=f_title, fg=BLUE,
                     bg=WHITE).pack(pady=(30, 0))
            tk.Label(self, text="Please enter your details", font=f_sub,
                     fg=SLATE, bg=WHITE).pack(pady=(2, 20))

        self.name = self.email = self.password = None
        self.name_err = self.email_err = self.password_err = None
        if mode in ("user", "signup"):
            self.name, self.name_err = self._field("Enter Your Name", f_input, f_err)
        self.email, self.email_err = self._field("Enter your email", f_input, f_err)
        self.password, self.password_err = self._field("Password", f_input, f_err, password=True)

        main_text = "Sign up" if mode == "signup" else "Login"
        RoundedButton(self, main_text, self.submit, 340, 40, radius=18,
                      bg=PURPLE, hover=PURPLE_DARK, fg=WHITE,
                      font=f_btn).pack(pady=(10, 8))

        if mode != "signup":
            RoundedButton(self, "Forgot Password", self.forgot, 340, 36,
                          radius=10, bg=WHITE, hover="#f5f3ff", fg=GHOST_TEXT,
                          outline=GHOST_BORDER, font=f_btn).pack(pady=(0, 10))

        if mode == "user":
            self._switch_row("Don't have an account? ", "Sign up", "signup", f_small)
        elif mode == "signup":
            self._switch_row("Already have an account? ", "Login", "user", f_small)

        self.bind("<Return>", lambda e: self.submit())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        try:
            self.grab_set()
        except tk.TclError:
            pass
        first = self.name or self.email
        first.entry.focus_set()

    def _field(self, placeholder, font, err_font, password=False):
        wrap = tk.Frame(self, bg=WHITE)
        wrap.pack(pady=5)
        entry = RoundedEntry(wrap, placeholder, width=340, password=password, font=font)
        entry.pack()
        err = tk.Label(wrap, text="", font=err_font, fg="#dc2626", bg=WHITE,
                       anchor="w", justify="left")
        err.pack(fill="x", padx=4, pady=(2, 0))
        return entry, err

    def _switch_row(self, text, link, target, font):
        row = tk.Frame(self, bg=WHITE)
        row.pack(pady=(4, 0))
        tk.Label(row, text=text, font=font, bg=WHITE, fg="black").pack(side="left")
        lbl = tk.Label(row, text=link, font=font, bg=WHITE, fg=PURPLE_LINK, cursor="hand2")
        lbl.pack(side="left")
        lbl.bind("<Button-1>", lambda e: self._switch(target))

    def _switch(self, target):
        self.destroy()
        AuthDialog(self.app, target)

    def forgot(self):
        self.destroy()
        ForgotPasswordDialog(self.app)

    def _check(self, entry, err_label, message, ok):
        if ok:
            entry.clear_error()
            err_label.config(text="")
        else:
            entry.set_error()
            err_label.config(text=message)
        return ok

    def submit(self):
        ok = True
        if self.name is not None:
            name_val = self.name.get()
            ok &= self._check(self.name, self.name_err, "Please enter your name.", bool(name_val))

        email_val = self.email.get()
        if not email_val:
            ok &= self._check(self.email, self.email_err, "Please enter your email.", False)
        else:
            ok &= self._check(self.email, self.email_err, "Please enter a valid email address.",
                              bool(EMAIL_RE.match(email_val)))

        pw_val = self.password.get()
        if not pw_val:
            ok &= self._check(self.password, self.password_err, "Please enter your password.", False)
        elif self.mode == "signup" and len(pw_val) < 6:
            ok &= self._check(self.password, self.password_err, "Password must be at least 6 characters.", False)
        else:
            ok &= self._check(self.password, self.password_err, "", True)

        if not ok:
            return

        if self.mode == "signup":
            ok_saved, msg = create_user(
                name=self.name.get(), email=email_val, password=pw_val)
            if not ok_saved:
                messagebox.showerror("Sign up failed", msg, parent=self)
                return

        data = {"email": email_val, "password": pw_val}
        if self.name is not None:
            data["name"] = self.name.get()
        self.app.handle_auth(self.mode, data)
        self.destroy()


class ForgotPasswordDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Reset Password")
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(app)

        w, h = 420, 300
        x = app.winfo_rootx() + (app.winfo_width() - w) // 2
        y = app.winfo_rooty() + (app.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

        fam = app.family
        f_title = tkfont.Font(family=fam, size=-22, weight="bold")
        f_sub = tkfont.Font(family=fam, size=-13)
        f_input = tkfont.Font(family=fam, size=-15)
        f_err = tkfont.Font(family=fam, size=-11)
        f_btn = tkfont.Font(family=fam, size=-15)
        self._fonts = (f_title, f_sub, f_input, f_err, f_btn)

        tk.Label(self, text="Reset your password", font=f_title, fg=BLUE, bg=WHITE).pack(pady=(30, 0))
        tk.Label(self, text="Enter your email and we'll send you a reset link.",
                 font=f_sub, fg=SLATE, bg=WHITE, wraplength=350, justify="center").pack(pady=(4, 20))

        wrap = tk.Frame(self, bg=WHITE)
        wrap.pack()
        self.email = RoundedEntry(wrap, "Enter your email", width=340, font=f_input)
        self.email.pack()
        self.email_err = tk.Label(wrap, text="", font=f_err, fg="#dc2626", bg=WHITE, anchor="w", justify="left")
        self.email_err.pack(fill="x", padx=4, pady=(2, 0))

        RoundedButton(self, "Send Reset Link", self.submit, 340, 40, radius=18,
                      bg=PURPLE, hover=PURPLE_DARK, fg=WHITE, font=f_btn).pack(pady=(18, 8))
        RoundedButton(self, "Back to Login", self.back, 340, 36, radius=10,
                      bg=WHITE, hover="#f5f3ff", fg=GHOST_TEXT, outline=GHOST_BORDER, font=f_btn).pack()

        self.bind("<Return>", lambda e: self.submit())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        try:
            self.grab_set()
        except tk.TclError:
            pass
        self.email.entry.focus_set()

    def back(self):
        self.destroy()
        AuthDialog(self.app, "user")

    def submit(self):
        val = self.email.get()
        if not val:
            self.email.set_error()
            self.email_err.config(text="Please enter your email.")
            return
        if not EMAIL_RE.match(val):
            self.email.set_error()
            self.email_err.config(text="Please enter a valid email address.")
            return
        self.email.clear_error()
        self.email_err.config(text="")
        print("[password reset requested]", val)
        messagebox.showinfo(
            "Check your email",
            "If an account exists for that email, a reset link is on its way.",
            parent=self)
        self.destroy()


class StartPage(BasePage):
    BASE = {"title": 72, "sub": 32, "body": 17, "start": 26}

    def __init__(self, app):
        super().__init__(app)
        fam = app.family
        self.fonts = {
            "title": tkfont.Font(family=fam, size=-72, weight="bold"),
            "sub": tkfont.Font(family=fam, size=-32, weight="bold"),
            "body": tkfont.Font(family=fam, size=-17),
            "start": tkfont.Font(family=fam, size=-26),
        }
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_content()

        self._after = None
        self.bind("<Configure>", self._on_configure)
        self.after(80, self._relayout)

    def on_show(self, **kwargs):
        self.after(60, self._relayout)

    def _build_header(self):
        app = self.app
        header = tk.Frame(self, bg=WHITE)
        header.grid(row=0, column=0, sticky="ew", padx=(60, 60), pady=(22, 0))
        brand = tk.Frame(header, bg=WHITE)
        brand.pack(side="left")
        LogoMark(brand, 40).pack(side="left")
        text = tk.Frame(brand, bg=WHITE)
        text.pack(side="left", padx=(12, 0))
        tk.Label(text, text="PLAY ZONE", font=app.f_brand, fg=NAVY, bg=WHITE).pack(anchor="w")
        tk.Label(text, text="BOOK. PLAY. ENJOY.", font=app.f_tag, fg=GREEN, bg=WHITE).pack(anchor="w")

    def _build_content(self):
        app = self.app
        content = tk.Frame(self, bg=WHITE)
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1, uniform="col")
        content.grid_columnconfigure(1, weight=1, uniform="col")

        left = tk.Frame(content, bg=WHITE)
        left.grid(row=0, column=0, sticky="w", padx=(70, 10))

        Pill(left, "CAMPUS RECREATION PORTAL", app.f_badge, BLUE, BLUE_SOFT).pack(anchor="w")
        tk.Label(left, text="PLAY ZONE", font=self.fonts["title"], fg=NAVY, bg=WHITE).pack(anchor="w", pady=(6, 0))
        tk.Label(left, text="Your Space. Your Game. Your Time.", font=self.fonts["sub"], fg=BLUE, bg=WHITE).pack(anchor="w")

        self.para = tk.Label(
            left, justify="left", anchor="w", font=self.fonts["body"], fg=SLATE, bg=WHITE, wraplength=560,
            text=("Reserve college sports grounds, discover upcoming tournaments, and coordinate "
                  "instantly with your teammates. Elevate your physical training and make the "
                  "absolute most of your time on the field."))
        self.para.pack(anchor="w", pady=(26, 0))

        tk.Label(left, text="Lets get started", font=self.fonts["start"], fg=SLATE, bg=WHITE).pack(anchor="w", pady=(26, 0))

        btns = tk.Frame(left, bg=WHITE)
        btns.pack(anchor="w", pady=(24, 0))
        RoundedButton(btns, "Sign up", lambda: AuthDialog(app, "signup"), 108, 46, radius=8,
                      bg=BLUE, hover=BLUE_DARK, fg=WHITE, font=app.f_btn).pack(side="left")
        RoundedButton(btns, "Login", lambda: AuthDialog(app, "user"), 92, 46, radius=8,
                      bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE, font=app.f_btn).pack(side="left", padx=(12, 0))

        admin = tk.Frame(left, bg=WHITE)
        admin.pack(anchor="w", pady=(28, 0))
        tk.Label(admin, text="If you are admin - ", font=app.f_link, fg="black", bg=WHITE).pack(side="left")
        link = tk.Label(admin, text="Login here!", font=app.f_link, fg=BLUE, bg=WHITE, cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: AuthDialog(app, "admin"))

        self.hero = HeroImage(content)
        self.hero.grid(row=0, column=1, padx=(10, 80))

    def _on_configure(self, event):
        if event.widget is not self:
            return
        if self._after:
            self.after_cancel(self._after)
        self._after = self.after(60, self._relayout)

    def _relayout(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 50:
            return
        s = clamp(w / 1480, 0.6, 1.25)
        for key, base in self.BASE.items():
            self.fonts[key].configure(size=-max(11, round(base * s)))

        self.para.config(wraplength=int(max(300, min(w * 0.44, w * 0.5 - 110))))

        hero_w = w * 0.5 - 100
        hero_h = hero_w * HeroImage.RATIO
        avail_h = h - 110
        if hero_h > avail_h:
            hero_h = avail_h
            hero_w = hero_h / HeroImage.RATIO
        self.hero.render(hero_w, hero_h)


PAGES = {
    "start":         (StartPage,        "PlayZone"),
    "home":          (HomePage,         "PlayZone - Home"),
    "about":         (AboutPage,        "PlayZone - About Us"),
    "events":        (EventsPage,       "PlayZone - Events"),
    "event_detail":  (EventDetailPage,  "PlayZone - Event Details"),
    "reservation":   (ReservationPage,  "PlayZone - Reservation"),
    "feedback":      (FeedbackPage,     "PlayZone - Feedback"),
    "ground_detail": (GroundDetailPage, "PlayZone - Ground Details"),
    "admin":         (AdminShell,       "PlayZone - Admin"),
    "my_bookings":   (MyBookingsPage,   "PlayZone - My Bookings"),
    "profile":       (UserProfilePage,  "PlayZone - My Profile"),
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self._safe_close)

        self.configure(bg=WHITE)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(1480, sw - 80), min(727, sh - 120)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - 20)}")
        self.minsize(900, 560)

        icon = make_app_icon(self)
        if icon:
            try:
                self.iconphoto(True, icon)
            except tk.TclError:
                pass

        self.family = pick_font(self)
        self.f_btn = tkfont.Font(family=self.family, size=-14, weight="bold")
        self.f_link = tkfont.Font(family=self.family, size=-14)
        self.f_badge = tkfont.Font(family=self.family, size=-10, weight="bold")
        self.f_brand = tkfont.Font(family=self.family, size=-17, weight="bold")
        self.f_tag = tkfont.Font(family=self.family, size=-9, weight="bold")

        self.user = None
        self.role = None
        self.events = sample_events()
        self._notif_unread = 0

        try:
            from db import init_db
            init_db()
        except Exception as exc:
            print("[db] init skipped:", exc)

        from admin_data import seed_sample_reservations, ensure_admin
        ensure_admin(self)
        seed_sample_reservations(self)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._pages, self.current = {}, None
        self.show_page("start")

    def _safe_close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        for w in list(self.winfo_children()):
            try:
                if isinstance(w, tk.Toplevel):
                    w.grab_release()
                    w.destroy()
            except tk.TclError:
                pass
        try:
            from db import get_conn
            c = get_conn()
            if c is not None:
                c.close()
        except Exception:
            pass
        try:
            self.quit()
        except tk.TclError:
            pass
        try:
            self.destroy()
        except tk.TclError:
            pass

    def show_page(self, name, **kwargs):
        page_cls, title = PAGES[name]
        previous = self.current
        try:
            safe_destroy_all_grabs(self)
            if name not in self._pages:
                self._pages[name] = page_cls(self)
            if previous and previous != name:
                self._pages[previous].grid_remove()
            page = self._pages[name]
            page.grid(row=0, column=0, sticky="nsew")
            self.current = name
            self.title(title)
            page.on_show(**kwargs)
        except Exception as exc:
            self._page_failed(name, previous, exc)

    def _page_failed(self, name, previous, exc):
        traceback.print_exc()
        bad = self._pages.pop(name, None)
        if bad is not None:
            bad.grid_remove()
            bad.destroy()
        if previous and previous in self._pages:
            self._pages[previous].grid(row=0, column=0, sticky="nsew")
            self.current = previous
            self.title(PAGES[previous][1])
        self._show_error(f'The "{name}" page could not be opened.', exc)

    def _show_error(self, headline, exc):
        frames = traceback.extract_tb(exc.__traceback__)
        where = (f"\n\nFile: {os.path.basename(frames[-1].filename)}, line {frames[-1].lineno}") if frames else ""
        messagebox.showerror(
            "Something went wrong",
            f"{headline}\n\n{type(exc).__name__}: {exc}{where}\n\n"
            "(Send this message to your helper. The full details are in the terminal.)")

    def report_callback_exception(self, exc_type, exc, tb):
        traceback.print_exception(exc_type, exc, tb)
        if not getattr(self, "_showing_error", False):
            self._showing_error = True
            try:
                self._show_error("A button or step failed.", exc)
            finally:
                self._showing_error = False

    def navigate(self, name, section=None, **kwargs):
        if name not in PAGES:
            messagebox.showinfo("Coming soon", f'The "{name}" page has not been built yet.')
            return
        self.show_page(name, **kwargs)
        if section:
            self._pages[name].scroll_to(section)

    def handle_auth(self, mode, data):
        print(f"[{mode}]", data)

        if mode == "admin":
            from admin_data import admin_credentials_ok, ensure_admin
            ensure_admin(self)
            if not admin_credentials_ok(data["email"], data["password"]):
                messagebox.showerror("Wrong credentials", "That admin email or password is not correct.")
                return
            self.user = data
            self.role = "admin"
            self.show_page("admin")
            return

        if mode == "signup":
            self.user = {"email": data["email"], "name": data.get("name", "")}
            self.role = "user"
            self.show_page("home")
            return

        try:
            found = check_login(data["email"], data["password"])
        except Exception as exc:
            print("[login] check_login failed:", exc)
            found = None

        if not found:
            messagebox.showerror("Wrong credentials", "That email or password is not registered.")
            return

        self.user = {"email": found.get("email", ""), "name": found.get("name", "")}
        self.role = "user"
        self.show_page("home")

    def logout(self):
        self.user = self.role = None
        self.show_page("start")


if __name__ == "__main__":
    App().mainloop()