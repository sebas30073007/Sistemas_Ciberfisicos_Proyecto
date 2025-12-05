"""
Sistema de orquestación para UR3 + PLC + visión.
"""

import time
import requests
from threading import Event
from flask import Flask, request, jsonify
from flask_cors import CORS

from plc_open_close_door import connect_plc, write_M03_M04, T_MOV
from ur3_home1 import move_home
from ur3_secuential_files import run_urp_sequence

# ==========================================================
# CONFIGURACIÓN INICIAL
# ==========================================================

app = Flask(__name__)
CORS(app)

API_RENDER="https://recicla.onrender.com"

start_event = Event()
consulta_event = Event()
rutina_event = Event()

current_user_id = None
current_categoria = None

CMD_STOP  = (False, False)
CMD_OPEN  = (False, True)
CMD_CLOSE = (True, False)

STOP_EXTRA = 2.0

OBS_PROG = "/programs/rutObservacion.urp"

RECOLECCION_PROGS = {
    "lata": "/programs/rutRecolecionLata.urp",
    "tetra": "/programs/rutRecolecionTetra.urp",
    "vidrio": "/programs/rutRecolecionVidrio.urp",
}

DEPOSITO_PROGS = {
    "lata": "/programs/rutLata.urp",
    "tetra": "/programs/rutTetra.urp",
    "vidrio": "/programs/rutVid.urp",
}

IDENTIFY_URL = "http://192.168.1.122:5000/identify_window"

# ==========================================================
# FUNCIONES PLC
# ==========================================================

def door_open():
    try:
        plc = connect_plc()
        print("[PLC] Conectado para abrir puerta")
        write_M03_M04(plc, *CMD_STOP)
        time.sleep(0.5)
        print("[PLC] Abriendo puerta...")
        write_M03_M04(plc, *CMD_OPEN)
        time.sleep(T_MOV)
        print("[PLC] STOP 2s...")
        write_M03_M04(plc, *CMD_STOP)
        time.sleep(STOP_EXTRA)
        print("[PLC] Puerta en STOP final")
    except Exception as e:
        print("[PLC][ERROR]:", e)
    finally:
        try: plc.disconnect()
        except: pass
        print("[PLC] Desconectado")

def door_close():
    try:
        plc = connect_plc()
        print("[PLC] Conectado para cerrar puerta")
        write_M03_M04(plc, *CMD_STOP)
        time.sleep(0.5)
        print("[PLC] Cerrando puerta...")
        write_M03_M04(plc, *CMD_CLOSE)
        time.sleep(T_MOV)
        write_M03_M04(plc, *CMD_STOP)
        print("[PLC] Puerta cerrada (STOP)")
    except Exception as e:
        print("[PLC][ERROR]:", e)
    finally:
        try: plc.disconnect()
        except: pass
        print("[PLC] Desconectado")

# ==========================================================
# ENDPOINTS FLASK
# ==========================================================

@app.route("/empezarObjeto", methods=["POST"])
def empezarObjeto():
    data = request.get_json(silent=True)
    body = request.data.decode().strip()

    print("\n--- Señal recibida en /empezarObjeto ---")
    print("JSON:", data)
    print("Body:", body)

    if data and str(data.get("start")) == "1":
        start_event.set()
        return {"status": "ok"}, 200

    if body == "1":
        start_event.set()
        return {"status": "ok"}, 200

    return {"status": "error", "detalle": "start != 1"}, 400

@app.route('/consulta/<user_id>', methods=['GET'])
def consultar(user_id):
    global current_user_id
    current_user_id = user_id
    try:
        consulta_event.set()
        r = requests.get(f"{API_RENDER}/consulta/{user_id}")
        return {"status": "ok", "respuesta_render": r.json()}, r.status_code
    except Exception as e:
        return {"status": "error", "detalle": str(e)}, 500

def sumar():
    global current_user_id
    global current_categoria
    user_id=current_user_id
    objeto=current_categoria
    if user_id and objeto:
        try:
            r = requests.post(f"{API_RENDER}/sumar/{user_id}/{objeto}")
            print("Sumo punto a", user_id, objeto)
            return {"status": "ok", "respuesta_render": r.json()}, r.status_code
        except Exception as e:
            return {"status": "error", "detalle": str(e)}, 500
    return {"status": "error", "detalle": "user_id u objeto no definidos"}, 400

# ==========================================================
# ROBOT POV
# ==========================================================

def robot_pov(duration=15):
    try:
        print(f"[ROBOT POV] Solicitando POV {duration}s")
        requests.get(f"http://192.168.1.122:5000/robot_pov?duration={duration}", timeout=duration+3)
    except Exception as e:
        print("[ROBOT POV][ERROR]:", e)

# ==========================================================
# IDENTIFICACIÓN
# ==========================================================

def identify_object():
    print("[ID] Llamando a:", IDENTIFY_URL)
    try:
        # 1) Identify window dura por default 5 segundos
        r = requests.get(IDENTIFY_URL, timeout=7)
        r.raise_for_status()
        time.sleep(5)
        # 2) Luego se llama robot_pov
        #robot_pov(15)  # puedes cambiar el 5 a lo que quieras

        data = r.json()
        print("[ID] Respuesta:", data)
        return data.get("object")

    except Exception as e:
        print("[ID][ERROR]:", e)
        return None

