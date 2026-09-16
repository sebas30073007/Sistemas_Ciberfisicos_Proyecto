#!/usr/bin/env python3
"""
demo.py  ·  HMI v2 — Modo Demo
Simulación completa sin servidor ni hardware.

Mejoras sobre la versión base:
  1. Teclado QWERTY táctil con shift, números y espacio
  2. Preview en tiempo real del saludo mientras se escribe el nombre
  3. Validación visual inline (borde rojo/verde en el campo)
  4. Confirmación explícita "¿Tu nombre es X?" antes de guardar
  5. Feedback del objeto clasificado: tipo + delta de puntos
  6. Historial de depósitos de la sesión en el panel del usuario
  7. Pantalla de carga con pasos del robot animados
  8. Countdown de inactividad con botón "Seguir aquí"

Tarjetas de prueba:
  TARJETA-001  Ana García      (5 lata · 3 vidrio · 2 tetra)
  TARJETA-002  Carlos López    (0 lata · 7 vidrio · 1 tetra)
  TARJETA-003  María Torres    (12 lata · 8 vidrio · 6 tetra)
  NUEVA-004    Tarjeta nueva   → 404 en login / flujo crear en cuenta
"""
import random
import threading
import time
import tkinter as tk

# ── Ventana ───────────────────────────────────────────────────────────────────
WIN_W, WIN_H   = 480, 800
INACT_MS       = 60_000     # ms hasta mostrar countdown de inactividad
COUNTDOWN_SECS = 10         # segundos del countdown antes de volver a inicio

# ── Paleta ────────────────────────────────────────────────────────────────────
BG       = "#0d1117"
SURFACE  = "#161b22"
SURFACE2 = "#21262d"
ACCENT   = "#3fb950"
ACCENT_H = "#2ea043"
FG       = "#e6edf3"
FG2      = "#7d8590"
FG_AC    = "#0d1117"
DANGER   = "#f85149"
WARN     = "#f59e0b"
INFO     = "#60a5fa"

# ── Fuentes ───────────────────────────────────────────────────────────────────
F_TITLE = ("Arial", 24, "bold")
F_SUB   = ("Arial", 14)
F_BODY  = ("Arial", 16)
F_BTN   = ("Arial", 15, "bold")
F_SMALL = ("Arial", 12)
F_KEY   = ("Arial", 15, "bold")

# ── Etiquetas de categorías ───────────────────────────────────────────────────
CAT_LABEL = {"lata": "🥫 Lata", "vidrio": "🍶 Vidrio", "tetra": "📦 Tetra"}
CAT_COLOR = {"lata": "#60a5fa", "vidrio": "#a78bfa", "tetra": "#fb923c"}


# ══════════════════════════════════════════════════════════════════════════════
# Base de datos en memoria
# ══════════════════════════════════════════════════════════════════════════════

_DB: dict = {
    "TARJETA-001": {"user_id": "TARJETA-001", "nombre": "Ana García",
                    "lata": 5,  "vidrio": 3, "tetra": 2},
    "TARJETA-002": {"user_id": "TARJETA-002", "nombre": "Carlos López",
                    "lata": 0,  "vidrio": 7, "tetra": 1},
    "TARJETA-003": {"user_id": "TARJETA-003", "nombre": "María Torres",
                    "lata": 12, "vidrio": 8, "tetra": 6},
}

DEMO_CARDS = [
    ("TARJETA-001", "Ana García"),
    ("TARJETA-002", "Carlos López"),
    ("TARJETA-003", "María Torres"),
    ("NUEVA-004",   "Tarjeta nueva / desconocida"),
]


def _total(u: dict) -> int:
    return u["lata"] + u["vidrio"] + u["tetra"]


class _NotFound(Exception):
    pass


def _consulta(user_id: str) -> dict:
    if user_id not in _DB:
        raise _NotFound()
    u = _DB[user_id]
    return {"status": "ok", "respuesta_render": {**u, "total": _total(u)}}


def _existe(user_id: str) -> bool:
    return user_id in _DB


def _crear_usuario(user_id: str, nombre: str):
    if user_id in _DB:
        raise ValueError("El usuario ya existe.")
    _DB[user_id] = {"user_id": user_id, "nombre": nombre,
                    "lata": 0, "vidrio": 0, "tetra": 0}
    DEMO_CARDS.append((user_id, nombre))


