#!/usr/bin/env python3
"""
main.py — Servidor de visión en la Raspberry Pi (Rasp Sebas)

Arquitectura:
  - Hilo PRINCIPAL : loop OpenCV (obligatorio en Linux/X11)
  - Hilo BACKGROUND: Flask HTTP server (threaded=True)
  - Comunicación   : _cmd_queue (Flask → main) + threading.Event (resultado)

Comportamiento:
  - Inactivo   → carrusel de videos/imágenes en pantalla completa
  - /identify  → para carrusel, inferencia, devuelve {"object": "..."}
  - /identify_window → igual pero mostrando cámara en pantalla
  - Al terminar → retoma carrusel

Endpoints:
  GET /identify                → identifica objeto (headless)
  GET /identify_window         → identifica mostrando cámara
  GET /robot_pov               → cámara en vivo sin inferencia
  GET /show_media?name=X&duration=Y → muestra archivo específico
  GET /display_on              → reabre ventana fullscreen
  GET /display_off             → pinta negro (ventana sigue abierta)
  GET /display_close           → destruye ventana (libera escritorio)
  GET /health                  → estado del servidor
"""

import os
import sys
import time
import datetime
import threading
import traceback
import queue

# Forzar variable DISPLAY antes de importar cv2 (necesario en Raspberry Pi)
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":0"

import numpy as np
import cv2
from flask import Flask, request, jsonify

# =============================================================================
#  CONFIG — editar aquí
# =============================================================================

CAM_INDEX        = 0
FRAME_SIZE       = (640, 480)
NUM_THREADS      = 4
VERBOSE          = False

HOST             = "192.168.1.122"
PORT             = 5000
PC_URL           = "http://192.168.1.50:5000"

IDENT_DURATION_S = 5.0
DISPLAY_SIZE     = (1920, 1080)   # resolución de la TV
WINDOW_MAIN_NAME = "ROBOT_DISPLAY"

MODEL_PATH       = "model_unquant.tflite"
LABELS_PATH      = "labels.txt"

# Archivos del carrusel. Solo se usan los que existan en el directorio del script.
PLAYLIST_CONFIG = [
    ("video1.mp4",          17.0),
    ("Topologia_blanco.jpg", 10.0),
    ("video2.mp4",          17.0),
    ("Topologia_negro.jpg",  10.0),
    ("video3.mp4",          17.0),
    ("QR_documentación.jpg", 10.0),
    ("leaderboard.png",      12.0),
]

# Pon True para deshabilitar toda ventana OpenCV (útil al depurar sin monitor)
HEADLESS = False

# =============================================================================
#  Estado global
# =============================================================================

app = Flask(__name__)

interpreter  = None
inp_details  = None
out_details  = None
OUT_SIZE     = None
LABELS       = None
CAP          = None
IS_QUANT     = False
IN_H         = None
IN_W         = None
MAIN_BLACK_FRAME = None
PLAYLIST     = []
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))

# Cola de comandos: Flask → hilo principal OpenCV
# maxsize=1: el 2° request espera a que el 1° se consuma antes de entrar
_cmd_queue = queue.Queue(maxsize=1)
_running   = True


# =============================================================================
#  Helpers generales
# =============================================================================

def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")

def abs_path(fname):
    return fname if os.path.isabs(fname) else os.path.join(BASE_DIR, fname)


# =============================================================================
#  Cámara
# =============================================================================

def open_camera(max_retries=10, wait_s=2.0):
    global CAP
    import platform
    backend = cv2.CAP_V4L2 if platform.system().lower() == "linux" else 0
    for attempt in range(max_retries):
        print(f"[CAM] Intentando abrir cámara (intento {attempt+1}/{max_retries})...")
        try:
            if CAP is not None:
                CAP.release()
        except Exception:
            pass
        CAP = cv2.VideoCapture(CAM_INDEX, backend)
        CAP.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_SIZE[0])
        CAP.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_SIZE[1])
        time.sleep(0.2)
        if CAP.isOpened():
            warm_ok, _ = CAP.read()
            print(f"[CAM] Abierta. Primer frame ok: {warm_ok}")
            return True
        print("[CAM] Fallo, reintentando...")
        time.sleep(wait_s)
    print("[CAM][ERR] No se pudo abrir la cámara.")
    CAP = None
    return False