# ==========================================================
# MOVIMIENTOS Y LÓGICA DEL ROBOT
# ==========================================================

def mover():
    try:
        print("\n=== 2) Secuencia de puerta ===")
        door_open()

        print("\n=== 3) Ejecutando observación ===")
        try:
            run_urp_sequence([OBS_PROG])
        except Exception as e:
            print("⚠ [OBS][ERROR]:", e)
            return None

        print("\n=== 4) Identificando objeto ===")
        obj = identify_object()
        if not obj:
            door_close()
            return None

        obj = obj.lower()
        print(f"[MAIN] Objeto detectado: {obj}")
        door_close()
        return obj

    except Exception as e:
        print("⚠ [MOVER][ERROR]:", e)
        return None

# ==========================================================
# LOOP FOTOS VIDEOS
# ==========================================================

def media_loop(indice):
    """
    Loop que se ejecuta cuando NO hay start_event activo.
    Muestra videos e imágenes en secuencia hasta que llegue el evento.
    """
    media_files = [
        "file1.mp4",
        "file2.mp4",
        "file3.mp4",
        "file2.jpg"
    ]
    archivo = media_files[indice]
    try:
        print(f"[MEDIA] Mostrando: {archivo}")
        requests.get(f"http://192.168.1.122:5000/show_media?name={archivo}", timeout=17)
    except Exception as e:
        print("[MEDIA][ERROR]:", e)


# ==========================================================
# MAIN (PROTEGIDO)
# ==========================================================

def main():
    global current_categoria, current_user_id
    try:
        print("\n=== 1) Enviando UR3 a HOME ===")
        move_home()
        obj=current_categoria
        user_id=current_user_id
        obj = mover()
        if not obj:
            print("[MAIN] No se pudo obtener objeto.")
            door_close()
            return

        if obj == "bg":
            move_home()
            return

        if obj not in RECOLECCION_PROGS:
            print("[MAIN] Objeto desconocido:", obj)
            move_home()
            return

        print(f"\n=== 5) Recolección ({obj}) ===")
        try:
            print(f"[ROBOT POV] Solicitando POV {25}s")
            requests.get(f"http://192.168.1.122:5000/robot_pov?duration={25}", timeout=1)
        except Exception as e:
            print("[ROBOT POV][ERROR]:", e)
        try:
            run_urp_sequence([RECOLECCION_PROGS[obj]])
        except Exception as e:
            print("⚠ [URP RECOLECCION][ERROR]:", e)
            return

        print(f"\n=== 6) Depósito ({obj}) ===")
        try:
            run_urp_sequence([DEPOSITO_PROGS[obj]])
            rutina_event.set()
        except Exception as e:
            print("⚠ [URP DEPOSITO][ERROR]:", e)
            return

        move_home()

    except Exception as e:
        print("⚠ [MAIN ERROR]:", e)

def verificar_suma():
    if consulta_event.is_set() and rutina_event.is_set():
        print(">>> Ambos eventos activos. Ejecutando SUMAR()...")
        sumar()

        # limpiar eventos después de sumar
        consulta_event.clear()
        rutina_event.clear()
# ==========================================================
# LOOP PRINCIPAL
# ==========================================================
if __name__ == "__main__":
    from threading import Thread

    cont = 0
    media_files = [
        "file1.mp4",
        "file2.mp4",
        "file3.mp4",
        "file2.jpg"
    ]

    # Cronómetro para controlar cada 17 segundos
    last_media_time = 0
    MEDIA_INTERVAL = 17   # segundos

    server = Thread(
        target=lambda: app.run(host="192.168.1.60", port=5000, debug=False, use_reloader=False),
        daemon=True
    )
    server.start()

    print("\nSistema listo. Esperando señal '1'...\n")

    while True:
        try:
            now = time.time()

            # ======================================================
            # PRIORIDAD: si llega evento -> ejecutar robot
            # ======================================================
            if start_event.is_set():
                start_event.clear()
                print(">>> Señal detectada. Ejecutando ciclo principal...")
                main()
                print("\nEsperando nueva señal...\n")

            else:
                # ======================================================
                # SOLO si han pasado 17 segundos mostramos media
                # ======================================================
                if now - last_media_time >= MEDIA_INTERVAL:

                    archivo = media_files[cont]

                    try:
                        print(f"[MEDIA] Mostrando: {archivo}")
                        requests.get(
                            f"http://192.168.1.122:5000/show_media?name={archivo}",
                            timeout=5
                        )
                    except Exception as e:
                        print("[MEDIA][ERROR]:", e)

                    # reiniciar cronómetro
                    last_media_time = now

                    # pasar al siguiente archivo
                    cont = (cont + 1) % len(media_files)

            # ejecución suave del loop
            verificar_suma()
            time.sleep(0.1)

        except KeyboardInterrupt:
            print("Detenido por usuario.")
            break
        except Exception as e:
            print("⚠ [LOOP PRINCIPAL ERROR]:", e)
