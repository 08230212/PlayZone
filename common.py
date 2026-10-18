"""common.py - shared by login.py and home.py: colours, paths, helpers, reusable widgets."""
import os
import tkinter as tk
from tkinter import font as tkfont

try:
    from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageOps, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
HERO_IMG = os.path.join(ASSETS_DIR, "hero.jpg")
LOGO_IMG = os.path.join(ASSETS_DIR, "logo.png")

# ---- colours
WHITE = "#ffffff"
NAVY = "#1e293b"
BLUE = "#2563eb"
BLUE_DARK = "#1d4ed8"
BLUE_SOFT = "#dbeafe"
BLUE_HOVER = "#eff6ff"
SLATE = "#64748b"
GREEN = "#10b981"
PURPLE = "#b98af7"
PURPLE_DARK = "#a56ff0"
PURPLE_LINK = "#a855f7"
FIELD_FILL = "#fdf7fb"
FIELD_BORDER = "#111111"
PLACEHOLDER = "#9ca3af"
GHOST_BORDER = "#9a9ab5"
GHOST_TEXT = "#6b6b8d"
SOFT_BG = "#f8fafc"
NAVY_DARK = "#0f172a"
TINTS = ["#dbeafe", "#dcfce7", "#fef3c7", "#ede9fe"]
AMBER = "#f59e0b"


# ---- helpers
def pick_font(root):
    families = set(tkfont.families(root))
    for name in ("Poppins", "Segoe UI", "Helvetica Neue", "Arial"):
        if name in families:
            return name
    return "TkDefaultFont"


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1,
        x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2,
        x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2, x1, y2,
        x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


def bind_tree(widget, event, handler, add="+"):
    widget.bind(event, handler, add)
    for child in widget.winfo_children():
        bind_tree(child, event, handler, add)


def hover_card(card, normal_border="#e5e7eb", hover_border=BLUE, widget=None):
    if not hasattr(card, "_hover_handlers"):
        state = {"on": False}

        def apply(on):
            if state["on"] != on:
                state["on"] = on
                card.hover = on
                card.border = hover_border if on else normal_border
                card.redraw()

        def inside():
            try:
                x, y = card.winfo_pointerxy()
                left, top = card.winfo_rootx(), card.winfo_rooty()
                return (left <= x < left + card.winfo_width() and
                        top <= y < top + card.winfo_height())
            except tk.TclError:
                return False

        def on_enter(e):
            apply(True)

        def on_leave(e):
            def settle():
                try:
                    apply(inside())
                except tk.TclError:
                    pass
            card.after(30, settle)

        card._hover_handlers = (on_enter, on_leave)
    on_enter, on_leave = card._hover_handlers
    bind_tree(widget or card, "<Enter>", on_enter)
    bind_tree(widget or card, "<Leave>", on_leave)


def hover_label(label, normal, hover):
    label.bind("<Enter>", lambda e: label.config(fg=hover))
    label.bind("<Leave>", lambda e: label.config(fg=normal))


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in rgb)


def lerp_color(c1, c2, t):
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t,
                        b1 + (b2 - b1) * t))


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width, height, radius=10,
                 bg=BLUE, fg=WHITE, outline=None, hover=None, font=None,
                 parent_bg=WHITE):
        super().__init__(parent, width=width, height=height, bg=parent_bg,
                         highlightthickness=0, cursor="hand2")
        self._bg = bg
        self._hover = hover or bg
        self._command = command
        self._anim = None
        self._shape = round_rect(self, 1, 1, width - 1, height - 1, radius,
                                 fill=bg, outline=outline or bg, width=1)
        self._text_id = self.create_text(width / 2, height / 2, text=text,
                                         fill=fg, font=font)
        self.bind("<Enter>", lambda e: self._fade_to(self._hover))
        self.bind("<Leave>", lambda e: self._fade_to(self._bg))
        self.bind("<ButtonRelease-1>", lambda e: self._command())

    def _fade_to(self, target, steps=6, delay=12):
        if self._anim:
            self.after_cancel(self._anim)
            self._anim = None
        start = self.itemcget(self._shape, "fill")
        if start == target:
            return

        def step(i):
            self.itemconfig(self._shape,
                            fill=lerp_color(start, target, i / steps))
            self._anim = (self.after(delay, lambda: step(i + 1))
                          if i < steps else None)
        step(1)