# =============================================================================
#  TFLite
# =============================================================================

def clean_label(raw: str) -> str:
    if not raw:
        return ""
    parts = raw.split()
    label = " ".join(parts[1:]) if len(parts) >= 2 and parts[0].isdigit() else raw
    return label.strip().lower()


def resolve_label(index, labels, out_size):
    if not labels:
        return str(index)
    n = len(labels)
    if n == out_size:         mapped = index
    elif n == out_size - 1:   mapped = index - 1
    elif n == out_size + 1:   mapped = index + 1
    else:                     mapped = max(0, min(index, n - 1))
    return labels[mapped] if 0 <= mapped < n else str(index)


def load_interpreter(threads):
    try:
        from tflite_runtime.interpreter import Interpreter
        print("[ok] tflite_runtime encontrado")
        return Interpreter, "tflite_runtime"
    except Exception as e1:
        print("[warn] tflite_runtime no disponible:", e1)
        from tensorflow.lite import Interpreter
        print("[ok] tensorflow.lite (fallback)")
        return Interpreter, "tensorflow"


def infer_frame(frame):
    img = cv2.resize(frame, (IN_W, IN_H))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.uint8) if IS_QUANT else (img.astype(np.float32) / 127.5) - 1.0
    img = np.expand_dims(img, axis=0)
    interpreter.set_tensor(inp_details["index"], img)
    interpreter.invoke()
    pred = np.squeeze(interpreter.get_tensor(out_details["index"]))
    i    = int(np.argmax(pred))
    conf = float(pred[i]) if pred.ndim == 1 else float(np.max(pred))
    size = OUT_SIZE if OUT_SIZE else (len(LABELS) if LABELS else i + 1)
    return resolve_label(i, LABELS, size), conf


# =============================================================================
#  Display — solo llamar desde hilo principal
# =============================================================================

