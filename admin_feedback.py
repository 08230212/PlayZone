"""admin_feedback.py - the admin Feedback screen + Feedback Detail modal."""
import tkinter as tk

from common import *
from reservation import RoundedPopup
from admin_shell import AdminPage, PAGE_BG
from admin_data import all_feedback, mark_feedback_read


STATUS_COLORS = {
    "Read":   ("#059669", "#dcfce7"),
    "Unread": ("#d97706", "#fef3c7"),
}


class FeedbackPage(AdminPage):
    def build(self):
        self.filter_status = "All Feedback"

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
        head.pack(fill="x", pady=(0, 18))
        head.grid_columnconfigure(0, weight=1)
        tk.Label(head, text="Feedback", font=self.f["h1"], fg=NAVY,
                 bg=PAGE_BG).grid(row=0, column=0, sticky="w")

        right = tk.Frame(head, bg=PAGE_BG)
        right.grid(row=0, column=1, sticky="e")
        self.search = RoundedEntry(right, "Search by user or message...",
                                   width=240, height=36, font=self.f["small"],
                                   parent_bg=PAGE_BG)
        self.search.pack(side="left", padx=(0, 10))
        self.search.var.trace_add("write", lambda *a: self._render_table())

        self._dropdown(right, "Status: All Feedback",
                       ["All Feedback", "Read", "Unread"],
                       lambda v: self._set_status(v))

    def _set_status(self, v):
        self.filter_status = v
        self._render_table()

    def _dropdown(self, parent, label, options, on_pick):
        box = tk.Canvas(parent, width=190, height=36, bg=PAGE_BG,
                        highlightthickness=0, cursor="hand2")
        box.pack(side="left")
        round_rect(box, 1, 1, 189, 35, 10, fill=WHITE, outline="#e5e7eb")
        tid = box.create_text(14, 18, anchor="w", text=label,
                              font=self.f["small"], fill=NAVY)
        box.create_line(168, 15, 173, 20, 178, 15, fill=SLATE, width=2)

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

    def _render_table(self):
        for w in self._table_holder.winfo_children():
            w.destroy()

        q = self.search.get().lower() if hasattr(self, "search") else ""
        rows = []
        for i, f in enumerate(all_feedback()):
            if (self.filter_status != "All Feedback"
                    and f["status"] != self.filter_status):
                continue
            if q and (q not in f["user"].lower()
                      and q not in f["message"].lower()):
                continue
            rows.append((i, f))

        card = Card(self._table_holder, PAGE_BG, pad=0, border="#e5e7eb")
        card.pack(fill="both", expand=True)
        inner = card.inner

        title = tk.Frame(inner, bg=WHITE)
        title.pack(fill="x", padx=20, pady=(16, 10))
        tk.Label(title, text="Student Reviews and Ratings", font=self.f["h2"],
                 fg=NAVY, bg=WHITE).pack(side="left")

        cols = ["User Name", "Message Preview", "Date", "Status", "Rating",
                "Detail"]
        weights = [2, 5, 2, 1, 1, 1]
        head = tk.Frame(inner, bg="#f8fafc")
        head.pack(fill="x")
        for i, (c, w) in enumerate(zip(cols, weights)):
            head.grid_columnconfigure(i, weight=w, uniform="fb")
            tk.Label(head, text=c, font=self.f["cap"], fg=SLATE,
                     bg="#f8fafc", anchor="w").grid(
                         row=0, column=i, sticky="ew", padx=16, pady=10)

        if not rows:
            tk.Label(inner, text="No feedback matches your filters.",
                     font=self.f["p"], fg=SLATE, bg=WHITE).pack(pady=40)
            return

        for idx, f in rows:
            row = tk.Frame(inner, bg=WHITE)
            row.pack(fill="x")
            for i, w in enumerate(weights):
                row.grid_columnconfigure(i, weight=w, uniform="fb")

            tk.Label(row, text=f["user"], font=self.f["small"], fg=NAVY,
                     bg=WHITE, anchor="w").grid(row=0, column=0, sticky="ew",
                                                padx=16, pady=12)
            preview = f["message"][:55] + ("…" if len(f["message"]) > 55 else "")
            tk.Label(row, text=preview, font=self.f["small"], fg=SLATE,
                     bg=WHITE, anchor="w").grid(row=0, column=1, sticky="ew",
                                                padx=16, pady=12)
            tk.Label(row, text=f["date"], font=self.f["small"], fg=SLATE,
                     bg=WHITE, anchor="w").grid(row=0, column=2, sticky="ew",
                                                padx=16, pady=12)
            fg, bg = STATUS_COLORS.get(f["status"], (SLATE, "#f1f5f9"))
            Pill(row, f["status"], self.f["small"], fg, bg, parent_bg=WHITE,
                 padx=10, pady=4).grid(row=0, column=3, sticky="w", padx=16)
            tk.Label(row, text=str(f["rating"]), font=self.f["small"], fg=NAVY,
                     bg=WHITE).grid(row=0, column=4, sticky="w", padx=16)
            view = tk.Label(row, text="View", font=self.f["small"], fg=BLUE,
                            bg=WHITE, cursor="hand2")
            view.grid(row=0, column=5, sticky="w", padx=16)
            view.bind("<Button-1>",
                      lambda e, i=idx: self._open_detail(i))
            tk.Frame(inner, bg="#f1f5f9", height=1).pack(fill="x")

        foot = tk.Frame(inner, bg=WHITE)
        foot.pack(fill="x", padx=16, pady=12)
        tk.Label(foot, text=f"Showing {len(rows)} review"
                            f"{'s' if len(rows) != 1 else ''}",
                 font=self.f["small"], fg=SLATE,
                 bg=WHITE).pack(side="left")

    def _open_detail(self, index):
        """Wrap the modal in a try/except so a failure inside it can never
        leave the app holding a grab and frozen."""
        try:
            FeedbackDetailDialog(self, index)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            for w in self.app.winfo_children():
                try:
                    if isinstance(w, tk.Toplevel):
                        w.grab_release()
                        w.destroy()
                except tk.TclError:
                    pass
            try:
                self.app.grab_release()
            except tk.TclError:
                pass
            from tkinter import messagebox
            messagebox.showerror("Feedback Detail failed",
                                 f"{type(exc).__name__}: {exc}")