class FilterChip(RoundedButton):
    def __init__(self, parent, text, command, font, active=False,
                 parent_bg=WHITE):
        w = font.measure(text) + 34
        super().__init__(parent, text, command, w, 34, radius=17,
                         bg=BLUE if active else WHITE,
                         hover=BLUE_DARK if active else BLUE_SOFT,
                         fg=WHITE if active else "#334155",
                         outline=BLUE if active else "#d1d5db",
                         font=font, parent_bg=parent_bg)

    def set_active(self, active):
        self._bg = BLUE if active else WHITE
        self._hover = BLUE_DARK if active else BLUE_SOFT
        self.itemconfig(self._shape, fill=self._bg,
                        outline=BLUE if active else "#d1d5db")
        self.itemconfig(self._text_id,
                        fill=WHITE if active else "#334155")


class Pill(tk.Canvas):
    def __init__(self, parent, text, font, fg, fill, parent_bg=WHITE,
                 padx=14, pady=6):
        tw = font.measure(text)
        th = font.metrics("linespace")
        w, h = tw + 2 * padx, th + 2 * pady
        super().__init__(parent, width=w, height=h, bg=parent_bg,
                         highlightthickness=0)
        round_rect(self, 1, 1, w - 1, h - 1, (h - 2) // 2, fill=fill,
                   outline=fill)
        self.create_text(w / 2, h / 2, text=text, font=font, fill=fg)