def _empezar(user_id=None) -> dict:
    """Simula el robot: retardo corto + incrementa categoría aleatoria."""
    time.sleep(0.2)   # retardo mínimo; la pantalla de pasos controla el timing visual
    cat = random.choice(["lata", "vidrio", "tetra"])
    if user_id and user_id in _DB:
        _DB[user_id][cat] += 1
    return {"status": "ok", "objeto": cat}


# ══════════════════════════════════════════════════════════════════════════════
# Widgets base
# ══════════════════════════════════════════════════════════════════════════════

def _rrect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1+r, y1,   x2-r, y1,
        x2,   y1,   x2,   y1+r,
        x2,   y2-r, x2,   y2,
        x2-r, y2,   x1+r, y2,
        x1,   y2,   x1,   y2-r,
        x1,   y1+r, x1,   y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


class RoundedButton(tk.Canvas):
    """
    Botón redondeado con Canvas.
    Atributos propios con prefijo btn_ para no pisar tk.Widget._w (path Tcl).
    """

    def __init__(self, parent, text, bg, fg,
                 command=None, w=340, h=54, r=14, hover=None):
        pbg = parent["bg"] if hasattr(parent, "__getitem__") else BG
        super().__init__(parent, width=w, height=h,
                         bg=pbg, highlightthickness=0, bd=0)
        self.btn_bg  = bg
        self.btn_hov = hover or bg
        self.btn_fg  = fg
        self.btn_cmd = command

        self._rid = _rrect(self, 2, 2, w-2, h-2, r, fill=bg, outline="")
        self._tid = self.create_text(w//2, h//2, text=text,
                                     font=F_BTN, fill=fg, anchor="center")

        for ev, fn in [("<Enter>",          self._enter),
                       ("<Leave>",          self._leave),
                       ("<ButtonPress-1>",  self._press),
                       ("<ButtonRelease-1>",self._release)]:
            self.bind(ev, fn)

    def _enter(self,   _=None): self.itemconfig(self._rid, fill=self.btn_hov)
    def _leave(self,   _=None): self.itemconfig(self._rid, fill=self.btn_bg)
    def _press(self,   _=None): self.itemconfig(self._rid, fill=self.btn_hov)
    def _release(self, _=None):
        self.itemconfig(self._rid, fill=self.btn_bg)
        if self.btn_cmd:
            self.btn_cmd()

    def set_text(self, text):
        self.itemconfig(self._tid, text=text)


class Divider(tk.Frame):
    def __init__(self, parent, color=SURFACE2, **kw):
        super().__init__(parent, height=1, bg=color, **kw)


# ══════════════════════════════════════════════════════════════════════════════
# Teclado QWERTY virtual  (mejora 1)
# ══════════════════════════════════════════════════════════════════════════════

