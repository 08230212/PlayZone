"""email_service.py - sends notification emails when the admin acts on a booking.

Two modes:
    "demo"  -> no real email. Prints to terminal + shows a custom popup.
    "gmail" -> real email via Gmail SMTP (needs app password).
"""
import smtplib
import tkinter as tk
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tkinter import font as tkfont

from common import (
    WHITE, NAVY, BLUE, BLUE_DARK, SLATE, SOFT_BG,
    WideButton
)


# --------------------------------------------------------------- settings ---
EMAIL_MODE = "demo"        # "demo" or "gmail"

GMAIL_USER = "your.address@gmail.com"
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"

SENDER_NAME = "PlayZone Sports Office"


# ---------------------------------------------------------- email body ----
def _subject_for(status):
    if status == "Confirmed":
        return "Your PlayZone booking is confirmed"
    if status == "Cancelled":
        return "Your PlayZone booking has been cancelled"
    return "Update on your PlayZone booking"


def _body_for(booking, status):
    ground = booking.get("ground", "the ground")
    date = booking.get("date", "")
    time = booking.get("time", "")
    name = booking.get("name", "student")

    if hasattr(date, "day"):
        date_str = f"{date.day} {date.strftime('%b %Y')}"
    else:
        date_str = str(date)

    if status == "Confirmed":
        action = "has been APPROVED by the sports office"
        next_step = ("Please arrive about 10 minutes before your slot and "
                     "bring your student ID card.")
    elif status == "Cancelled":
        action = "has been CANCELLED by the sports office"
        next_step = ("If this is unexpected, please contact the sports office "
                     "directly.")
    else:
        action = "has been updated"
        next_step = ""

    return (
        f"Hi {name},\n\n"
        f"Your booking for {ground} on {date_str} ({time}) {action}.\n\n"
        f"{next_step}\n\n"
        f"Booking reference: {booking.get('id', '')}\n\n"
        f"— {SENDER_NAME}\n"
        f"PlayZone · Campus Recreation Portal"
    )


# ---------------------------------------------------------- custom popup ---
class NotificationPopup(tk.Toplevel):
    """A custom modal that matches the PlayZone design."""
    def __init__(self, app, to_address, subject):
        super().__init__(app)
        self.title("Notification sent")
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(app)

        w, h = 440, 280
        x = app.winfo_rootx() + (app.winfo_width() - w) // 2
        y = app.winfo_rooty() + (app.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

        fam = app.family
        f_title = tkfont.Font(family=fam, size=-20, weight="bold")
        f_body = tkfont.Font(family=fam, size=-14)
        f_small = tkfont.Font(family=fam, size=-12)
        self._fonts = (f_title, f_body, f_small)

        card = tk.Frame(self, bg=WHITE, padx=30, pady=28)
        card.pack(fill="both", expand=True)

        icon = tk.Canvas(card, width=48, height=48, bg=WHITE, highlightthickness=0)
        icon.create_oval(0, 0, 48, 48, fill=BLUE, outline=BLUE)
        icon.create_rectangle(14, 16, 34, 32, outline=WHITE, width=2)
        icon.create_line(14, 16, 24, 24, 34, 16, fill=WHITE, width=2)
        icon.pack(pady=(0, 16))

        tk.Label(card, text="Notification Sent", font=f_title, fg=NAVY,
                 bg=WHITE).pack()
        tk.Label(card, text=f"To: {to_address}", font=f_body,
                 fg=SLATE, bg=WHITE, wraplength=340, justify="center").pack(pady=(8, 0))

        subj_frame = tk.Frame(card, bg=SOFT_BG, padx=12, pady=8)
        subj_frame.pack(fill="x", pady=(16, 20))
        tk.Label(subj_frame, text=subject, font=f_small, fg=NAVY,
                 bg=SOFT_BG, wraplength=320, justify="center").pack()

        WideButton(card, "OK", self.destroy, height=44, radius=8,
                   bg=BLUE, hover=BLUE_DARK, fg=WHITE, font=f_body,
                   parent_bg=WHITE).pack(fill="x")

        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()

        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass


# ---------------------------------------------------------- the send -------
def send_email(app_window, to_address, subject, body):
    """Send (or pretend to send) an email."""
    if not to_address:
        return False

    # ---- demo mode: print + custom popup ----
    if EMAIL_MODE == "demo":
        print("\n----- [email demo] -----")
        print("To:     ", to_address)
        print("Subject:", subject)
        print("Body:\n" + body)
        print("----- [/email demo] ----\n")

        try:
            NotificationPopup(app_window, to_address, subject)
        except Exception as e:
            print("[email] popup failed:", e)
        return True

    # ---- gmail mode: real send ----
    try:
        msg = MIMEMultipart()
        msg["From"] = f"{SENDER_NAME} <{GMAIL_USER}>"
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as s:
            s.starttls()
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.send_message(msg)
        print(f"[email] sent to {to_address}")

        try:
            NotificationPopup(app_window, to_address, subject)
        except Exception as e:
            print("[email] popup failed:", e)
        return True

    except Exception as exc:
        print(f"[email] failed to send to {to_address}: {exc}")
        return False


def notify_booking_status(app_window, booking, status):
    """Build the subject + body from a booking dict and send it.
    Wrapped so a broken email never crashes the admin UI."""
    try:
        return send_email(
            app_window,
            booking.get("email", ""),
            _subject_for(status),
            _body_for(booking, status),
        )
    except Exception as exc:
        print("[email] notify_booking_status failed:", exc)
        return False