def init_display():
    """Crea/recrea la ventana fullscreen. Llamar SOLO desde hilo principal."""
    global MAIN_BLACK_FRAME
    if HEADLESS:
        return
    MAIN_BLACK_FRAME = np.zeros((DISPLAY_SIZE[1], DISPLAY_SIZE[0], 3), dtype=np.uint8)
    try:
        cv2.namedWindow(WINDOW_MAIN_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_MAIN_NAME, DISPLAY_SIZE[0], DISPLAY_SIZE[1])
        cv2.moveWindow(WINDOW_MAIN_NAME, 0, 0)
        cv2.setWindowProperty(WINDOW_MAIN_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow(WINDOW_MAIN_NAME, MAIN_BLACK_FRAME)
        cv2.waitKey(30)
        print("[display] Ventana fullscreen lista")
    except Exception as e:
        print("[display][WARN]", e)


def _show(frame):
    """imshow seguro: si la ventana no existe la recrea."""
    if HEADLESS or frame is None:
        return
    try:
        vis = cv2.getWindowProperty(WINDOW_MAIN_NAME, cv2.WND_PROP_VISIBLE)
    except Exception:
        vis = -1
    if vis < 1:
        init_display()
    try:
        cv2.imshow(WINDOW_MAIN_NAME, frame)
    except Exception as e:
        print("[display][WARN] imshow:", e)


def show_black():
    if MAIN_BLACK_FRAME is not None:
        _show(MAIN_BLACK_FRAME)
        cv2.waitKey(1)


# =============================================================================
#  Leaderboard — descarga imagen desde la PC antes de mostrarla en carrusel
# =============================================================================

def _fetch_leaderboard():
    """Descarga leaderboard.png desde la PC. Silencioso si falla (sin conexión)."""
    try:
        import requests as _req
        r = _req.get(f"{PC_URL}/leaderboard_img", timeout=5)
        if r.status_code == 200:
            with open(abs_path("leaderboard.png"), "wb") as f:
                f.write(r.content)
            print("[leaderboard] Imagen actualizada desde PC")
        else:
            print(f"[leaderboard] PC respondió {r.status_code}")
    except Exception as e:
        print(f"[leaderboard] fallo descarga: {e}")


# =============================================================================
#  CarouselState — gestión frame a frame del carrusel (hilo principal)
# =============================================================================

class CarouselState:
    def __init__(self):
        self.idx      = -1
        self.deadline = 0.0
        self.cap      = None   # VideoCapture activo
        self.img      = None   # imagen estática redimensionada

    def start(self):
        if PLAYLIST:
            self.idx = 0
            self._load()

    def _load(self):
        self._release_cap()
        self.img = None
        if not PLAYLIST:
            return
        name, dur = PLAYLIST[self.idx]
        if name == "leaderboard.png":
            _fetch_leaderboard()
        self.deadline = time.time() + dur
        fpath = abs_path(name)
        ext   = os.path.splitext(fpath)[1].lower()
        if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
            raw = cv2.imread(fpath)
            if raw is not None:
                self.img = cv2.resize(raw, DISPLAY_SIZE)
                print(f"[carrusel] Imagen cargada: {name}")
            else:
                print(f"[carrusel][WARN] No se pudo leer: {name}")
        elif ext in (".mp4", ".avi", ".mov", ".mkv"):
            self.cap = cv2.VideoCapture(fpath)
            if self.cap.isOpened():
                print(f"[carrusel] Video abierto: {name}")
            else:
                print(f"[carrusel][WARN] No se pudo abrir: {name}")
                self._release_cap()

    def tick(self):
        """Muestra un frame. Devuelve True si hay que avanzar al siguiente archivo."""
        if not PLAYLIST or HEADLESS:
            return False
        if time.time() >= self.deadline:
            return True
        if self.img is not None:
            _show(self.img)
            return False
        if self.cap is not None and self.cap.isOpened():
            ok, frame = self.cap.read()
            if not ok:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self.cap.read()
            if ok:
                _show(cv2.resize(frame, DISPLAY_SIZE))
            return False
        # Nada cargado → avanzar
        return True

    def advance(self):
        if not PLAYLIST:
            return
        self.idx = (self.idx + 1) % len(PLAYLIST)
        self._load()

    def _release_cap(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def release(self):
        self._release_cap()
        self.img = None


# =============================================================================
#  Operaciones de display — ejecutadas en hilo principal
# =============================================================================

def _run_identify(duration_s: float, show_gui: bool) -> dict:
    global CAP
    counts, conf_acc = {}, {}
    frames_total = 0
    t0 = time.time()

    if CAP is None or not CAP.isOpened():
        if not open_camera(max_retries=5, wait_s=1.0):
            return {"label_mode": "bg", "error": "cámara no disponible", "frames": 0}

    while time.time() - t0 < duration_s:
        ok, frame = CAP.read()
        if not ok:
            if not open_camera(max_retries=3, wait_s=0.5):
                break
            continue

        label_txt, conf = infer_frame(frame)
        counts[label_txt]   = counts.get(label_txt, 0) + 1
        conf_acc[label_txt] = conf_acc.get(label_txt, 0.0) + conf
        frames_total += 1

        if show_gui:
            view = frame.copy()
            cv2.putText(view, f"{label_txt}  {conf*100:.1f}%",
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (0, 255, 0), 2, cv2.LINE_AA)
            for i, (lbl, cnt) in enumerate(sorted(counts.items(), key=lambda kv: -kv[1])):
                frac = cnt / max(frames_total, 1)
                cv2.putText(view, f"  {lbl}: {cnt} ({frac*100:.0f}%)",
                            (10, 80 + 30 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            _show(cv2.resize(view, DISPLAY_SIZE))

        cv2.waitKey(1)

    show_black()
    if not counts:
        return {"label_mode": "bg", "counts": {}, "frames": 0, "duration_s": time.time() - t0}

    label_mode = max(counts, key=lambda k: counts[k])
    return {
        "label_mode": label_mode,
        "counts":     counts,
        "avg_conf":   {l: conf_acc[l] / counts[l] for l in counts},
        "frames":     frames_total,
        "duration_s": round(time.time() - t0, 2),
    }


def _run_robot_pov(duration_s: float):
    """Muestra cámara en vivo. Sale antes si llega un nuevo comando al queue."""
    global CAP
    if CAP is None or not CAP.isOpened():
        open_camera(max_retries=3, wait_s=0.5)
    t0 = time.time()
    while time.time() - t0 < duration_s:
        if not _cmd_queue.empty():   # comando prioritario esperando → salir
            break
        if CAP is None or not CAP.isOpened():
            break
        ok, frame = CAP.read()
        if not ok:
            break
        _show(cv2.resize(frame, DISPLAY_SIZE))
        cv2.waitKey(1)
    show_black()


def _run_show_media(name: str, duration_s: float):
    fpath = abs_path(name)
    if not os.path.exists(fpath):
        raise FileNotFoundError(f"Archivo no encontrado: {fpath}")
    ext      = os.path.splitext(fpath)[1].lower()
    is_image = ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff")
    is_video = ext in (".mp4", ".avi", ".mov", ".mkv")
    if not (is_image or is_video):
        raise ValueError(f"Tipo no soportado: {ext}")
    t0 = time.time()
    if is_image:
        img = cv2.imread(fpath)
        if img is None:
            raise RuntimeError(f"No se pudo leer: {fpath}")
        big = cv2.resize(img, DISPLAY_SIZE)
        while time.time() - t0 < duration_s:
            _show(big)
            cv2.waitKey(1)
    else:
        cap = cv2.VideoCapture(fpath)
        if not cap.isOpened():
            raise RuntimeError(f"No se pudo abrir video: {fpath}")
        try:
            while time.time() - t0 < duration_s:
                ok, frame = cap.read()
                if not ok:
                    break
                _show(cv2.resize(frame, DISPLAY_SIZE))
                cv2.waitKey(1)
        finally:
            cap.release()
    show_black()


# =============================================================================
#  Comunicación Flask → hilo principal
# =============================================================================

def _fire_cmd(cmd_type: str, **params):
    """
    Envía un comando al loop OpenCV SIN esperar resultado (fire-and-forget).
    Si la cola está llena (otro comando en curso) lo descarta silenciosamente.
    """
    done   = threading.Event()
    cmd    = {"type": cmd_type, "params": params, "done": done, "result": {}}
    try:
        _cmd_queue.put(cmd, block=False)
    except queue.Full:
        pass


def _post_cmd(cmd_type: str, timeout: float = 60.0, **params) -> dict:
    """
    Envía un comando al hilo principal OpenCV y espera el resultado.
    Bloquea hasta que el hilo principal lo procese o hasta timeout.
    """
    done   = threading.Event()
    result = {}
    cmd    = {"type": cmd_type, "params": params, "done": done, "result": result}
    try:
        _cmd_queue.put(cmd, block=True, timeout=timeout)
    except queue.Full:
        return {"error": "El display está ocupado, intenta de nuevo"}
    wait_timeout = params.get("duration", 10.0) + 15.0
    if not done.wait(timeout=wait_timeout):
        return {"error": "Timeout esperando respuesta del display"}
    return result


# =============================================================================
#  Flask routes
# =============================================================================

@app.route("/identify", methods=["GET"])
def identify():
    if CAP is None or not CAP.isOpened():
        if not open_camera(max_retries=3, wait_s=1.0):
            return jsonify({"error": "cámara no disponible"}), 500
    try:
        duration_s = max(float(request.args.get("duration", IDENT_DURATION_S)), 0.5)
    except Exception:
        duration_s = IDENT_DURATION_S
    result = _post_cmd("identify", duration=duration_s, show_gui=False)
    if "error" in result:
        return jsonify(result), 500
    return jsonify({"object": clean_label(result.get("label_mode", "bg")),
                    "frames": result.get("frames", 0),
                    "counts": result.get("counts", {})}), 200


@app.route("/identify_window", methods=["GET"])
def identify_window():
    try:
        duration_s = max(float(request.args.get("duration", IDENT_DURATION_S)), 0.5)
    except Exception:
        duration_s = IDENT_DURATION_S
    result = _post_cmd("identify", duration=duration_s, show_gui=True)
    if "error" in result:
        return jsonify(result), 500
    return jsonify({"object": clean_label(result.get("label_mode", "bg")),
                    "frames": result.get("frames", 0),
                    "counts": result.get("counts", {})}), 200


@app.route("/robot_pov", methods=["GET"])
def robot_pov():
    try:
        duration_s = float(request.args.get("duration", 5.0))
    except Exception:
        duration_s = 5.0
    result = _post_cmd("robot_pov", duration=duration_s)
    return (jsonify({"ok": True}), 200) if "error" not in result \
           else (jsonify(result), 500)


@app.route("/show_media", methods=["GET"])
def api_show_media():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Falta parámetro 'name'"}), 400
    try:
        duration_s = float(request.args.get("duration", 17.0))
    except Exception:
        duration_s = 17.0
    result = _post_cmd("show_media", duration=duration_s, name=name)
    return (jsonify({"ok": True}), 200) if "error" not in result \
           else (jsonify(result), 500)


@app.route("/robot_pov_bg", methods=["GET"])
def robot_pov_bg():
    """
    Inicia robot POV en background sin bloquear al llamador.
    Se interrumpe automáticamente si llega otro comando (/identify, /display_off, etc.).
    Úsalo desde el orquestador justo antes de que el robot empiece a recoger.
    """
    try:
        duration_s = float(request.args.get("duration", 90.0))
    except Exception:
        duration_s = 90.0
    _fire_cmd("robot_pov", duration=duration_s)
    return jsonify({"ok": True, "duration": duration_s}), 200


@app.route("/display_on", methods=["GET"])
def api_display_on():
    result = _post_cmd("display_on", timeout=10)
    return jsonify({"ok": True, "display": "on"}), 200


@app.route("/display_off", methods=["GET"])
def api_display_off():
    result = _post_cmd("display_off", timeout=10)
    return jsonify({"ok": True, "display": "off (black)"}), 200


@app.route("/display_close", methods=["GET"])
def api_display_close():
    result = _post_cmd("display_close", timeout=10)
    return jsonify({"ok": True, "display": "closed"}), 200


@app.route("/health", methods=["GET"])
def health():
    cam_ok = CAP is not None and CAP.isOpened()
    return jsonify({
        "ok":             True,
        "time":           now_iso(),
        "camera_open":    cam_ok,
        "labels_loaded":  len(LABELS) if LABELS else 0,
        "playlist":       [n for n, _ in PLAYLIST],
        "headless":       HEADLESS,
    }), 200


# =============================================================================
#  Loop principal OpenCV — corre en el hilo MAIN
# =============================================================================

def opencv_main_loop():
    global _running

    carousel     = CarouselState()
    window_open  = not HEADLESS

    init_display()
    carousel.start()
    print("[main] Loop OpenCV iniciado")

    while _running:
        # --- Teclado (q / Escape cierran la ventana sin detener Flask) ---
        if not HEADLESS:
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                print("[main] Tecla q/Esc → cerrando ventana")
                try:
                    cv2.destroyAllWindows()
                    cv2.waitKey(1)
                except Exception:
                    pass
                window_open = False

        # --- Nuevo comando de Flask ---
        try:
            cmd = _cmd_queue.get_nowait()
        except queue.Empty:
            cmd = None

        if cmd is not None:
            carousel.release()    # libera VideoCapture del carrusel
            ct = cmd["type"]
            p  = cmd["params"]
            try:
                if ct == "identify":
                    if not window_open and p.get("show_gui"):
                        init_display(); window_open = True
                    r = _run_identify(p.get("duration", IDENT_DURATION_S),
                                      p.get("show_gui", False))
                    cmd["result"].update(r)

                elif ct == "robot_pov":
                    if not window_open:
                        init_display(); window_open = True
                    _run_robot_pov(p.get("duration", 5.0))

                elif ct == "show_media":
                    if not window_open:
                        init_display(); window_open = True
                    try:
                        _run_show_media(p["name"], p.get("duration", 17.0))
                    except Exception as e:
                        cmd["result"]["error"] = str(e)

                elif ct == "display_on":
                    init_display(); window_open = True

                elif ct == "display_off":
                    show_black()

                elif ct == "display_close":
                    try:
                        cv2.destroyAllWindows()
                        cv2.waitKey(1)
                    except Exception:
                        pass
                    window_open = False

            except Exception as e:
                print(f"[main][ERR] Comando '{ct}':", traceback.format_exc())
                cmd["result"]["error"] = str(e)
            finally:
                cmd["done"].set()

            # Reinicia carrusel tras el comando
            carousel.start()
            continue

        # --- Carrusel ---
        if window_open and PLAYLIST:
            if carousel.tick():
                carousel.advance()
        else:
            time.sleep(0.02)   # sin ventana o sin playlist: espera pasiva


# =============================================================================
#  Inicialización
# =============================================================================

def _ensure_test_media():
    """Crea una imagen de prueba si no existe ningún archivo de media."""
    any_exists = any(os.path.exists(abs_path(n)) for n, _ in PLAYLIST_CONFIG)
    if any_exists:
        return
    test_path = abs_path("test_slide.jpg")
    if not os.path.exists(test_path):
        img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        img[:] = (30, 60, 30)
        cv2.putText(img, "ROBOT CLASIFICADOR", (200, 500),
                    cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 220, 80), 10, cv2.LINE_AA)
        cv2.putText(img, "Sistema listo", (550, 650),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.5, (200, 200, 200), 5, cv2.LINE_AA)
        cv2.imwrite(test_path, img)
        print("[carrusel] Imagen de prueba generada: test_slide.jpg")
    # Agrega a PLAYLIST_CONFIG para que se use
    PLAYLIST_CONFIG.append(("test_slide.jpg", 10.0))


def init_vision():
    global interpreter, inp_details, out_details, OUT_SIZE
    global LABELS, IS_QUANT, IN_H, IN_W, PLAYLIST

    model_path  = abs_path(MODEL_PATH)
    labels_path = abs_path(LABELS_PATH)

    print("[info] model:", model_path)
    print("[info] labels:", labels_path)
    print("[info] cámara:", CAM_INDEX, "hilos:", NUM_THREADS)

    # Labels
    if os.path.exists(labels_path):
        with open(labels_path, encoding="utf-8") as f:
            LABELS = [l.strip() for l in f if l.strip()]
        print(f"[ok] {len(LABELS)} labels: {LABELS}")
    else:
        print("[warn] labels.txt no encontrado")

    # TFLite
    InterpreterCls, backend = load_interpreter(NUM_THREADS)
    interpreter = InterpreterCls(model_path=model_path, num_threads=NUM_THREADS)
    interpreter.allocate_tensors()
    inp_details = interpreter.get_input_details()[0]
    out_details = interpreter.get_output_details()[0]
    in_shape = inp_details["shape"]
    IN_H = int(in_shape[1]); IN_W = int(in_shape[2])
    IS_QUANT = (inp_details["dtype"] == np.uint8)
    try:
        s = out_details["shape"]
        OUT_SIZE = int(s[1]) if len(s) == 2 else (int(s[0]) if len(s) == 1 else None)
    except Exception:
        OUT_SIZE = None
    print(f"[ok] backend:{backend}  input:({IN_W}×{IN_H})  quant:{IS_QUANT}")

    # Cámara
    if not open_camera(max_retries=10, wait_s=2.0):
        raise RuntimeError("No se pudo abrir la cámara")

    # Playlist
    _ensure_test_media()
    PLAYLIST = [(n, d) for n, d in PLAYLIST_CONFIG
                if os.path.exists(abs_path(n))]
    if PLAYLIST:
        print(f"[carrusel] {len(PLAYLIST)} archivo(s): {[n for n,_ in PLAYLIST]}")
    else:
        print("[carrusel] Sin archivos de media — pantalla negra")


def _flask_thread():
    print(f"[Flask] Escuchando en http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False, threaded=True, use_reloader=False)


def main():
    init_vision()
    print(f"[info] Servidor: http://{HOST}:{PORT}")
    print(f"[info] Health:   http://{HOST}:{PORT}/health")
    print("[info] Para cerrar la ventana: tecla Q o Escape")
    print("[info] Para apagar el servidor: Ctrl+C en la terminal")

    # Flask en hilo background (OpenCV DEBE correr en hilo principal en Linux)
    ft = threading.Thread(target=_flask_thread, daemon=True, name="flask")
    ft.start()

    # OpenCV loop en hilo principal
    opencv_main_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[info] Ctrl+C — saliendo...")
        _running = False
        sys.exit(0)
    except Exception:
        print("[EXCEPTION]", traceback.format_exc())
        time.sleep(3)
        sys.exit(1)
    finally:
        try:
            if CAP is not None:
                CAP.release()
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