class VirtualKeyboard(tk.Frame):
    """
    Teclado táctil QWERTY con shift, modo numérico y barra espaciadora.
    Escribe en el StringVar que recibe en el constructor.
    """

    _ALPHA = [
        list("QWERTYUIOP"),
        list("ASDFGHJKLÑ"),
        list("ZXCVBNM"),
    ]
    _NUM = [
        list("1234567890"),
        list("@#$%-+=()!"),
        list(".,;:?'\"/_"),
    ]

    # Tamaños de teclas (px)
    _KW  = 41    # tecla normal
    _KH  = 42    # altura normal
    _KR  = 8     # radio de esquinas
    _PAD = 2     # gap entre teclas

    def __init__(self, parent, string_var: tk.StringVar):
        super().__init__(parent, bg=BG)
        self._var   = string_var
        self._upper = True
        self._mode  = "alpha"   # "alpha" | "num"
        self._draw()

    # ── construcción ──────────────────────────────────────────────────────────

    def _draw(self):
        for w in self.winfo_children():
            w.destroy()

        rows = self._ALPHA if self._mode == "alpha" else self._NUM

        for i, keys in enumerate(rows):
            row = tk.Frame(self, bg=BG)
            row.pack(pady=self._PAD)

            if i == 2:
                self._add_shift(row)

            for k in keys:
                disp = k.upper() if (self._upper and self._mode == "alpha") else k
                btn = RoundedButton(row, disp, SURFACE2, FG,
                                    hover=SURFACE,
                                    w=self._KW, h=self._KH, r=self._KR,
                                    command=lambda c=k: self._type(c))
                btn.pack(side="left", padx=self._PAD)

            if i == 2:
                self._add_backspace(row, w=52)

        # Fila inferior: modo | espacio | borrar
        bot = tk.Frame(self, bg=BG)
        bot.pack(pady=self._PAD)

        mode_lbl = "123" if self._mode == "alpha" else "ABC"
        RoundedButton(bot, mode_lbl, SURFACE2, FG2,
                      hover=SURFACE,
                      w=64, h=self._KH, r=self._KR,
                      command=self._toggle_mode
                      ).pack(side="left", padx=self._PAD)

        RoundedButton(bot, "espacio", SURFACE2, FG,
                      hover=SURFACE,
                      w=218, h=self._KH, r=self._KR,
                      command=lambda: self._type(" ")
                      ).pack(side="left", padx=self._PAD)

        self._add_backspace(bot, w=76)

    def _add_shift(self, row):
        color = ACCENT if self._upper else SURFACE2
        fg    = FG_AC  if self._upper else FG2
        RoundedButton(row, "⇧", color, fg,
                      hover=ACCENT_H if self._upper else SURFACE,
                      w=48, h=self._KH, r=self._KR,
                      command=self._toggle_shift
                      ).pack(side="left", padx=self._PAD)

    def _add_backspace(self, row, w=48):
        RoundedButton(row, "⌫", SURFACE2, DANGER,
                      hover="#3d1f1f",
                      w=w, h=self._KH, r=self._KR,
                      command=self._backspace
                      ).pack(side="left", padx=self._PAD)

    # ── acciones ──────────────────────────────────────────────────────────────

    def _type(self, char: str):
        out = char.upper() if (self._upper and self._mode == "alpha") else char
        self._var.set(self._var.get() + out)

    def _backspace(self):
        self._var.set(self._var.get()[:-1])

    def _toggle_shift(self):
        self._upper = not self._upper
        self._draw()

    def _toggle_mode(self):
        self._mode  = "num" if self._mode == "alpha" else "alpha"
        self._upper = True
        self._draw()


# ══════════════════════════════════════════════════════════════════════════════
# Popup genérico
# ══════════════════════════════════════════════════════════════════════════════

def popup(root: tk.Tk, title: str, msg: str, color: str, on_close=None):
    """Modal sin decoración, auto-cierra en 2.5 s o al tocar."""
    win = tk.Toplevel(root)
    win.resizable(False, False)
    win.configure(bg=SURFACE)
    win.overrideredirect(True)

    tk.Frame(win, height=20, bg=SURFACE).pack()
    tk.Label(win, text=title, font=F_BODY, bg=SURFACE, fg=color).pack(padx=30)
    tk.Frame(win, height=8,   bg=SURFACE).pack()
    tk.Label(win, text=msg, font=F_SMALL, bg=SURFACE, fg=FG2,
             wraplength=280, justify="center").pack(padx=30)
    tk.Frame(win, height=20, bg=SURFACE).pack()

    win.update_idletasks()
    pw = win.winfo_reqwidth()
    ph = win.winfo_reqheight()
    ox = root.winfo_x() + (WIN_W - pw) // 2
    oy = root.winfo_y() + (WIN_H - ph) // 2
    win.geometry(f"+{ox}+{oy}")
    win.grab_set()

    def _cerrar():
        try:
            win.grab_release()
            win.destroy()
        except Exception:
            pass
        if on_close:
            root.after(0, on_close)

    win.after(2500, _cerrar)
    win.bind("<Button-1>", lambda _: _cerrar())


# ══════════════════════════════════════════════════════════════════════════════
# Countdown de inactividad  (mejora 8)
# ══════════════════════════════════════════════════════════════════════════════

