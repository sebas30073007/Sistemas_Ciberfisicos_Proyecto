"""
robot_control.py — Control del robot UR3.

Fusión de:
  - jetson/ur3_home.py      → move_home() via librería urx
  - jetson/ur3_secuential_files.py → run_urp_sequence() via Dashboard socket

Si urx no está disponible o falla en Python 3.12/Windows, move_home()
usa un URScript enviado por el Dashboard (misma clase que run_urp_sequence),
eliminando la dependencia de urx.
"""

import socket
import time
import logging

from config import UR3_IP

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Posición HOME (ángulos de articulaciones en radianes)
# ---------------------------------------------------------------------------

HOME_JOINTS = (1.5708, -2.4958, 2.5307, -3.2812, -1.6406, 1.5708)
MOVE_ACCEL  = 0.8
MOVE_VEL    = 0.8
JOINT_TOL   = 0.02   # ~1.1 grados
HOME_TIMEOUT = 20    # segundos

# ---------------------------------------------------------------------------
# Dashboard client (puerto 29999)
# ---------------------------------------------------------------------------

class Dashboard:
    def __init__(self, host=UR3_IP, port=29999, timeout=5):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.recv(1024)   # banner inicial

    def cmd(self, s, recv=True):
        self.sock.sendall((s + "\n").encode("utf-8"))
        return self.sock.recv(4096).decode("utf-8") if recv else ""

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


def _wait_state(db, targets=("STOPPED",), poll=0.2, timeout=120):
    """Espera hasta que programState contenga alguno de los estados en targets."""
    t0 = time.time()
    last = ""
    while time.time() - t0 < timeout:
        ans = db.cmd("programState")
        last = ans
        for st in targets:
            if st in ans:
                return ans
        time.sleep(poll)
    raise TimeoutError(f"Timeout esperando {targets}. Última respuesta: {last}")


# ---------------------------------------------------------------------------
# move_home — intenta urx, cae a Dashboard si no disponible
# ---------------------------------------------------------------------------

def move_home():
    """Mueve el UR3 a la posición HOME con aceleración suave."""
    try:
        import urx
        _move_home_urx()
    except ImportError:
        log.warning("[robot] urx no disponible, usando Dashboard para HOME")
        _move_home_dashboard()


def _move_home_urx():
    """Implementación con urx (suave, con telemetría de articulaciones)."""
    import urx

    robot = urx.Robot(UR3_IP)
    try:
        print(f"[UR3] Moviendo a HOME via urx: {HOME_JOINTS}")
        robot.movej(HOME_JOINTS, acc=MOVE_ACCEL, vel=MOVE_VEL, wait=False)

        t0 = time.time()
        last_read = time.time()
        while time.time() - t0 < HOME_TIMEOUT:
            try:
                joints = robot.getj()
                last_read = time.time()
                diffs = [abs(joints[i] - HOME_JOINTS[i]) for i in range(6)]
                if all(d < JOINT_TOL for d in diffs):
                    print("[UR3] HOME alcanzado")
                    return
            except Exception:
                if time.time() - last_read > 3:
                    log.warning("[UR3] Sin telemetría por >3 s, asumiendo HOME alcanzado")
                    return
            time.sleep(0.1)

        log.warning("[UR3] Timeout esperando HOME — continuando de todas formas")
    finally:
        robot.close()


def _move_home_dashboard():
    """Fallback: envía URScript movej() via Dashboard."""
    j = ", ".join(str(round(v, 4)) for v in HOME_JOINTS)
    script = f"movej([{j}], a={MOVE_ACCEL}, v={MOVE_VEL})"
    db = Dashboard(UR3_IP)
    try:
        db.cmd(f"script:{script}", recv=False)
        time.sleep(HOME_TIMEOUT * 0.5)   # espera conservadora
        print("[UR3] HOME enviado via Dashboard (sin confirmación de articulaciones)")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# run_urp_sequence — ejecuta programas .urp en secuencia
# ---------------------------------------------------------------------------

def run_urp_sequence(programs: list):
    """
    Carga y ejecuta cada programa .urp en la lista, esperando STOPPED entre cada uno.

    Ejemplo:
        run_urp_sequence(["/programs/rutObservacion.urp",
                          "/programs/rutLata.urp"])
    """
    db = Dashboard(UR3_IP)
    try:
        # Limpiar popups / protective stop si los hay
        for clear_cmd in ("close safety popup", "unlock protective stop", "close popup"):
            try:
                db.cmd(clear_cmd)
            except Exception:
                pass

        for i, prog in enumerate(programs, 1):
            print(f"[UR3] Paso {i}/{len(programs)}: cargando {prog}")
            print(db.cmd(f"load {prog}").strip())

            print("[UR3] play")
            print(db.cmd("play").strip())

            _wait_state(db, targets=("PLAYING",), poll=0.2, timeout=10)
            print(f"[UR3] Ejecutando {prog}...")

            _wait_state(db, targets=("STOPPED",), poll=0.5, timeout=600)
            print(f"[UR3] Completado: {prog}")

        print("[UR3] Secuencia de programas completada")
    finally:
        db.close()
