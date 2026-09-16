"""
orchestrator.py — Secuencia completa de clasificación de residuos.

Basado en jetson/main.py, con hooks de modo demo en cada paso.
Cada función de hardware se puede saltar individualmente desde config.DEMO.

Secuencia normal:
  1) UR3 a HOME
  2) Abrir puerta PLC, STOP 2 s, cerrar puerta
  3) Ejecutar rutObservacion.urp
  4) Identificar objeto (GET /identify a Rasp Sebas)
  5) Si bg → HOME y terminar
  6) Recolección + depósito según objeto
  7) (Opcional) sumar punto al usuario en la BD local
"""

import time
import threading
import requests

import config
from config import DEMO, RASP_SEBAS_URL
from robot_control import move_home, run_urp_sequence
from plc_door import door_open_stop_close

# ---------------------------------------------------------------------------
# Paso actual de la secuencia (para el HMI y panel de debug)
# ---------------------------------------------------------------------------

_current_step = ""
_step_lock    = threading.Lock()


def _set_step(s: str):
    global _current_step
    with _step_lock:
        _current_step = s
    print(f"[ORCH] PASO → {s}")


def get_step() -> str:
    with _step_lock:
        return _current_step


# ---------------------------------------------------------------------------
# Helper: llamada fire-and-forget a la Rasp Sebas (display / POV)
# ---------------------------------------------------------------------------

def _rasp(path: str, timeout: float = 4.0):
    """Llama a la Rasp Sebas sin bloquear mucho. Errores silenciados."""
    try:
        requests.get(f"{RASP_SEBAS_URL}{path}", timeout=timeout)
    except Exception as e:
        print(f"[RASP] {path} → {e}")

# ---------------------------------------------------------------------------
# Programas URP
# ---------------------------------------------------------------------------

OBS_PROG = "/programs/rutObservacion.urp"

RECOLECCION = {
    "lata":   "/programs/rutRecolecionLata.urp",
    "tetra":  "/programs/rutRecolecionTetra.urp",
    "vidrio": "/programs/rutRecolecionVidrio.urp",
}

DEPOSITO = {
    "lata":   "/programs/rutLata.urp",
    "tetra":  "/programs/rutTetra.urp",
    "vidrio": "/programs/rutVid.urp",
}

# ---------------------------------------------------------------------------
# Estado global (consultado por el servidor en /estado)
# ---------------------------------------------------------------------------

_busy = False
_busy_lock = threading.Lock()


def is_busy() -> bool:
    with _busy_lock:
        return _busy


def _set_busy(value: bool):
    global _busy
    with _busy_lock:
        _busy = value


# ---------------------------------------------------------------------------
# Identificación por HTTP
# ---------------------------------------------------------------------------

def _identify_object() -> str | None:
    """Llama a /identify en Rasp Sebas y devuelve el label, o None si falla."""
    url = f"{RASP_SEBAS_URL}/identify"
    print(f"[ID] GET {url}")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        obj = r.json().get("object")
        print(f"[ID] Objeto detectado: '{obj}'")
        return obj
    except Exception as e:
        print(f"[ID][ERR] Falló identificación: {e}")
        return None


# ---------------------------------------------------------------------------
# Secuencia principal
# ---------------------------------------------------------------------------

def run_full_sequence(user_id: str | None = None):
    """
    Ejecuta la secuencia completa en el hilo que la llame.
    user_id: si se pasa, al finalizar con éxito se llama /sumar en el servidor local.

    Pensado para correrse en un hilo daemon desde server.py.
    """
    if is_busy():
        print("[ORCH] Secuencia ya en curso, ignorando solicitud")
        return

    _set_busy(True)
    _set_step("")
    try:
        _run_sequence(user_id)
    except Exception as e:
        print(f"[ORCH][ERR] Excepción en secuencia: {e}")
    finally:
        _set_step("LISTO")
        _set_busy(False)
        print("[ORCH] Secuencia finalizada")