class CountdownOverlay(tk.Toplevel):
    """
    Overlay modal que muestra una cuenta regresiva.
    Si el usuario no toca "Seguir aquí" en COUNTDOWN_SECS segundos,
    vuelve a la pantalla de bienvenida.
    """

    def __init__(self, root: tk.Tk, app):
        super().__init__(root)
        self.overrideredirect(True)
        self.configure(bg=SURFACE)
        self._app   = app
        self._count = COUNTDOWN_SECS
        self._alive = True

        # Dimensiones y posición centrada
        w, h = 320, 230
        ox = root.winfo_x() + (WIN_W - w) // 2
        oy = root.winfo_y() + (WIN_H - h) // 2
        self.geometry(f"{w}x{h}+{ox}+{oy}")

        tk.Frame(self, height=20, bg=SURFACE).pack()
        tk.Label(self, text="¿Sigues ahí?",
                 font=F_TITLE, bg=SURFACE, fg=FG).pack()
        tk.Label(self, text="Volviendo a inicio en",
                 font=F_SMALL, bg=SURFACE, fg=FG2).pack(pady=(4, 0))

        self._lbl = tk.Label(self, text=str(self._count),
                              font=("Arial", 52, "bold"), bg=SURFACE, fg=WARN)
        self._lbl.pack()

        RoundedButton(self, "  Seguir aquí  ",
                      ACCENT, FG_AC, hover=ACCENT_H,
                      w=220, h=48, r=12,
                      command=self._stay).pack(pady=12)

        self.grab_set()
        self._tick()

    def _tick(self):
        if not self._alive:
            return
        self._count -= 1
        if self._count <= 0:
            self._go_home()
            return
        try:
            self._lbl.config(text=str(self._count))
            self.after(1000, self._tick)
        except tk.TclError:
            pass

    def _stay(self):
        self._alive = False
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass
        self._app._reset_inact()

    def _go_home(self):
        self._alive = False
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass
        self._app.show_welcome()


# ══════════════════════════════════════════════════════════════════════════════
# App — controlador de navegación
# ══════════════════════════════════════════════════════════════════════════════

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Clasificadora — DEMO")
        self.root.geometry(f"{WIN_W}x{WIN_H}")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self._body  = tk.Frame(root, bg=BG)
        self._body.pack(fill=tk.BOTH, expand=True)

        self._frame   = None
        self._timer   = None
        self._overlay = None

        # Sesión del usuario logueado
        self.session_uid     = None
        self.session_history = []   # lista de cats depositados en esta visita

        self.show_welcome()

    # ── swap de frames ────────────────────────────────────────────────────────

    def _swap(self, FrameCls, **kwargs):
        if self._frame:
            self._frame.destroy()
        self._frame = FrameCls(self._body, self, **kwargs)
        self._frame.pack(fill=tk.BOTH, expand=True)
        self._reset_inact()

    # ── inactividad ───────────────────────────────────────────────────────────

    def _reset_inact(self):
        if self._timer:
            self.root.after_cancel(self._timer)
        self._timer = self.root.after(INACT_MS, self._show_countdown)

    def _show_countdown(self):
        # No mostrar countdown en bienvenida ni en loading
        if isinstance(self._frame, (WelcomeFrame, LoadingStepsFrame)):
            return
        try:
            self._overlay = CountdownOverlay(self.root, self)
        except Exception:
            pass

    # ── navegación ────────────────────────────────────────────────────────────

    def show_welcome(self):
        self.session_uid     = None
        self.session_history = []
        self._swap(WelcomeFrame)

    def show_scan(self, mode: str):
        self._swap(ScanFrame, mode=mode)

    def show_user(self, data: dict):
        uid = data.get("respuesta_render", {}).get("user_id")
        if uid != self.session_uid:
            self.session_uid     = uid
            self.session_history = []
        self._swap(UserFrame, data=data)

    def show_create(self, rfid_id: str):
        self._swap(CreateFrame, rfid_id=rfid_id)

    def show_anonymous(self):
        self._swap(AnonymousFrame)

    def show_loading_steps(self, user_id, on_complete):
        self._swap(LoadingStepsFrame, user_id=user_id, on_complete=on_complete)


# ══════════════════════════════════════════════════════════════════════════════
# Frame base con badge DEMO
# ══════════════════════════════════════════════════════════════════════════════

class _Base(tk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, bg=BG)
        self.app = app
        tk.Label(self, text=" DEMO ", font=("Arial", 10, "bold"),
                 bg=WARN, fg=BG, padx=4
                 ).place(relx=1.0, rely=0.0, anchor="ne", x=-8, y=8)


# ══════════════════════════════════════════════════════════════════════════════
# Pantallas
# ══════════════════════════════════════════════════════════════════════════════

# ── Bienvenida ────────────────────────────────────────────────────────────────

