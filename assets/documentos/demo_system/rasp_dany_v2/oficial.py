#!/usr/bin/env python3
"""
oficial.py  ·  HMI v2  ·  Clasificadora de reciclaje
Tkinter puro — sin PNGs.  Resolución 480 × 800.

Mejoras sobre v1:
  1. Teclado QWERTY táctil (shift · números · espacio)
  2. Preview en tiempo real del nombre mientras se escribe
  3. Validación visual inline del campo (borde rojo/verde)
  4. Confirmación explícita antes de guardar nombre
  5. Feedback del objeto: tipo + puntos actualizados
  6. Historial de depósitos de la sesión en el panel
  7. Pantalla de carga con pasos del robot animados
  8. Countdown de inactividad con botón "Seguir aquí"
"""
import threading
import time

import requests
import serial
import tkinter as tk

# ── Servidor ──────────────────────────────────────────────────────────────────
SERVIDOR  = "http://192.168.1.50:5000"

# ── Hardware ──────────────────────────────────────────────────────────────────
RFID_PORT    = "/dev/ttyUSB0"
RFID_BAUD    = 9600
MIN_RFID_LEN = 9    # IDs válidos tienen ≥ 9 caracteres; menos indica lectura truncada

# ── Ventana ───────────────────────────────────────────────────────────────────
WIN_W, WIN_H   = 480, 800
INACT_MS       = 30_000     # ms hasta mostrar countdown
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

# ── Fuentes ───────────────────────────────────────────────────────────────────
F_TITLE = ("Arial", 24, "bold")
F_SUB   = ("Arial", 14)
F_BODY  = ("Arial", 16)
F_BTN   = ("Arial", 15, "bold")
F_SMALL = ("Arial", 12)
F_KEY   = ("Arial", 15, "bold")

# ── Categorías ────────────────────────────────────────────────────────────────
CAT_LABEL = {"lata": "🥫 Lata", "vidrio": "🍶 Vidrio", "tetra": "📦 Tetra"}
CAT_COLOR = {"lata": "#60a5fa", "vidrio": "#a78bfa",   "tetra": "#fb923c"}


# ══════════════════════════════════════════════════════════════════════════════
# Capa de red
# ══════════════════════════════════════════════════════════════════════════════

