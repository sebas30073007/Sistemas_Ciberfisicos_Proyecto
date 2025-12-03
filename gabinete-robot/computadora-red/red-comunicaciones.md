---
title: Red de comunicaciones
layout: default
parent: Conexiones eléctricas y red de comunicaciones
nav_order: 2
---

## 2. Red de comunicaciones

Esta sección describe cómo se comunican los dispositivos a nivel de red y software.
![Diagrama de topología y jerarquia]({{ "/assets/img/Diagrama-topologia.jpg" | relative_url }})

---

### 2.1 Topología física

La red interna se organiza así:

- Todos los dispositivos se conectan a un **switch Ethernet**, salvo la Raspberry Pi del HMI.  
- El switch se conecta también a la **red de la escuela** para acceso a internet.

Asignación de direcciones IP:

- `192.168.1.44` – **Jetson Nano** (servidor/orquestador).  
- `192.168.1.236` – **Raspberry Pi HMI + RFID**.  
  - Conectada directamente a la red de la escuela (no pasa por el switch interno).  
- `192.168.1.122` – **Raspberry Pi de visión artificial** (“rasp sebas”).  
- `192.168.1.13` – **PLC S7-1200** (control de puerta con motor a pasos).  
- `192.168.1.77` – **Robot UR3**.  
- `192.168.1.1` – **Gripper / controlador adicional**.

Todos usan la misma máscara de red (`255.255.255.0`).

---

### 2.2 Tabla de roles y protocolos

| IP            | Dispositivo                | Rol principal                                      | Protocolos usados                            |
|---------------|---------------------------|----------------------------------------------------|----------------------------------------------|
| 192.168.1.44  | Jetson Nano               | Orquestador, servidor principal                    | Python + HTTP (Flask), Snap7, sockets TCP    |
| 192.168.1.236  | Rasp HMI + RFID           | Interfaz gráfica local para el usuario             | HTTP (cliente), TCP/IP hacia Jetson          |
| 192.168.1.122  | Rasp visión               | Servidor de visión artificial (`/identify`)        | Flask/HTTP + cámara USB                      |
| 192.168.1.13  | PLC S7-1200               | Control de puerta con motor a pasos                | Snap7/TCP desde Jetson                       |
| 192.168.1.77  | UR3                       | Ejecución de rutinas de observación, pick & place  | Dashboard API (puerto 29999) + URScript      |
| 192.168.1.1   | Controlador gripper       | Control dedicado del accionamiento del gripper     | TCP/UDP                 |

---

### Librerías y dependencias en la Jetson Nano

En la Jetson Nano se usan principalmente:

- **Python 3.x**
- **`requests`** — para llamar servicios HTTP (por ejemplo, la Raspberry de visión).  
- **`Flask`** — cuando la Jetson actúa como servidor.  
- **`python-snap7`** — para comunicarse con el PLC Siemens S7-1200.  
- **`socket`** (módulo estándar de Python) — para hablar con el Dashboard del UR3.

Ejemplo de instalación:

{% raw %}
~~~bash
pip install requests flask python-snap7
~~~
{% endraw %}

---

### Pruebas de comunicación PLC S7-1200 (Snap7)

Ejemplo mínimo para **enviar un comando** (bit de abrir/cerrar puerta) y **leer el estado** del byte M0:

{% raw %}
~~~python
import snap7
from snap7.util import get_bool, set_bool

PLC_IP = "192.168.1.13"
RACK, SLOT = 0, 1

M_BYTE = 0      # M0.x
M_SIZE = 1      # 1 byte
BIT_OPEN  = 4   # M0.4 -> abrir puerta
BIT_CLOSE = 3   # M0.3 -> cerrar puerta

def connect_plc():
    plc = snap7.client.Client()
    plc.connect(PLC_IP, RACK, SLOT)
    if not plc.get_connected():
        raise RuntimeError("No se pudo conectar al PLC")
    return plc

def write_cmd(plc, close_cmd=False, open_cmd=False):
    data = plc.mb_read(M_BYTE, M_SIZE)      # leer byte actual
    set_bool(data, 0, BIT_CLOSE, close_cmd)
    set_bool(data, 0, BIT_OPEN,  open_cmd)
    plc.mb_write(M_BYTE, data)             # escribir byte M0

def read_status(plc):
    data = plc.mb_read(M_BYTE, M_SIZE)
    return {
        "close": get_bool(data, 0, BIT_CLOSE),
        "open":  get_bool(data, 0, BIT_OPEN),
    }

if __name__ == "__main__":
    plc = connect_plc()
    print("Estado inicial:", read_status(plc))

    print("Comando: abrir puerta")
    write_cmd(plc, close_cmd=False, open_cmd=True)

    print("Estado después del comando:", read_status(plc))
    plc.disconnect()
~~~
{% endraw %}

---

### Pruebas de comunicación Robot UR3 (Dashboard API)

Prueba rápida para **mandar al UR3 a home** y luego **ejecutar una rutina** completa:

{% raw %}
~~~python
import socket
import time

UR3_IP    = "192.168.1.77"
PORT_DASH = 29999

def send_dashboard(cmd: str) -> str:
    """Envía un comando al Dashboard y devuelve la respuesta."""
    with socket.create_connection((UR3_IP, PORT_DASH), timeout=5) as s:
        _ = s.recv(1024)  # banner inicial
        s.sendall((cmd + "\n").encode("utf-8"))
        return s.recv(4096).decode("utf-8")

# 1) Llevar al robot a HOME (programa URP guardado en el controlador)
print(send_dashboard("load /programs/rutHome.urp"))
print(send_dashboard("play"))
time.sleep(1)

# 2) Ejecutar el programa de observación
print(send_dashboard("load /programs/rutObservacion.urp"))
print(send_dashboard("play"))
~~~
{% endraw %}

Se asume que en el UR3 existen los programas `rutHome.urp` y `rutObservacion.urp` en la carpeta `/programs/`.

---

### Pruebas de comunicación Raspberry de visión

Ejemplo mínimo para **invocar el servicio de visión** y leer el objeto detectado:

{% raw %}
~~~python
import requests

VISION_URL = "http://192.168.1.12:5000/identify"

resp = requests.get(VISION_URL, timeout=10)
resp.raise_for_status()

data = resp.json()
print("Respuesta de visión:", data)
print("Objeto detectado:", data.get("object"))
~~~
{% endraw %}

El servidor devuelve un JSON del estilo:

{% raw %}
~~~json
{ "object": "lata" }
~~~
{% endraw %}

donde la etiqueta puede ser, por ejemplo, `"lata"`, `"tetra"`, `"vidrio"` o `"bg"`.

---

## Visión general del orquestador

En el sistema completo, la Jetson Nano no ejecuta estos scripts por separado, sino que corre un **orquestador** que:

1. Manda al **UR3** a HOME.  
2. Indica al **PLC** que abra la puerta, espere y la cierre.  
3. Ejecuta en el UR3 la **rutina de observación**.  
4. Llama al servicio `/identify` de la Raspberry de visión.  
5. Según el tipo de residuo detectado, carga y ejecuta la rutina URP de **recolección** y **depósito** correspondiente, o regresa a HOME si el resultado es fondo (`"bg"`).

Esta sección de comunicaciones deja documentado qué IP tiene cada equipo, qué protocolo usa y qué código mínimo se necesita para comprobar que el enlace funciona correctamente.