class WelcomeFrame(_Base):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        tk.Frame(self, height=70, bg=BG).pack()
        tk.Label(self, text="♻", font=("Arial", 96), bg=BG, fg=ACCENT).pack()
        tk.Label(self, text="CLASIFICADORA",
                 font=F_TITLE, bg=BG, fg=FG).pack(pady=(8, 4))
        tk.Label(self, text="Sistema de reciclaje inteligente",
                 font=F_SUB, bg=BG, fg=FG2).pack()
        tk.Frame(self, height=52, bg=BG).pack()

        RoundedButton(self, "  Iniciar sesión  ",
                      ACCENT, FG_AC, hover=ACCENT_H,
                      command=lambda: self.app.show_scan("login")
                      ).pack(pady=10)
        RoundedButton(self, "  Crear cuenta  ",
                      SURFACE2, FG, hover=SURFACE,
                      command=lambda: self.app.show_scan("create")
                      ).pack(pady=10)
        RoundedButton(self, "  Reciclar sin cuenta  ",
                      SURFACE, FG2, hover=SURFACE2,
                      command=self.app.show_anonymous
                      ).pack(pady=10)

        tk.Frame(self, height=28, bg=BG).pack()
        Divider(self).pack(fill="x", padx=40)
        tk.Label(self, text="Selecciona una opción para explorar el demo",
                 font=F_SMALL, bg=BG, fg=FG2).pack(pady=10)


# ── Selector de tarjeta RFID (simulado) ───────────────────────────────────────

class ScanFrame(_Base):
    def __init__(self, parent, app, mode: str):
        super().__init__(parent, app)
        self._mode = mode
        self._build()

    def _build(self):
        RoundedButton(self, "← Volver", SURFACE, FG2,
                      w=130, h=40, r=10,
                      command=self.app.show_welcome
                      ).pack(anchor="w", padx=20, pady=20)

        tk.Frame(self, height=8, bg=BG).pack()
        tk.Label(self, text="💳", font=("Arial", 56), bg=BG).pack()
        tk.Label(self, text="Selecciona una tarjeta",
                 font=F_TITLE, bg=BG, fg=FG).pack(pady=(10, 2))
        sub = ("para iniciar sesión"
               if self._mode == "login" else "para crear una cuenta")
        tk.Label(self, text=sub, font=F_SUB, bg=BG, fg=FG2).pack()

        tk.Frame(self, height=16, bg=BG).pack()
        Divider(self).pack(fill="x", padx=50)
        tk.Label(self, text="Modo demo — elige una tarjeta",
                 font=F_SMALL, bg=BG, fg=WARN).pack(pady=6)
        Divider(self).pack(fill="x", padx=50)
        tk.Frame(self, height=14, bg=BG).pack()

        for card_id, label in DEMO_CARDS:
            known = card_id in _DB
            icon  = "👤" if known else "❓"
            bg    = SURFACE2 if known else SURFACE
            RoundedButton(
                self, f"{icon}  {label}",
                bg, FG, hover=SURFACE, w=370, h=50, r=12,
                command=lambda cid=card_id: self._dispatch(cid)
            ).pack(pady=5)

    def _dispatch(self, rfid_id: str):
        if self._mode == "login":
            self._do_login(rfid_id)
        else:
            self._do_check_create(rfid_id)

    def _do_login(self, rfid_id: str):
        root, app = self.app.root, self.app
        def tarea():
            try:
                data = _consulta(rfid_id)
                root.after(0, lambda: app.show_user(data))
            except _NotFound:
                root.after(0, lambda: popup(
                    root, "No encontrado",
                    "Tarjeta sin cuenta.\nCrea una primero.",
                    DANGER, on_close=app.show_welcome))
            except Exception as e:
                root.after(0, lambda: popup(
                    root, "Error", str(e), DANGER, on_close=app.show_welcome))
        threading.Thread(target=tarea, daemon=True).start()

    def _do_check_create(self, rfid_id: str):
        root, app = self.app.root, self.app
        def tarea():
            try:
                if _existe(rfid_id):
                    root.after(0, lambda: popup(
                        root, "Ya existe",
                        "Esta tarjeta ya tiene una cuenta.",
                        WARN, on_close=app.show_welcome))
                else:
                    root.after(0, lambda: app.show_create(rfid_id))
            except Exception as e:
                root.after(0, lambda: popup(
                    root, "Error", str(e), DANGER, on_close=app.show_welcome))
        threading.Thread(target=tarea, daemon=True).start()


# ── Panel del usuario ─────────────────────────────────────────────────────────

