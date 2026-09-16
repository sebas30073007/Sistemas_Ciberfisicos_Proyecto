"""
config.py — Única fuente de verdad para IPs, puertos y modos demo.
Todos los demás módulos importan desde aquí.
"""

import os

# ---------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------

PC_HOST = "0.0.0.0"
PC_PORT = 5000

# *** CAMBIAR ESTA IP a la IP real de la PC en la red del router ***
# Para verificar: ejecuta `ipconfig` en PowerShell y busca el adaptador ethernet
PC_IP = "192.168.1.50"

RASP_SEBAS_URL = "http://192.168.1.122:5000"   # Servidor de visión (GET /identify)
UR3_IP         = "192.168.1.77"                # Robot UR3 (Dashboard puerto 29999)
PLC_IP         = "192.168.1.13"               # PLC Siemens S7-1200

# ---------------------------------------------------------------------------
# Base de datos local
# ---------------------------------------------------------------------------

# Ruta al CSV de usuarios (junto a este archivo)
DB_PATH = os.path.join(os.path.dirname(__file__), "usuarios.csv")

# ---------------------------------------------------------------------------
# Modos demo
# Modificables en runtime desde el panel web /demo sin reiniciar el servidor.
# ---------------------------------------------------------------------------

DEMO = {
    "skip_robot":   False,  # Saltar movimientos del UR3
    "skip_plc":     False,  # Saltar secuencia de puerta PLC
    "skip_vision":  False,  # Saltar llamada a Rasp Sebas /identify
    "force_object": None,   # None | "lata" | "vidrio" | "tetra" | "bg"
}