# ------------------------------------------------------ Feedback Detail modal
class FeedbackDetailDialog(RoundedPopup):
    def __init__(self, page, index):
        super().__init__(page.app, 420)
        self.page, self.index = page, index
        fb = all_feedback()[index]

        f_title = self.F(22, True)
        f_cap   = self.F(10, True)
        f_val   = self.F(15, True)
        f_sub   = self.F(13)
        f_msg   = self.F(14)
        f_btn   = self.F(14, True)

        # visible close button (overrideredirect windows have no title bar)
        close_btn = tk.Label(self.card, text="✕", font=f_btn, fg="#94a3b8",
                             bg=WHITE, cursor="hand2", padx=8, pady=2)
        close_btn.place(relx=1.0, x=-8, y=8, anchor="ne")
        close_btn.lift()
        close_btn.bind("<Button-1>", lambda e: self.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#dc2626"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#94a3b8"))

        tk.Label(self.body, text="Feedback Detail", font=f_title, fg=NAVY,
                 bg=WHITE).pack(anchor="w")

        head = tk.Frame(self.body, bg=WHITE)
        head.pack(fill="x", pady=(14, 6))
        av = tk.Canvas(head, width=48, height=48, bg=WHITE,
                       highlightthickness=0)
        av.create_oval(0, 0, 48, 48, fill=BLUE_SOFT, outline=BLUE_SOFT)
        av.create_text(24, 26, text="👤", fill=BLUE, font=f_sub)
        av.pack(side="left")
        info = tk.Frame(head, bg=WHITE)
        info.pack(side="left", padx=(12, 0))
        tk.Label(info, text=fb["user"], font=f_val, fg=NAVY,
                 bg=WHITE).pack(anchor="w")
        tk.Label(info, text=fb.get("email", "student.sce@rub.edu.bt"),
                 font=f_sub, fg=SLATE, bg=WHITE).pack(anchor="w", pady=(2, 0))

        tk.Frame(self.body, bg="#e5e7eb", height=1).pack(fill="x",
                                                         pady=(14, 14))

        tk.Label(self.body, text="SUBMITTED ON", font=f_cap, fg=SLATE,
                 bg=WHITE).pack(anchor="w")
        tk.Label(self.body, text=f"{fb['date']} at 04:32 PM", font=f_val,
                 fg=NAVY, bg=WHITE).pack(anchor="w", pady=(2, 12))

        tk.Label(self.body, text="RATING REVIEW", font=f_cap, fg=SLATE,
                 bg=WHITE).pack(anchor="w")
        tk.Label(self.body, text=f"{fb['rating']} out of 5", font=f_val,
                 fg=BLUE, bg=WHITE).pack(anchor="w", pady=(2, 12))

        tk.Label(self.body, text="FULL FEEDBACK MESSAGE", font=f_cap, fg=SLATE,
                 bg=WHITE).pack(anchor="w")
        box = tk.Frame(self.body, bg="#f8fafc")
        box.pack(fill="x", pady=(6, 18))
        tk.Label(box, text=f"\"{fb['message']}\"", font=f_msg, fg=NAVY,
                 bg="#f8fafc", wraplength=self.fw - 30, justify="left",
                 anchor="w").pack(anchor="w", padx=14, pady=14)

        row = tk.Frame(self.body, bg=WHITE)
        row.pack(fill="x", pady=(0, 6))
        tk.Label(row, text="Mark as Resolved & Read", font=f_btn, fg=NAVY,
                 bg=WHITE).pack(side="left")
        self.read = tk.BooleanVar(value=fb["status"] == "Read")
        self.switch = tk.Canvas(row, width=44, height=24, bg=WHITE,
                                highlightthickness=0, cursor="hand2")
        self.switch.pack(side="right")
        self.switch.bind("<Button-1>", lambda e: self._toggle())
        self._draw_switch()

        # footer Close button (alternative to the ✕)
        btns = tk.Frame(self.body, bg=WHITE)
        btns.pack(fill="x", pady=(14, 0))
        WideButton(btns, "Close", self.destroy, height=40, radius=8,
                   bg=WHITE, hover=BLUE_SOFT, fg=BLUE, outline=BLUE,
                   font=f_btn).pack(fill="x")

        self.show()

    def _toggle(self):
        self.read.set(not self.read.get())
        self._draw_switch()
        if self.read.get():
            mark_feedback_read(self.index)
        else:
            all_feedback()[self.index]["status"] = "Unread"
        # Rebuild the table under the modal, but AFTER the current event
        # loop finishes - so we never rebuild widgets while a grab is held.
        page = self.page
        def refresh():
            try:
                if page.winfo_exists():
                    page._render_table()
            except tk.TclError:
                pass
        self.after(120, refresh)

    def _draw_switch(self):
        self.switch.delete("all")
        on = self.read.get()
        round_rect(self.switch, 1, 1, 43, 23, 12,
                   fill=BLUE if on else "#cbd5e1",
                   outline=BLUE if on else "#cbd5e1")
        cx = 32 if on else 12
        self.switch.create_oval(cx - 9, 3, cx + 9, 21, fill=WHITE,
                                outline=WHITE)