class UserFrame(_Base):
    def __init__(self, parent, app, data: dict):
        super().__init__(parent, app)
        self._info = data.get("respuesta_render", {})
        self._build()

    def _build(self):
        info = self._info

        # ── Header ───────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=SURFACE, height=106)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"Hola, {info.get('nombre', '—')}",
                 font=F_TITLE, bg=SURFACE, fg=FG).pack(pady=(22, 2))
        tk.Label(hdr, text=f"ID: {info.get('user_id', '—')}",
                 font=F_SMALL, bg=SURFACE, fg=FG2).pack()

        # ── Puntos totales ────────────────────────────────────────────────────
        tk.Frame(self, height=18, bg=BG).pack()
        tk.Label(self, text=str(info.get("total", 0)),
                 font=("Arial", 68, "bold"), bg=BG, fg=ACCENT).pack()
        tk.Label(self, text="puntos totales",
                 font=F_SUB, bg=BG, fg=FG2).pack()

        # ── Desglose ──────────────────────────────────────────────────────────
        tk.Frame(self, height=14, bg=BG).pack()
        row = tk.Frame(self, bg=BG)
        row.pack()
        for icon, label, key in [("🥫","Lata","lata"),
                                  ("🍶","Vidrio","vidrio"),
                                  ("📦","Tetra","tetra")]:
            cell = tk.Frame(row, bg=SURFACE, width=124, height=80)
            cell.pack(side="left", padx=6)
            cell.pack_propagate(False)
            tk.Label(cell, text=f"{icon} {label}",
                     font=F_SMALL, bg=SURFACE, fg=FG2).pack(pady=(12, 0))
            tk.Label(cell, text=str(info.get(key, 0)),
                     font=("Arial", 22, "bold"),
                     bg=SURFACE, fg=CAT_COLOR[key]).pack()

        # ── Historial de sesión  (mejora 6) ──────────────────────────────────
        hist = self.app.session_history
        if hist:
            tk.Frame(self, height=10, bg=BG).pack()
            Divider(self).pack(fill="x", padx=40)
            tk.Label(self, text="Esta visita:",
                     font=F_SMALL, bg=BG, fg=FG2).pack(pady=(6, 2))
            # Mostrar los últimos 6 ítems como íconos en línea
            icons = "  ".join(CAT_LABEL[c].split()[0] for c in hist[-6:])
            suffix = f"  (+{len(hist)-6} más)" if len(hist) > 6 else ""
            tk.Label(self, text=icons + suffix,
                     font=("Arial", 22), bg=BG, fg=FG).pack()
            Divider(self).pack(fill="x", padx=40, pady=(6, 0))

        # ── Acciones ──────────────────────────────────────────────────────────
        tk.Frame(self, height=18, bg=BG).pack()
        RoundedButton(self, "  Depositar objeto  ",
                      ACCENT, FG_AC, hover=ACCENT_H,
                      command=self._depositar).pack(pady=10)
        RoundedButton(self, "  Terminar  ",
                      SURFACE, FG2, hover=SURFACE2,
                      command=self.app.show_welcome).pack(pady=6)

    def _depositar(self):
        uid  = self._info.get("user_id")
        root = self.app.root
        app  = self.app

        def on_complete(result):
            cat = result.get("objeto", "lata")
            app.session_history.append(cat)
            try:
                data = _consulta(uid)
            except Exception:
                data = None
            total_nuevo = data["respuesta_render"]["total"] if data else "?"

            def on_ui():
                msg = (f"Depositaste: {CAT_LABEL[cat]}\n"
                       f"Total ahora: {total_nuevo} puntos")
                if data:
                    popup(root, "¡Clasificado!", msg, ACCENT,
                          on_close=lambda: app.show_user(data))
                else:
                    popup(root, "¡Listo!", "Secuencia simulada.",
                          ACCENT, on_close=app.show_welcome)
            root.after(0, on_ui)

        app.show_loading_steps(uid, on_complete=on_complete)


# ── Crear cuenta ──────────────────────────────────────────────────────────────