def _check_server() -> bool:
    try:
        r = requests.get(f"{SERVIDOR}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _consulta(user_id: str) -> dict:
    r = requests.get(f"{SERVIDOR}/consulta/{user_id}", timeout=10)
    r.raise_for_status()
    return r.json()


def _existe(user_id: str) -> bool:
    r = requests.get(f"{SERVIDOR}/existe/{user_id}", timeout=10)
    return r.json().get("existe", False)


def _crear_usuario(user_id: str, nombre: str):
    r = requests.post(f"{SERVIDOR}/crear_usuario",
                      json={"user_id": user_id, "nombre": nombre},
                      timeout=10)
    r.raise_for_status()


def _empezar(user_id=None) -> dict:
    payload = {"start": 1}
    if user_id:
        payload["user_id"] = user_id
    r = requests.post(f"{SERVIDOR}/empezarObjeto", json=payload, timeout=8)
    r.raise_for_status()
    return r.json()


def _estado_ocupado() -> bool:
    try:
        r = requests.get(f"{SERVIDOR}/estado", timeout=3)
        return r.json().get("ocupado", False)
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# RFID
# ══════════════════════════════════════════════════════════════════════════════

def leer_rfid(callback, on_short=None):
    """
    Lee el lector RFID en hilo daemon. Reintenta si el ID tiene menos de
    MIN_RFID_LEN caracteres (lectura truncada). Llama on_short(id_parcial)
    en ese caso para que la UI muestre feedback.
    """
    def _tarea():
        ser = None
        try:
            ser = serial.Serial(RFID_PORT, RFID_BAUD, timeout=1)
            time.sleep(0.5)
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if len(line) < MIN_RFID_LEN:
                    print(f"[RFID] ID cortado ({len(line)} chars): '{line}', reintentando...")
                    if on_short:
                        try:
                            on_short(line)
                        except Exception:
                            pass
                    continue
                try:
                    callback(line)
                except Exception as e:
                    print(f"[RFID] callback error: {e}")
                break
        except Exception as e:
            print(f"[RFID] error puerto: {e}")
        finally:
            try:
                if ser and ser.is_open:
                    ser.close()
            except Exception:
                pass
    threading.Thread(target=_tarea, daemon=True).start()


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
    Prefijos btn_ en atributos propios para no pisar tk.Widget._w (path Tcl).
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
    """Teclado táctil QWERTY con shift, modo numérico y barra espaciadora."""

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

    _KW  = 41   # ancho tecla normal
    _KH  = 42   # altura tecla
    _KR  = 8    # radio esquinas
    _PAD = 2    # gap entre teclas

    def __init__(self, parent, string_var: tk.StringVar):
        super().__init__(parent, bg=BG)
        self._var   = string_var
        self._upper = True
        self._mode  = "alpha"
        self._draw()

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
                RoundedButton(row, disp, SURFACE2, FG,
                              hover=SURFACE,
                              w=self._KW, h=self._KH, r=self._KR,
                              command=lambda c=k: self._type(c)
                              ).pack(side="left", padx=self._PAD)
            if i == 2:
                self._add_backspace(row, w=52)

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
    def __init__(self, root: tk.Tk, app):
        super().__init__(root)
        self.overrideredirect(True)
        self.configure(bg=SURFACE)
        self._app   = app
        self._count = COUNTDOWN_SECS
        self._alive = True

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
# Diálogo de confirmación de nombre  (mejora 4)
# ══════════════════════════════════════════════════════════════════════════════

class ConfirmDialog(tk.Toplevel):
    """Modal con dos botones: Sí/Corregir. No se auto-cierra."""

    def __init__(self, root: tk.Tk, nombre: str, on_confirm, on_cancel=None):
        super().__init__(root)
        self.overrideredirect(True)
        self.configure(bg=SURFACE)
        self._on_confirm = on_confirm
        self._on_cancel  = on_cancel

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
        if self._on_cancel:
            self._on_cancel()

    def _close(self):
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# App — controlador de navegación
# ══════════════════════════════════════════════════════════════════════════════

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Clasificadora")
        self.root.geometry(f"{WIN_W}x{WIN_H}")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self._body  = tk.Frame(root, bg=BG)
        self._body.pack(fill=tk.BOTH, expand=True)

        self._frame = None
        self._timer = None

        # Sesión activa
        self.session_uid     = None
        self.session_history = []   # cats depositados en esta visita

        self.show_welcome()

    # ── swap ──────────────────────────────────────────────────────────────────

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
        if isinstance(self._frame, (WelcomeFrame, LoadingStepsFrame)):
            return
        try:
            CountdownOverlay(self.root, self)
        except Exception:
            pass

    # ── navegación ────────────────────────────────────────────────────────────

    def show_welcome(self):
        self.session_uid     = None
        self.session_history = []
        self._swap(WelcomeFrame)

    def show_scan(self, mode: str):
        if not _check_server():
            popup(self.root, "Sin conexión",
                  f"No hay conexión al servidor.\n{SERVIDOR}", DANGER)
            return
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
        if not _check_server():
            popup(self.root, "Sin conexión",
                  f"No hay conexión al servidor.\n{SERVIDOR}", DANGER)
            return
        self._swap(AnonymousFrame)

    def show_loading_steps(self, user_id, on_complete):
        self._swap(LoadingStepsFrame, user_id=user_id, on_complete=on_complete)


# ══════════════════════════════════════════════════════════════════════════════
# Frame base
# ══════════════════════════════════════════════════════════════════════════════

class _Base(tk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, bg=BG)
        self.app = app


# ══════════════════════════════════════════════════════════════════════════════
# Pantallas
# ══════════════════════════════════════════════════════════════════════════════

# ── Bienvenida ────────────────────────────────────────────────────────────────

class WelcomeFrame(_Base):
    """
    Pantalla de bienvenida.
    • Detecta RFID automáticamente:
        - Si el ID ya existe  → va directo al panel del usuario (login)
        - Si el ID no existe  → va directo a crear cuenta
    • Los botones siguen funcionando como antes.
    """

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._alive = True
        self._scanning = False          # evita disparos dobles
        self._build()
        leer_rfid(self._on_card, on_short=self._on_short_id)

    def destroy(self):
        self._alive = False
        super().destroy()

    def _build(self):
        tk.Frame(self, height=70, bg=BG).pack()
        tk.Label(self, text="♻", font=("Arial", 96), bg=BG, fg=ACCENT).pack()
        tk.Label(self, text="CLASIFICADORA",
                 font=F_TITLE, bg=BG, fg=FG).pack(pady=(8, 4))
        tk.Label(self, text="Sistema de reciclaje inteligente",
                 font=F_SUB, bg=BG, fg=FG2).pack()
        tk.Frame(self, height=56, bg=BG).pack()

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

        tk.Frame(self, height=40, bg=BG).pack()
        Divider(self).pack(fill="x", padx=40)
        self._rfid_lbl = tk.Label(
            self, text="Acerca tu tarjeta o elige una opción",
            font=F_SMALL, bg=BG, fg=FG2)
        self._rfid_lbl.pack(pady=12)

    # ── RFID desde bienvenida ──────────────────────────────────────────────

    def _on_card(self, rfid_id: str):
        """Callback del hilo RFID → despacha en hilo principal."""
        self.app.root.after(0, lambda: self._dispatch(rfid_id))

    def _dispatch(self, rfid_id: str):
        if not self._alive or self._scanning:
            return
        self._scanning = True
        try:
            self._rfid_lbl.config(text="🔄 Leyendo tarjeta...", fg=WARN)
        except tk.TclError:
            return

        if not _check_server():
            popup(self.app.root, "Sin conexión",
                  f"No hay conexión al servidor.\n{SERVIDOR}", DANGER,
                  on_close=self._reset_scan)
            return

        root, app = self.app.root, self.app

        def tarea():
            try:
                if _existe(rfid_id):
                    # Tarjeta registrada → login directo
                    data = _consulta(rfid_id)
                    root.after(0, lambda: app.show_user(data))
                else:
                    # Tarjeta nueva → crear cuenta
                    root.after(0, lambda: app.show_create(rfid_id))
            except Exception as e:
                root.after(0, lambda: popup(
                    root, "Error", str(e), DANGER,
                    on_close=self._reset_scan))

        threading.Thread(target=tarea, daemon=True).start()

    def _on_short_id(self, partial: str):
        """Feedback cuando el RFID devuelve un ID truncado."""
        self.app.root.after(0, lambda: self._safe_lbl_update(
            "⚠ Tarjeta no leída, acerca de nuevo", WARN))

    def _safe_lbl_update(self, text: str, color: str):
        try:
            self._rfid_lbl.config(text=text, fg=color)
        except tk.TclError:
            pass

    def _reset_scan(self):
        """Permite intentar de nuevo si hubo error."""
        self._scanning = False
        self._safe_lbl_update("Acerca tu tarjeta o elige una opción", FG2)
        leer_rfid(self._on_card, on_short=self._on_short_id)


# ── Escaneo RFID ──────────────────────────────────────────────────────────────

class ScanFrame(_Base):
    _ANIM = ["●  ○  ○", "○  ●  ○", "○  ○  ●"]

    def __init__(self, parent, app, mode: str):
        super().__init__(parent, app)
        self._mode  = mode
        self._tick  = 0
        self._alive = True
        self._build()
        leer_rfid(self._on_card, on_short=self._on_short_id)
        self._animate()

    def destroy(self):
        self._alive = False
        super().destroy()

    def _build(self):
        RoundedButton(self, "← Volver", SURFACE, FG2,
                      w=130, h=42, r=10,
                      command=self.app.show_welcome
                      ).pack(anchor="w", padx=20, pady=20)

        tk.Frame(self, height=50, bg=BG).pack()
        tk.Label(self, text="💳", font=("Arial", 80), bg=BG).pack()
        tk.Frame(self, height=20, bg=BG).pack()
        tk.Label(self, text="Acerca tu tarjeta",
                 font=F_TITLE, bg=BG, fg=FG).pack()
        subtitle = ("para iniciar sesión"
                    if self._mode == "login" else "para crear una cuenta")
        tk.Label(self, text=subtitle,
                 font=F_SUB, bg=BG, fg=FG2).pack(pady=(6, 50))
        self._anim_lbl = tk.Label(self, text=self._ANIM[0],
                                   font=F_BODY, bg=BG, fg=ACCENT)
        self._anim_lbl.pack()

    def _animate(self):
        if not self._alive:
            return
        self._tick = (self._tick + 1) % 3
        try:
            self._anim_lbl.config(text=self._ANIM[self._tick])
            self.after(500, self._animate)
        except tk.TclError:
            pass

    def _on_short_id(self, partial: str):
        """Feedback cuando el RFID devuelve un ID truncado."""
        def _update():
            if not self._alive:
                return
            try:
                self._anim_lbl.config(text="⚠ ID incompleto, acerca de nuevo", fg=WARN)
                self.after(2000, lambda: self._restore_anim())
            except tk.TclError:
                pass
        self.app.root.after(0, _update)

    def _restore_anim(self):
        try:
            self._anim_lbl.config(text=self._ANIM[self._tick], fg=ACCENT)
        except tk.TclError:
            pass

    def _on_card(self, rfid_id: str):
        self.app.root.after(0, lambda: self._dispatch(rfid_id))

    def _dispatch(self, rfid_id: str):
        if not self._alive:
            return
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
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    root.after(0, lambda: popup(
                        root, "No encontrado",
                        "Tarjeta sin cuenta.\nCrea una primero.",
                        DANGER, on_close=app.show_welcome))
                else:
                    root.after(0, lambda: popup(
                        root, "Error de servidor", str(e),
                        DANGER, on_close=app.show_welcome))
            except Exception as e:
                root.after(0, lambda: popup(
                    root, "Error de red", str(e),
                    DANGER, on_close=app.show_welcome))
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
                    root, "Error", str(e),
                    DANGER, on_close=app.show_welcome))
        threading.Thread(target=tarea, daemon=True).start()