def _run_sequence(user_id: str | None):
    # 1) HOME
    _set_step("HOME")
    if not DEMO["skip_robot"]:
        print("\n=== 1) Enviando UR3 a HOME ===")
        move_home()
    else:
        print("\n=== 1) [DEMO] Saltando HOME robot ===")
        time.sleep(0.5)

    # 2) Puerta
    _set_step("PUERTA")
    if not DEMO["skip_plc"]:
        print("\n=== 2) Secuencia puerta (abrir / stop / cerrar) ===")
        door_open_stop_close()
    else:
        print("\n=== 2) [DEMO] Saltando secuencia puerta PLC ===")
        time.sleep(1)

    # 3) Observación
    _set_step("OBSERVACION")
    if not DEMO["skip_robot"]:
        print("\n=== 3) Ejecutando rutObservacion.urp ===")
        run_urp_sequence([OBS_PROG])
    else:
        print("\n=== 3) [DEMO] Saltando rutObservacion.urp ===")
        time.sleep(0.5)

    # 4) Identificación
    _set_step("CLASIFICANDO")
    if DEMO["force_object"]:
        obj = DEMO["force_object"]
        print(f"\n=== 4) [DEMO] Objeto forzado: '{obj}' ===")
    elif DEMO["skip_vision"]:
        obj = "bg"
        print("\n=== 4) [DEMO] Visión saltada → objeto = 'bg' ===")
    else:
        print("\n=== 4) Identificando objeto por cámara ===")
        obj = _identify_object()
        if obj is None:
            print("[ORCH] No se pudo identificar. Regresando a HOME.")
            _set_step("REGRESANDO")
            if not DEMO["skip_robot"]:
                move_home()
            return

    obj = obj.lower()

    # 5) ¿Fondo? → volver a HOME
    if obj == "bg":
        print("[ORCH] Objeto = 'bg'. Nada que tomar.")
        _set_step("REGRESANDO")
        if not DEMO["skip_robot"]:
            move_home()
        return

    if obj not in RECOLECCION or obj not in DEPOSITO:
        print(f"[ORCH] Etiqueta desconocida '{obj}'. Regresando a HOME.")
        _set_step("REGRESANDO")
        if not DEMO["skip_robot"]:
            move_home()
        return

    # 6) Recolección + depósito
    # Activa POV en la Rasp antes de que el robot empiece a recoger
    _rasp(f"/robot_pov_bg?duration=120")

    _set_step("DEPOSITANDO")
    if not DEMO["skip_robot"]:
        print(f"\n=== 5) Recolección de '{obj}' → {RECOLECCION[obj]} ===")
        run_urp_sequence([RECOLECCION[obj]])

        print(f"\n=== 6) Depósito de '{obj}' → {DEPOSITO[obj]} ===")
        run_urp_sequence([DEPOSITO[obj]])
    else:
        print(f"\n=== 5-6) [DEMO] Saltando recolección y depósito de '{obj}' ===")
        time.sleep(2)

    # Robot terminó: volver a HOME y restaurar carrusel
    _set_step("REGRESANDO")
    if not DEMO["skip_robot"]:
        move_home()

    # Devuelve el carrusel (interrumpe el robot_pov_bg)
    _rasp("/display_off")

    print("\n=== Secuencia completa ===")

    # 7) Sumar punto en BD local
    if user_id:
        _sumar_punto(user_id, obj)


def _sumar_punto(user_id: str, categoria: str):
    """Llama al endpoint local /sumar para registrar el punto."""
    url = f"http://127.0.0.1:{config.PC_PORT}/sumar/{user_id}/{categoria}"
    try:
        r = requests.post(url, timeout=5)
        print(f"[ORCH] Punto registrado → {r.json()}")
    except Exception as e:
        print(f"[ORCH][WARN] No se pudo registrar punto: {e}")