class CreateFrame(_Base):
    def __init__(self, parent, app, rfid_id: str):
        super().__init__(parent, app)
        self._rfid   = rfid_id
        self._nombre = tk.StringVar()
        self._nombre.trace_add("write", self._on_change)
        self._build()

    def _build(self):
        tk.Frame(self, height=22, bg=BG).pack()
        tk.Label(self, text="Nueva cuenta",
                 font=F_TITLE, bg=BG, fg=FG).pack()
        tk.Label(self, text="Escribe tu nombre",
                 font=F_SMALL, bg=BG, fg=FG2).pack(pady=(2, 10))

        # ── Preview en tiempo real  (mejora 2) ───────────────────────────────
        self._preview = tk.Label(self, text="Hola, ... ♻",
                                  font=("Arial", 18, "italic"),
                                  bg=BG, fg=FG2)
        self._preview.pack()

        # ── Campo de texto con borde de validación  (mejora 3) ───────────────
        self._entry_border = tk.Frame(self, bg=FG2, pady=2, padx=2)
        self._entry_border.pack(padx=36, fill="x", pady=(6, 4))
        self._entry = tk.Entry(
            self._entry_border,
            textvariable=self._nombre,
            font=("Arial", 20), justify="center",
            bg=SURFACE2, fg=FG, insertbackground=FG,
            relief="flat", bd=6,
        )
        self._entry.pack(fill="x", ipady=6)

        # ── Teclado QWERTY  (mejora 1) ───────────────────────────────────────
        VirtualKeyboard(self, self._nombre).pack(pady=6)

        # ── Botón guardar ─────────────────────────────────────────────────────
        RoundedButton(self, "Guardar  ✓",
                      ACCENT, FG_AC, hover=ACCENT_H,
                      w=340, h=50,
                      command=self._confirmar).pack(pady=6)

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _on_change(self, *_):
        """Actualiza preview y color del borde según longitud del nombre."""
        nombre = self._nombre.get().strip()

        # Preview  (mejora 2)
        display = nombre if nombre else "..."
        self._preview.config(
            text=f"Hola, {display} ♻",
            fg=FG if nombre else FG2)

        # Color de borde  (mejora 3)
        if not nombre:
            color = FG2
        elif len(nombre) > 20:
            color = DANGER
        elif len(nombre) >= 2:
            color = ACCENT
        else:
            color = WARN
        self._entry_border.config(bg=color)

    def _confirmar(self):
        """Muestra diálogo de confirmación antes de guardar  (mejora 4)."""
        nombre = self._nombre.get().strip()
        root   = self.app.root

        if not nombre:
            popup(root, "Nombre vacío", "Escribe tu nombre.", WARN)
            return
        if len(nombre) > 20:
            popup(root, "Nombre largo", "Máximo 20 caracteres.", WARN)
            return

        ConfirmDialog(root, nombre,
                      on_confirm=lambda: self._guardar(nombre),
                      on_cancel=None)

    def _guardar(self, nombre: str):
        root, app = self.app.root, self.app
        rfid = self._rfid

        def tarea():
            try:
                _crear_usuario(rfid, nombre)
                root.after(0, lambda: popup(
                    root, "¡Cuenta creada!",
                    f"Bienvenido/a, {nombre}.",
                    ACCENT, on_close=app.show_welcome))
            except Exception as e:
                root.after(0, lambda: popup(
                    root, "Error al crear", str(e), DANGER))

        threading.Thread(target=tarea, daemon=True).start()


# ── Diálogo de confirmación de nombre  (mejora 4) ────────────────────────────

class ConfirmDialog(tk.Toplevel):
    """
    Modal con dos botones: "Sí, guardar" y "Corregir".
    No se auto-cierra — requiere acción explícita del usuario.
    """

    def __init__(self, root: tk.Tk, nombre: str, on_confirm, on_cancel):
        super().__init__(root)
        self.overrideredirect(True)
        self.configure(bg=SURFACE)
        self._on_confirm = on_confirm

        w, h = 340, 220
        ox = root.winfo_x() + (WIN_W - w) // 2
        oy = root.winfo_y() + (WIN_H - h) // 2
        self.geometry(f"{w}x{h}+{ox}+{oy}")

        tk.Frame(self, height=24, bg=SURFACE).pack()
        tk.Label(self, text="¿Tu nombre es correcto?",
                 font=F_BODY, bg=SURFACE, fg=FG).pack()
        tk.Frame(self, height=8,  bg=SURFACE).pack()
        tk.Label(self, text=nombre,
                 font=("Arial", 22, "bold"), bg=SURFACE, fg=ACCENT).pack()
        tk.Frame(self, height=20, bg=SURFACE).pack()

        btns = tk.Frame(self, bg=SURFACE)
        btns.pack()
        RoundedButton(btns, "Sí, guardar",
                      ACCENT, FG_AC, hover=ACCENT_H,
                      w=148, h=48, r=12,
                      command=self._confirm
                      ).pack(side="left", padx=6)
        RoundedButton(btns, "Corregir",
                      SURFACE2, FG2, hover=SURFACE,
                      w=148, h=48, r=12,
                      command=self._cancel
                      ).pack(side="left", padx=6)

        self.grab_set()

    def _confirm(self):
        self._close()
        if self._on_confirm:
            self._on_confirm()

    def _cancel(self):
        self._close()

    def _close(self):
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass


# ── Reciclar sin cuenta ───────────────────────────────────────────────────────

class AnonymousFrame(_Base):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        tk.Frame(self, height=100, bg=BG).pack()
        tk.Label(self, text="♻", font=("Arial", 96), bg=BG, fg=ACCENT).pack()
        tk.Frame(self, height=20, bg=BG).pack()
        tk.Label(self, text="Depositar objeto",
                 font=F_TITLE, bg=BG, fg=FG).pack()
        tk.Label(self, text="sin cuenta registrada",
                 font=F_SUB, bg=BG, fg=FG2).pack(pady=(4, 50))
        RoundedButton(self, "  Depositar ahora  ",
                      ACCENT, FG_AC, hover=ACCENT_H,
                      command=self._depositar).pack(pady=12)
        RoundedButton(self, "  Cancelar  ",
                      SURFACE, FG2, hover=SURFACE2,
                      command=self.app.show_welcome).pack(pady=8)

    def _depositar(self):
        root, app = self.app.root, self.app

        def on_complete(result):
            cat = result.get("objeto", "lata")
            root.after(0, lambda: popup(
                root, "¡Clasificado!",
                f"Objeto: {CAT_LABEL[cat]}\n(sin cuenta, sin puntos)",
                ACCENT, on_close=app.show_welcome))

        app.show_loading_steps(user_id=None, on_complete=on_complete)


# ── Pantalla de carga con pasos del robot  (mejora 7) ────────────────────────

class LoadingStepsFrame(_Base):
    """
    Muestra los pasos de la secuencia del robot animados.
    Corre _empezar() en un hilo mientras avanza la animación visual.
    Llama on_complete(result) cuando ambos terminan.
    """

    STEPS = [
        ("Moviendo a HOME",    380),
        ("Abriendo puerta",    460),
        ("Observando objeto",  700),
        ("Clasificando",       520),
        ("Depositando",        440),
        ("Regresando a HOME",  360),
    ]
    # Suma total ≈ 2860 ms > tiempo real de _empezar (≈200 ms) → siempre esperamos la visual

    def __init__(self, parent, app, user_id, on_complete):
        super().__init__(parent, app)
        self._user_id    = user_id
        self._on_complete = on_complete
        self._result     = None
        self._alive      = True
        self._current    = 0
        self._build()
        threading.Thread(target=self._work, daemon=True).start()
        self.after(200, self._advance)

    def destroy(self):
        self._alive = False
        super().destroy()

    def _work(self):
        self._result = _empezar(self._user_id)

    def _build(self):
        tk.Frame(self, height=50, bg=BG).pack()
        tk.Label(self, text="⚙ Robot en acción",
                 font=F_TITLE, bg=BG, fg=FG).pack()
        tk.Frame(self, height=28, bg=BG).pack()

        self._lbls = []
        for name, _ in self.STEPS:
            lbl = tk.Label(self, text=f"  ○  {name}",
                           font=F_BODY, bg=BG, fg=FG2, anchor="w")
            lbl.pack(fill="x", padx=60, pady=5)
            self._lbls.append(lbl)

    def _advance(self):
        if not self._alive:
            return
        i = self._current

        # Marcar el paso anterior como completado
        if i > 0:
            self._lbls[i-1].config(
                text=f"  ✓  {self.STEPS[i-1][0]}", fg=ACCENT)

        # Si terminaron todos los pasos visuales, esperar resultado
        if i >= len(self.STEPS):
            self._wait_result()
            return

        # Marcar paso actual como activo
        self._lbls[i].config(
            text=f"  ⟳  {self.STEPS[i][0]}...", fg=WARN)

        self._current += 1
        self.after(self.STEPS[i][1], self._advance)

    def _wait_result(self):
        if not self._alive:
            return
        if self._result is not None:
            self._finish()
        else:
            self.after(80, self._wait_result)

    def _finish(self):
        if not self._alive:
            return
        self._on_complete(self._result)


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
