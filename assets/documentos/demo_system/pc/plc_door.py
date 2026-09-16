"""
plc_door.py — Control de la puerta mediante PLC Siemens S7-1200.

Basado en jetson/plc_open_close_door.py, con PLC_IP importado de config.py.

M0.3 = comando cerrar (close cmd)
M0.4 = comando abrir  (open cmd)
"""

import time

from config import PLC_IP

# ---------------------------------------------------------------------------
# Parámetros hardware
# ---------------------------------------------------------------------------

RACK   = 0   # S7-1200
SLOT   = 1   # S7-1200

M_BYTE  = 0  # byte M0.x
M_SIZE  = 1
M03_BIT = 3  # M0.3 → cerrar
M04_BIT = 4  # M0.4 → abrir

T_MOV   = 3.0   # segundos de movimiento de puerta
T_STOP  = 3.0   # segundos en estado STOP entre movimientos

CMD_STOP  = (False, False)
CMD_OPEN  = (False, True)
CMD_CLOSE = (True,  False)

STOP_EXTRA = 2.0  # segundos de STOP con puerta abierta (para visión)


# ---------------------------------------------------------------------------
# Funciones de bajo nivel
# ---------------------------------------------------------------------------

def connect_plc():
    import snap7
    plc = snap7.client.Client()
    plc.connect(PLC_IP, RACK, SLOT)
    if not plc.get_connected():
        raise RuntimeError(f"No se pudo conectar al PLC ({PLC_IP})")
    return plc


def read_M03_M04(plc):
    """Devuelve (M0.3, M0.4) como tupla de bool."""
    from snap7.util import get_bool
    data = plc.mb_read(M_BYTE, M_SIZE)
    return get_bool(data, 0, M03_BIT), get_bool(data, 0, M04_BIT)


def write_M03_M04(plc, val_m03: bool, val_m04: bool):
    """Escribe M0.3 y M0.4 en un solo ciclo lectura/escritura."""
    from snap7.util import set_bool, get_bool
    data = plc.mb_read(M_BYTE, M_SIZE)
    set_bool(data, 0, M03_BIT, val_m03)
    set_bool(data, 0, M04_BIT, val_m04)
    plc.mb_write(M_BYTE, M_SIZE, data)


# ---------------------------------------------------------------------------
# Operaciones individuales (para debug)
# ---------------------------------------------------------------------------

def door_stop():
    """Solo STOP (M0.3=0, M0.4=0). Seguro para llamar en cualquier momento."""
    plc = connect_plc()
    try:
        write_M03_M04(plc, *CMD_STOP)
        print("[PLC] STOP enviado")
    finally:
        plc.disconnect()


def door_open_only():
    """STOP → abrir → espera T_MOV → STOP final. Deja puerta abierta."""
    plc = connect_plc()
    print("[PLC] Conectado — secuencia ABRIR")
    try:
        write_M03_M04(plc, *CMD_STOP);  time.sleep(0.3)
        print("[PLC] Abriendo...")
        write_M03_M04(plc, *CMD_OPEN);  time.sleep(T_MOV)
        write_M03_M04(plc, *CMD_STOP)
        print("[PLC] Puerta abierta, STOP")
    finally:
        plc.disconnect()
        print("[PLC] Desconectado")


def door_close_only():
    """STOP → cerrar → espera T_MOV → STOP final. Deja puerta cerrada."""
    plc = connect_plc()
    print("[PLC] Conectado — secuencia CERRAR")
    try:
        write_M03_M04(plc, *CMD_STOP);  time.sleep(0.3)
        print("[PLC] Cerrando...")
        write_M03_M04(plc, *CMD_CLOSE); time.sleep(T_MOV)
        write_M03_M04(plc, *CMD_STOP)
        print("[PLC] Puerta cerrada, STOP")
    finally:
        plc.disconnect()
        print("[PLC] Desconectado")


# ---------------------------------------------------------------------------
# Secuencia de puerta
# ---------------------------------------------------------------------------

def door_open_stop_close():
    """
    Secuencia completa: STOP → abrir → STOP 2 s → cerrar → STOP.
    Deja el PLC en STOP al finalizar.
    """
    plc = connect_plc()
    print("[PLC] Conectado para secuencia de puerta")
    try:
        write_M03_M04(plc, *CMD_STOP)
        time.sleep(0.5)

        print("[PLC] Abriendo puerta...")
        write_M03_M04(plc, *CMD_OPEN)
        time.sleep(T_MOV)

        print(f"[PLC] STOP (puerta abierta) {STOP_EXTRA:.0f} s...")
        write_M03_M04(plc, *CMD_STOP)
        time.sleep(STOP_EXTRA)

        print("[PLC] Cerrando puerta...")
        write_M03_M04(plc, *CMD_CLOSE)
        time.sleep(T_MOV)

        write_M03_M04(plc, *CMD_STOP)
        print("[PLC] Puerta en STOP final")
    finally:
        plc.disconnect()
        print("[PLC] Desconectado")