class LogoMark(tk.Canvas):
    def __init__(self, parent, size=40, parent_bg=WHITE):
        super().__init__(parent, width=size, height=size, bg=parent_bg,
                         highlightthickness=0)
        self._photo = None
        if PIL_OK and os.path.exists(LOGO_IMG):
            img = Image.open(LOGO_IMG).convert("RGBA").resize(
                (size, size), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            self.create_image(0, 0, image=self._photo, anchor="nw")
            return
        round_rect(self, 0, 0, size, size, 10, fill=BLUE, outline=BLUE)
        c, r = size / 2, size * 0.32
        self.create_oval(c - r, c - r, c + r, c + r, fill="#14532d",
                         outline=WHITE, width=2)
        r2 = size * 0.14
        self.create_oval(c - r2, c - r2, c + r2, c + r2, fill="#22c55e",
                         outline=WHITE)


class RoundedEntry(tk.Canvas):
    def __init__(self, parent, placeholder, width=320, height=44, radius=12,
                 password=False, font=None, parent_bg=WHITE):
        super().__init__(parent, width=width, height=height, bg=parent_bg,
                         highlightthickness=0)
        self._password = password
        self._error = False
        self._reveal = False
        self._eye_xy = (width - 20, height // 2)

        self._box = round_rect(self, 1, 1, width - 1, height - 1, radius,
                               fill=FIELD_FILL, outline=FIELD_BORDER, width=1)

        field_w = width - 32 - (28 if password else 0)

        self.var = tk.StringVar()
        self.entry = tk.Entry(self, bd=0, relief="flat", bg=FIELD_FILL,
                              fg="black", font=font, insertbackground="black",
                              highlightthickness=0, textvariable=self.var,
                              show="•" if password else "")
        self.create_window(16, height // 2, window=self.entry, anchor="w",
                           width=field_w)

        self.placeholder = tk.Label(self, text=placeholder, font=font,
                                    fg=PLACEHOLDER, bg=FIELD_FILL, anchor="w")
        self._ph_win = self.create_window(17, height // 2,
                                          window=self.placeholder, anchor="w",
                                          width=field_w - 2)
        self.placeholder.bind("<Button-1>", lambda e: self.entry.focus_set())

        self.var.trace_add("write", lambda *a: self._sync_placeholder())
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self.bind("<Button-1>", lambda e: self.entry.focus_set())
        self._sync_placeholder()

        if password:
            ex, ey = self._eye_xy
            self.create_rectangle(ex - 13, 3, ex + 13, height - 3,
                                  fill=FIELD_FILL, outline=FIELD_FILL,
                                  tags="eye_hit")
            self._draw_eye()
            for tag in ("eye_hit", "eye_icon"):
                self.tag_bind(tag, "<Button-1>",
                              lambda e: self._toggle_reveal())
                self.tag_bind(tag, "<Enter>",
                              lambda e: self.config(cursor="hand2"))
                self.tag_bind(tag, "<Leave>", lambda e: self.config(cursor=""))

    def _sync_placeholder(self):
        self.itemconfigure(self._ph_win,
                           state="hidden" if self.var.get() else "normal")
        self.clear_error()

    def _draw_eye(self):
        self.delete("eye_icon")
        cx, cy = self._eye_xy
        color = BLUE if self._reveal else SLATE
        if self._reveal:
            self.create_oval(cx - 9, cy - 5, cx + 9, cy + 5, outline=color,
                             width=1.6, tags="eye_icon")
            self.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill=color,
                             outline=color, tags="eye_icon")
        else:
            self.create_line(cx - 9, cy, cx - 4, cy + 4, cx + 4, cy + 4,
                             cx + 9, cy, smooth=True, fill=color, width=1.6,
                             tags="eye_icon")
            self.create_line(cx - 6, cy + 3, cx - 6, cy + 6, fill=color,
                             width=1.2, tags="eye_icon")
            self.create_line(cx + 6, cy + 3, cx + 6, cy + 6, fill=color,
                             width=1.2, tags="eye_icon")

    def _toggle_reveal(self):
        self._reveal = not self._reveal
        self.entry.config(show="" if self._reveal else "•")
        self._draw_eye()

    def _focus_in(self, _):
        if not self._error:
            self.itemconfig(self._box, outline=BLUE)

    def _focus_out(self, _):
        if not self._error:
            self.itemconfig(self._box, outline=FIELD_BORDER)

    def get(self):
        return self.var.get().strip()

    def set_error(self):
        self._error = True
        self.itemconfig(self._box, outline="#dc2626")

    def clear_error(self):
        if self._error:
            self._error = False
            focused = self.focus_get() is self.entry
            self.itemconfig(self._box,
                            outline=BLUE if focused else FIELD_BORDER)

    def set_readonly(self):
        """Makes the field read-only with a grey background."""
        self.entry.config(state="readonly", readonlybackground=SOFT_BG)
        self.itemconfig(self._box, fill=SOFT_BG, outline="#e5e7eb")
        self.placeholder.config(bg=SOFT_BG)


class FlexInput(tk.Frame):
    def __init__(self, parent, placeholder, font=None, parent_bg=WHITE,
                 multiline=False, height=40):
        super().__init__(parent, bg=FIELD_BORDER, highlightthickness=0)
        inner = tk.Frame(self, bg=FIELD_FILL)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        self._ph, self._showing_ph, self._multiline = placeholder, True, multiline
        if multiline:
            self.widget = tk.Text(inner, bd=0, bg=FIELD_FILL, fg=PLACEHOLDER,
                                  font=font, height=max(3, height // 22),
                                  wrap="word", insertbackground="black",
                                  highlightthickness=0, padx=12, pady=10)
            self.widget.pack(fill="both", expand=True)
            self.widget.insert("1.0", placeholder)
        else:
            self.widget = tk.Entry(inner, bd=0, bg=FIELD_FILL, fg=PLACEHOLDER,
                                   font=font, insertbackground="black",
                                   highlightthickness=0)
            self.widget.pack(fill="x", padx=12, pady=10)
            self.widget.insert(0, placeholder)
        self.widget.bind("<FocusIn>", self._focus_in)
        self.widget.bind("<FocusOut>", self._focus_out)

    def _clear(self):
        if self._multiline:
            self.widget.delete("1.0", "end")
        else:
            self.widget.delete(0, "end")

    def _insert_ph(self):
        if self._multiline:
            self.widget.insert("1.0", self._ph)
        else:
            self.widget.insert(0, self._ph)

    def _focus_in(self, _):
        if self._showing_ph:
            self._clear()
            self.widget.config(fg="black")
            self._showing_ph = False

    def _focus_out(self, _):
        if not self.get():
            self._showing_ph = True
            self.widget.config(fg=PLACEHOLDER)
            self._insert_ph()

    def get(self):
        if self._showing_ph:
            return ""
        text = (self.widget.get("1.0", "end") if self._multiline
                else self.widget.get())
        return text.strip()

    def reset(self):
        self._clear()
        self._showing_ph = True
        self.widget.config(fg=PLACEHOLDER)
        self._insert_ph()


class HeroImage(tk.Canvas):
    RATIO = 0.765

    def __init__(self, parent):
        super().__init__(parent, bg=WHITE, highlightthickness=0)
        self._src = None
        self._photo = None
        self._last = None
        if PIL_OK and os.path.exists(HERO_IMG):
            self._src = Image.open(HERO_IMG).convert("RGB")

    def render(self, w, h):
        w, h = int(w), int(h)
        if w < 80 or h < 80 or (w, h) == self._last:
            return
        self._last = (w, h)
        self.config(width=w, height=h)
        self.delete("all")
        pad = 18
        iw, ih = w - 2 * pad, h - 2 * pad
        radius = int(min(iw, ih) * 0.06)

        if self._src is None:
            round_rect(self, pad, pad, w - pad, h - pad, radius,
                       fill=BLUE_SOFT, outline=BLUE_SOFT)
            self.create_text(w / 2, h / 2, fill=BLUE,
                             text="Add assets/hero.jpg\n(and pip install pillow)",
                             justify="center")
            return

        base = Image.new("RGB", (w, h), (255, 255, 255))
        shadow = Image.new("L", (w, h), 0)
        ImageDraw.Draw(shadow).rounded_rectangle(
            (pad, pad + 8, pad + iw, pad + ih + 8), radius, fill=70)
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        base.paste(Image.new("RGB", (w, h), (15, 23, 42)), (0, 0), shadow)

        photo = ImageOps.fit(self._src, (iw, ih), Image.LANCZOS)
        mask = Image.new("L", (iw, ih), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, iw - 1, ih - 1), radius,
                                                fill=255)
        base.paste(photo, (pad, pad), mask)

        self._photo = ImageTk.PhotoImage(base)
        self.create_image(0, 0, image=self._photo, anchor="nw")


def make_app_icon(root, size=64):
    if not PIL_OK:
        return None
    if os.path.exists(LOGO_IMG):
        img = Image.open(LOGO_IMG).convert("RGBA").resize((size, size),
                                                          Image.LANCZOS)
    else:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, size - 1, size - 1),
                            radius=int(size * 0.22), fill=BLUE)
        c, r = size / 2, size * 0.32
        d.ellipse((c - r, c - r, c + r, c + r), fill="#14532d",
                  outline=WHITE, width=max(1, size // 16))
        r2 = size * 0.14
        d.ellipse((c - r2, c - r2, c + r2, c + r2), fill="#22c55e",
                  outline=WHITE)
    photo = ImageTk.PhotoImage(img)
    root._icon_photo = photo
    return photo


class TopRightLogo(tk.Label):
    def __init__(self, parent, height=48):
        super().__init__(parent, bg=WHITE, bd=0)
        self.loaded = False
        self._photo = None
        if PIL_OK and os.path.exists(LOGO_IMG):
            img = Image.open(LOGO_IMG).convert("RGBA")
            w = round(img.width * height / img.height)
            img = img.resize((w, height), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            self.config(image=self._photo)
            self.loaded = True


class WideButton(RoundedButton):
    def __init__(self, parent, text, command, height=36, **kw):
        super().__init__(parent, text, command, 100, height, **kw)
        self._cfg = dict(text=text, radius=kw.get("radius", 10),
                         bg=kw.get("bg", BLUE), fg=kw.get("fg", WHITE),
                         outline=kw.get("outline"), font=kw.get("font"))
        self.bind("<Configure>", self._resize)

    def _resize(self, e):
        if e.width < 20:
            return
        c = self._cfg
        self.delete("all")
        self._shape = round_rect(self, 1, 1, e.width - 1, e.height - 1,
                                 c["radius"], fill=c["bg"],
                                 outline=c["outline"] or c["bg"], width=1)
        self.create_text(e.width / 2, e.height / 2, text=c["text"],
                         fill=c["fg"], font=c["font"])


class ScrollFrame(tk.Frame):
    def __init__(self, parent, on_width=None):
        super().__init__(parent, bg=WHITE)
        self.on_width = on_width
        self._after = None
        self.canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0,
                                yscrollincrement=20)
        self.vsb = tk.Scrollbar(self, orient="vertical",
                                command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=WHITE)
        self._win = self.canvas.create_window(0, 0, window=self.inner,
                                              anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_all(seq, self._wheel, add="+")

    def _on_canvas(self, e):
        self.canvas.itemconfigure(self._win, width=e.width)
        if self.on_width:
            if self._after:
                self.after_cancel(self._after)
            self._after = self.after(40, lambda: self.on_width(e.width))

    def _wheel(self, e):
        if not self.winfo_viewable():
            return
        num = getattr(e, "num", 0)
        if num == 4:
            d = -1
        elif num == 5:
            d = 1
        else:
            d = -1 if e.delta > 0 else 1
        self.canvas.yview_scroll(d * 3, "units")


class PhotoBox(tk.Canvas):
    """Rounded or circular photo."""
    def __init__(self, parent, filename, height, radius=12, bg=WHITE,
                 tint=BLUE_SOFT, circular=False, width=None):
        fixed_w = width if width else 10
        super().__init__(parent, width=fixed_w, height=height, bg=bg,
                         highlightthickness=0)
        self.h, self.radius, self.tint = height, radius, tint
        self.name, self.bgc = filename, bg
        self.circular = circular
        self._fixed_w = width
        self._src, self._photo, self._last_w = None, None, 0
        path = (filename if os.path.isabs(filename)
                else os.path.join(ASSETS_DIR, filename))
        if PIL_OK and os.path.exists(path):
            try:
                self._src = Image.open(path).convert("RGB")
            except Exception:
                self._src = None

        if width:
            self.after(20, lambda: self._draw(width))
        else:
            self.bind("<Configure>", self._on_cfg)

    def _on_cfg(self, e):
        if e.width < 20 or e.width == self._last_w:
            return
        self._last_w = e.width
        self._draw(e.width)

    def _draw(self, w):
        h = self.h
        self.delete("all")
        if self._src is None:
            if self.circular:
                self.create_oval(0, 0, w, h, fill=self.tint,
                                 outline=self.tint)
            else:
                round_rect(self, 0, 0, w, h, self.radius, fill=self.tint,
                           outline=self.tint)
            self.create_text(w / 2, h / 2, text=f"assets/{self.name}",
                             fill=SLATE)
            return
        img = ImageOps.fit(self._src, (w, h), Image.LANCZOS)
        mask = Image.new("L", (w, h), 0)
        if self.circular:
            ImageDraw.Draw(mask).ellipse((0, 0, w - 1, h - 1), fill=255)
        else:
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, w - 1, h - 1), self.radius, fill=255)
        out = Image.new("RGB", (w, h), ImageColor.getrgb(self.bgc))
        out.paste(img, (0, 0), mask)
        self._photo = ImageTk.PhotoImage(out)
        self.create_image(0, 0, image=self._photo, anchor="nw")


class Card(tk.Frame):
    def __init__(self, parent, parent_bg, fill=WHITE, border="#e5e7eb",
                 radius=16, pad=16):
        super().__init__(parent, bg=parent_bg, highlightthickness=0)
        self.fill, self.border, self.radius = fill, border, radius
        self.hover = False
        self._bgcanvas = tk.Canvas(self, bg=parent_bg, highlightthickness=0)
        self._bgcanvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.inner = tk.Frame(self, bg=fill)
        self.inner.pack(padx=pad, pady=pad, fill="both", expand=True)
        self._wraps = []
        self.bind("<Configure>", lambda e: self.redraw())

    def wrap(self, label, frac=1.0, margin=0):
        self._wraps.append((label, frac, margin))
        return label

    def redraw(self):
        w, h = self.winfo_width(), self.winfo_height()
        self._bgcanvas.delete("all")
        if w > 2 and h > 2:
            if self.hover:
                round_rect(self._bgcanvas, 1, 1, w - 1, h - 1, self.radius,
                           fill=BLUE_SOFT, outline=BLUE_SOFT, tags="bg")
                round_rect(self._bgcanvas, 4, 4, w - 4, h - 4,
                           max(4, self.radius - 3), fill=self.fill,
                           outline=self.border, width=2, tags="bg")
            else:
                round_rect(self._bgcanvas, 1, 1, w - 1, h - 1, self.radius,
                           fill=self.fill, outline=self.border, tags="bg")
        for lab, frac, margin in self._wraps:
            lab.config(wraplength=max(60, int(w * frac - margin)))


class LogoutDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Log out")
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(app)
        w, h = 420, 230
        x = app.winfo_rootx() + (app.winfo_width() - w) // 2
        y = app.winfo_rooty() + (app.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

        f_msg = tkfont.Font(family=app.family, size=-22)
        self._fonts = (f_msg,)
        tk.Label(self, text="Are you sure you want to log out?", font=f_msg,
                 fg="#64748b", bg=WHITE, wraplength=320,
                 justify="center").pack(pady=(44, 26))
        RoundedButton(self, "Log Out", self.confirm, 170, 58, radius=16,
                      bg=PURPLE, hover=PURPLE_DARK, fg=WHITE,
                      outline="#8e8e9f", font=f_msg).pack()
        self.bind("<Return>", lambda e: self.confirm())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def confirm(self):
        self.destroy()
        self.app.logout()


# ---- free-floating helpers ------------------------------------------------
def safe_destroy_all_grabs(root):
    try:
        root.grab_release()
    except tk.TclError:
        pass
    for w in list(root.winfo_children()):
        try:
            if isinstance(w, tk.Toplevel):
                w.grab_release()
        except tk.TclError:
            pass


# ---------------------------------------------------------------- PlayZone Dialog
class PlayZoneDialog(tk.Toplevel):
    """A custom modal that replaces tkinter.messagebox safely."""
    def __init__(self, parent, title, message, type="info"):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=WHITE)
        self.resizable(False, False)
        
        # Force standard window decorations so the Red X works natively
        self.transient(parent)
        self.attributes("-topmost", True)
        
        # Colors based on type
        colors = {
            "info": (BLUE, BLUE_HOVER, "ℹ"),
            "success": (GREEN, "#dcfce7", "✓"),
            "warning": (AMBER, "#fef3c7", "!"),
            "error": ("#dc2626", "#fee2e2", "✕"),
        }
        fg_color, bg_color, icon_text = colors.get(type, colors["info"])
        
        # Center logic
        w, h = 400, 260
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        
        card = Card(self, WHITE, border="#e5e7eb", radius=16, pad=28)
        card.pack(fill="both", expand=True, padx=2, pady=2)
        inner = card.inner

        # Icon
        ic = tk.Canvas(inner, width=50, height=50, bg=WHITE, highlightthickness=0)
        ic.create_oval(0, 0, 50, 50, fill=bg_color, outline=bg_color)
        ic.create_text(25, 25, text=icon_text, fill=fg_color, font=(parent.family, -22, "bold"))
        ic.pack(pady=(0, 16))

        tk.Label(inner, text=title, font=(parent.family, -18, "bold"), fg=NAVY, bg=WHITE).pack()
        tk.Label(inner, text=message, font=(parent.family, -12), fg=SLATE, bg=WHITE, wraplength=320, justify="center").pack(pady=(8, 24))

        WideButton(inner, "OK", self.destroy, height=40, radius=8, 
                   bg=BLUE, hover=BLUE_DARK, fg=WHITE, font=(parent.family, -13, "bold")).pack(fill="x")
        
        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.update_idletasks()
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass


# ---- base pages -----------------------------------------------------------
class BasePage(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=WHITE)
        self.app = app

    def on_show(self, **kwargs):
        pass


class SectionPage(BasePage):
    MAXW = 1200

    NAV_LINKS = [("Home", "home", None), ("About Us", "about", None),
                 ("Events", "events", None),
                 ("Reservation", "reservation", None),
                 ("Feedback", "feedback", None)]

    def __init__(self, app, nav_key, local=None):
        super().__init__(app)
        self.nav_key = nav_key
        self.local = local or {}
        self._bodies, self._reflows, self.targets, self._wraps2 = [], [], {}, []
        self._links_on = True

        def F(size, bold=False):
            return tkfont.Font(family=app.family, size=-size,
                               weight="bold" if bold else "normal")
        self.f = {
            "h1": F(44, True), "h2": F(30, True), "tag": F(12, True),
            "p": F(15), "label": F(14), "label_bold": F(14, True),
            "card_t": F(16, True), "small": F(13), "btn": F(13, True),
            "icon": F(18, True), "foot": F(13),
        }

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_nav()
        self.scroll = ScrollFrame(self, on_width=self._apply)
        self.scroll.grid(row=1, column=0, sticky="nsew")
        self.body = self.scroll.inner

    def on_show(self, **kwargs):
        self.scroll.canvas.yview_moveto(0)

    def _build_nav(self):
        app = self.app
        bar = tk.Frame(self, bg=WHITE)
        bar.grid(row=0, column=0, sticky="ew")
        row = tk.Frame(bar, bg=WHITE)
        row.pack(fill="x", padx=40, pady=12)

        brand = tk.Frame(row, bg=WHITE)
        brand.pack(side="left")
        LogoMark(brand, 36).pack(side="left")
        txt = tk.Frame(brand, bg=WHITE)
        txt.pack(side="left", padx=(10, 0))
        tk.Label(txt, text="PLAY ZONE", font=app.f_brand, fg=NAVY,
                 bg=WHITE).pack(anchor="w")
        tk.Label(txt, text="BOOK. PLAY. ENJOY.", font=app.f_tag, fg=GREEN,
                 bg=WHITE).pack(anchor="w")

        # ---- top-right buttons -----------------------------------------
        right = tk.Frame(row, bg=WHITE)
        right.pack(side="right")
        
        RoundedButton(right, "Reserve Now",
                      lambda: app.navigate("reservation"), 110, 36, radius=8,
                      bg=BLUE, hover=BLUE_DARK, fg=WHITE,
                      font=self.f["btn"]).pack(side="left", padx=(0, 12))
                      
        self.profile_icon = ProfileMenu(right, app, 36)
        self.profile_icon.pack(side="left")

        self.links = tk.Frame(row, bg=WHITE)
        self.links.pack(side="left", expand=True)
        for text, page, section in self.NAV_LINKS:
            key = text.split()[0].lower()
            is_current = (page == self.nav_key and section is None and
                          key not in self.local)
            if key in self.local:
                cmd = self.local[key]
            elif page == self.nav_key:
                cmd = ((lambda s=section: self.scroll_to(s)) if section
                       else (lambda: self.scroll.canvas.yview_moveto(0)))
            else:
                cmd = (lambda p=page, s=section: app.navigate(p, s))
            cell = tk.Frame(self.links, bg=WHITE)
            cell.pack(side="left", padx=10)
            lb = tk.Label(cell, text=text,
                          font=(self.f["label_bold"] if is_current
                                else self.f["label"]),
                          fg=BLUE if is_current else "#334155", bg=WHITE,
                          cursor="hand2")
            lb.pack()
            underline = tk.Frame(cell, bg=BLUE if is_current else WHITE,
                                 height=2)
            underline.pack(fill="x", pady=(5, 0))
            if not is_current:
                lb.bind("<Enter>", lambda e, l=lb: l.config(fg=BLUE))
                lb.bind("<Leave>", lambda e, l=lb: l.config(fg="#334155"))
            lb.bind("<Button-1>", lambda e, c=cmd: c())
        tk.Frame(bar, bg="#e5e7eb", height=1).pack(fill="x")

    def section(self, bg, top=56, bottom=56, key=None):
        outer = tk.Frame(self.body, bg=bg)
        outer.pack(fill="x")
        body = tk.Frame(outer, bg=bg)
        body.pack(fill="x", padx=40, pady=(top, bottom))
        self._bodies.append(body)
        if key:
            self.targets[key] = outer
        return body

    def heading(self, body, tag, title, bg, anchor="w"):
        if tag:
            tk.Label(body, text=tag, font=self.f["tag"], fg=BLUE,
                     bg=bg).pack(anchor=anchor)
        tk.Label(body, text=title, font=self.f["h2"], fg=NAVY, bg=bg).pack(
            anchor=anchor, pady=(4, 0) if tag else (0, 0))

    def reflow(self, container, items, fn, sticky="nsew"):
        r = {"c": container, "items": items, "fn": fn, "n": fn(self.MAXW),
             "sticky": sticky}
        self._reflows = [x for x in self._reflows if x["c"] is not container]
        self._reflows.append(r)
        self._regrid(r)
        return r

    def _regrid(self, r):
        c, n = r["c"], r["n"]
        for it in r["items"]:
            it.grid_forget()
        for i in range(8):
            c.grid_columnconfigure(i, weight=0, uniform="")
        for i in range(n):
            c.grid_columnconfigure(i, weight=1, uniform=f"g{id(c)}")
        for i, it in enumerate(r["items"]):
            it.grid(row=i // n, column=i % n, sticky=r["sticky"], padx=8,
                    pady=8)

    def wrap(self, label, r, margin, wraplength=None):
        if r is None:
            label.config(wraplength=wraplength or 400)
            return label
        self._wraps2.append((label, r, margin))
        return label

    def _apply_wraps(self, w=None):
        for label, r, margin in self._wraps2:
            if w:
                side = max(24, (w - self.MAXW) // 2)
                colw = (w - 2 * side) / max(1, r["n"])
            else:
                colw = r["c"].winfo_width() / max(1, r["n"])
            label.config(wraplength=max(60, int(colw - margin)))

    def scroll_to(self, key):
        self.update_idletasks()
        total = max(1, self.body.winfo_height())
        if key not in self.targets:
            self.scroll.canvas.yview_moveto(0)
            return
        y = self.targets[key].winfo_y()
        self.scroll.canvas.yview_moveto(y / total)

    def _apply(self, w):
        side = max(24, (w - self.MAXW) // 2)
        for b in self._bodies:
            b.pack_configure(padx=side)
        for r in self._reflows:
            n = r["fn"](w)
            if n != r["n"]:
                r["n"] = n
                self._regrid(r)
        want = w >= 860
        if want != self._links_on:
            self._links_on = want
            if want:
                self.links.pack(side="left", expand=True)
            else:
                self.links.pack_forget()
        self._apply_wraps(w)


class ProfileMenu(tk.Canvas):
    """Circular avatar button that opens a dropdown menu."""
    def __init__(self, parent, app, size=36):
        super().__init__(parent, width=size, height=size, bg=WHITE,
                         highlightthickness=0, cursor="hand2")
        self.app = app
        self.size = size
        self._panel = None
        self._photo = None
        self.bind("<Button-1>", self._toggle)
        self._draw()

    def _draw(self):
        self.delete("all")
        user = getattr(self.app, "user", {}) or {}
        name = user.get("name", "Student")
        initial = name[0].upper() if name else "U"
        
        # Try to load avatar from assets
        email = user.get("email", "user")
        base_name = f"user_avatar_{email.split('@')[0]}"
        
        target = None
        for ext in (".jpg", ".png", ".jpeg", ".gif", ".bmp"):
            if os.path.exists(os.path.join(ASSETS_DIR, base_name + ext)):
                target = base_name + ext
                break
                
        if target and PIL_OK:
            try:
                path = os.path.join(ASSETS_DIR, target)
                img = Image.open(path).convert("RGB").resize((self.size, self.size), Image.LANCZOS)
                mask = Image.new("L", (self.size, self.size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, self.size - 1, self.size - 1), fill=255)
                out = Image.new("RGB", (self.size, self.size), WHITE)
                out.paste(img, (0, 0), mask)
                self._photo = ImageTk.PhotoImage(out)
                self.create_image(0, 0, image=self._photo, anchor="nw")
                return
            except Exception:
                pass

        # Fallback: Circle with initial
        self.create_oval(1, 1, self.size-1, self.size-1, fill=BLUE_SOFT, outline=BLUE)
        self.create_text(self.size/2, self.size/2 + 1, text=initial, fill=BLUE, 
                         font=(self.app.family, -14, "bold"))

    def _toggle(self, event):
        if self._panel and self._panel.winfo_exists():
            self._panel.destroy()
            self._panel = None
            return
        self._panel = ProfilePanel(self)

class ProfilePanel(tk.Frame):
    """The dropdown menu."""
    def __init__(self, canvas):
        super().__init__(canvas.winfo_toplevel(), bg=WHITE, highlightthickness=1, highlightbackground="#e5e7eb")
        self.app = canvas.app
        canvas.update_idletasks()
        
        # Position it under the avatar, aligned to the right
        x = canvas.winfo_rootx() - canvas.winfo_toplevel().winfo_rootx() - 150 + canvas.winfo_width()
        y = canvas.winfo_rooty() - canvas.winfo_toplevel().winfo_rooty() + canvas.winfo_height() + 8
        self.place(x=x, y=y, width=170)

        # Top part: User info
        user = getattr(self.app, "user", {}) or {}
        name = user.get("name", "Student")
        email = user.get("email", "")
        
        info = tk.Frame(self, bg=WHITE, padx=16, pady=12)
        info.pack(fill="x")
        tk.Label(info, text=name, font=(self.app.family, -13, "bold"), fg=NAVY, bg=WHITE, anchor="w").pack(fill="x")
        tk.Label(info, text=email, font=(self.app.family, -11), fg=SLATE, bg=WHITE, anchor="w").pack(fill="x", pady=(2,0))
        
        tk.Frame(self, bg="#e5e7eb", height=1).pack(fill="x")

        # Menu items
        items = [
            ("👤  My Profile", lambda: self._go("profile")),
            ("📅  My Bookings", lambda: self._go("my_bookings")),
        ]
        for text, cmd in items:
            lbl = tk.Label(self, text=text, font=(self.app.family, -13), fg=NAVY, bg=WHITE, anchor="w", padx=16, pady=10, cursor="hand2")
            lbl.pack(fill="x")
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(bg=BLUE_SOFT, fg=BLUE))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(bg=WHITE, fg=NAVY))
            lbl.bind("<Button-1>", lambda e, c=cmd: c())

        tk.Frame(self, bg="#e5e7eb", height=1).pack(fill="x")

        # Logout
        out = tk.Label(self, text="🚪  Log out", font=(self.app.family, -13), fg="#dc2626", bg=WHITE, anchor="w", padx=16, pady=10, cursor="hand2")
        out.pack(fill="x")
        out.bind("<Enter>", lambda e: out.config(bg="#fee2e2"))
        out.bind("<Leave>", lambda e: out.config(bg=WHITE))
        out.bind("<Button-1>", lambda e: self._logout())

        self.after(100, self._bind_close)

    def _bind_close(self):
        self.winfo_toplevel().bind("<Button-1>", self._close_if_outside, add="+")

    def _close_if_outside(self, event):
        widget = event.widget
        if widget is self or str(widget).startswith(str(self)):
            return
        # If they clicked the avatar again, let _toggle handle it
        if isinstance(widget, ProfileMenu):
            return
        self.destroy()

    def _go(self, page):
        self.destroy()
        self.app.navigate(page)

    def _logout(self):
        self.destroy()
        LogoutDialog(self.app)