# ── Panel del usuario ─────────────────────────────────────────────────────────

class UserFrame(_Base):
    def __init__(self, parent, app, data: dict):
        super().__init__(parent, app)
        self._info = data.get("respuesta_render", {})
        self._build()

    def _build(self):
        info = self._info

        # Header
        hdr = tk.Frame(self, bg=SURFACE, height=106)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"Hola, {info.get('nombre', '—')}",
                 font=F_TITLE, bg=SURFACE, fg=FG).pack(pady=(22, 2))
        tk.Label(hdr, text=f"ID: {info.get('user_id', '—')}",
                 font=F_SMALL, bg=SURFACE, fg=FG2).pack()

        # Puntos
        tk.Frame(self, height=18, bg=BG).pack()
        tk.Label(self, text=str(info.get("total", 0)),
                 font=("Arial", 68, "bold"), bg=BG, fg=ACCENT).pack()
        tk.Label(self, text="puntos totales",
                 font=F_SUB, bg=BG, fg=FG2).pack()

        # Desglose
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

        # Historial de sesión  (mejora 6)
        hist = self.app.session_history
        if hist:
            tk.Frame(self, height=10, bg=BG).pack()
            Divider(self).pack(fill="x", padx=40)
            tk.Label(self, text="Esta visita:",
                     font=F_SMALL, bg=BG, fg=FG2).pack(pady=(6, 2))
            icons  = "  ".join(CAT_LABEL[c].split()[0] for c in hist[-6:])
            suffix = f"  (+{len(hist)-6} más)" if len(hist) > 6 else ""
            tk.Label(self, text=icons + suffix,
                     font=("Arial", 22), bg=BG, fg=FG).pack()
            Divider(self).pack(fill="x", padx=40, pady=(6, 0))

        # Acciones
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
            # Intentar leer el objeto clasificado desde la respuesta del servidor
            obj = result.get("objeto") if result else None
            # Refrescar datos del usuario
            def refrescar():
                try:
                    data = _consulta(uid)
                    info = data.get("respuesta_render", {})
                    total = info.get("total", "?")
                    if obj and obj in CAT_LABEL:
                        app.session_history.append(obj)
                        msg = f"Depositaste: {CAT_LABEL[obj]}\nTotal ahora: {total} puntos"
                    else:
                        msg = f"Secuencia completada.\nTotal ahora: {total} puntos"
                    root.after(0, lambda: popup(
                        root, "¡Clasificado!", msg, ACCENT,
                        on_close=lambda: app.show_user(data)))
                except Exception:
                    root.after(0, lambda: popup(
                        root, "¡Secuencia completada!",
                        "Vuelve a escanear tu tarjeta\npara ver tus puntos actualizados.",
                        ACCENT, on_close=app.show_welcome))
            threading.Thread(target=refrescar, daemon=True).start()

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
        RoundedButton(self, "← Volver", SURFACE, FG2,
                      w=130, h=42, r=10,
                      command=self.app.show_welcome
                      ).pack(anchor="w", padx=20, pady=(14, 0))
        tk.Label(self, text="Nueva cuenta",
                 font=F_TITLE, bg=BG, fg=FG).pack()
        tk.Label(self, text="Escribe tu nombre",
                 font=F_SMALL, bg=BG, fg=FG2).pack(pady=(2, 10))

        # Preview en tiempo real  (mejora 2)
        self._preview = tk.Label(self, text="Hola, ... ♻",
                                  font=("Arial", 17, "italic"),
                                  bg=BG, fg=FG2)
        self._preview.pack()

        # Campo con borde de validación  (mejora 3)
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

        # Teclado QWERTY  (mejora 1)
        VirtualKeyboard(self, self._nombre).pack(pady=6)

        # Botón guardar
        RoundedButton(self, "Guardar  ✓",
                      ACCENT, FG_AC, hover=ACCENT_H,
                      w=340, h=50,
                      command=self._confirmar).pack(pady=6)

    def _on_change(self, *_):
        nombre = self._nombre.get().strip()
        # Preview  (mejora 2)
        self._preview.config(
            text=f"Hola, {nombre} ♻" if nombre else "Hola, ... ♻",
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
        nombre = self._nombre.get().strip()
        root   = self.app.root
        if not nombre:
            popup(root, "Nombre vacío", "Escribe tu nombre.", WARN)
            return
        if len(nombre) > 20:
            popup(root, "Nombre largo", "Máximo 20 caracteres.", WARN)
            return
        # Confirmación explícita  (mejora 4)
        ConfirmDialog(root, nombre,
                      on_confirm=lambda: self._guardar(nombre))

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
            obj = result.get("objeto") if result else None
            if obj and obj in CAT_LABEL:
                msg = f"Objeto: {CAT_LABEL[obj]}\n(sin cuenta, sin puntos)"
            else:
                msg = "Objeto clasificado correctamente."
            root.after(0, lambda: popup(
                root, "¡Clasificado!", msg,
                ACCENT, on_close=app.show_welcome))

        app.show_loading_steps(user_id=None, on_complete=on_complete)


# ── Pantalla de carga con pasos del robot  (mejora 7) ────────────────────────

class LoadingStepsFrame(_Base):
    """
    Lanza /empezarObjeto y muestra los pasos en tiempo real via polling
    al endpoint /estado_detalle del servidor.

    El servidor expone el campo 'paso' que mapea 1:1 a cada fila de la lista.
    Cuando el servidor dice {ocupado:false, paso:'LISTO'} y ya tenemos
    la respuesta de _empezar, se llama on_complete(result).
    """

    # (texto visible, clave del servidor)
    STEPS = [
        ("Moviendo a HOME",   "HOME"),
        ("Abriendo puerta",   "PUERTA"),
        ("Observando objeto", "OBSERVACION"),
        ("Clasificando",      "CLASIFICANDO"),
        ("Depositando",       "DEPOSITANDO"),
        ("Regresando a HOME", "REGRESANDO"),
    ]

    # Mapeo clave → índice
    KEY_TO_IDX = {key: i for i, (_, key) in enumerate(STEPS)}

    POLL_MS = 600   # ms entre consultas

    def __init__(self, parent, app, user_id, on_complete):
        super().__init__(parent, app)
        self._user_id     = user_id
        self._on_complete = on_complete
        self._result      = None
        self._alive       = True
        self._last_idx    = -1      # último índice marcado como activo
        self._finishing   = False
        self._build()
        threading.Thread(target=self._work, daemon=True).start()
        self.after(self.POLL_MS, self._poll)

    def destroy(self):
        self._alive = False
        super().destroy()

    # ── UI ────────────────────────────────────────────────────────────────

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

    def _set_row(self, i: int, state: str):
        """state: 'done' | 'active' | 'pending'"""
        if not self._alive:
            return
        name = self.STEPS[i][0]
        try:
            if state == "done":
                self._lbls[i].config(text=f"  ✓  {name}", fg=ACCENT)
            elif state == "active":
                self._lbls[i].config(text=f"  ⟳  {name}...", fg=WARN)
            else:
                self._lbls[i].config(text=f"  ○  {name}", fg=FG2)
        except tk.TclError:
            pass

    def _update_to(self, idx: int):
        """Marca todos los pasos anteriores como done, el idx como active."""
        if idx <= self._last_idx:
            return   # no retroceder
        self._last_idx = idx
        for i in range(len(self.STEPS)):
            if i < idx:
                self._set_row(i, "done")
            elif i == idx:
                self._set_row(i, "active")

    def _complete_all(self):
        for i in range(len(self.STEPS)):
            self._set_row(i, "done")

    # ── Polling ───────────────────────────────────────────────────────────

    def _work(self):
        """Hilo: lanza la secuencia y espera a que termine."""
        try:
            resp = _empezar(self._user_id)
            for _ in range(240):       # max 120 s
                time.sleep(0.5)
                if not _estado_ocupado():
                    break
            self._result = resp
        except Exception as e:
            self._result = {"error": str(e)}

    def _poll(self):
        """Hilo principal: consulta /estado_detalle y actualiza los pasos."""
        if not self._alive or self._finishing:
            return

        try:
            r    = requests.get(f"{SERVIDOR}/estado_detalle", timeout=2)
            data = r.json()
            paso    = data.get("paso", "")
            ocupado = data.get("ocupado", True)

            idx = self.KEY_TO_IDX.get(paso, -1)
            if idx >= 0:
                self._update_to(idx)

            # ¿Terminó? → secuencia no ocupada + tenemos la respuesta de _empezar
            if not ocupado and self._result is not None and paso in ("LISTO", ""):
                self._finishing = True
                self._complete_all()
                self.after(500, self._finish)
                return

        except Exception:
            pass   # server no alcanzable → mantener estado actual

        self.after(self.POLL_MS, self._poll)

    def _finish(self):
        if not self._alive:
            return
        if "error" in (self._result or {}):
            popup(self.app.root, "Error",
                  self._result["error"], DANGER,
                  on_close=self.app.show_welcome)
        else:
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
