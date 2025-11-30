---
title: Red de comunicaciones
layout: default
parent: Conexiones eléctricas y red de comunicaciones
nav_order: 2
---

## 2. Red de comunicaciones

Esta sección describe cómo se comunican los dispositivos a nivel de red y software.

### 2.1 Topología física

La red interna se organiza así:

- Todos los dispositivos se conectan a un **switch Ethernet**, salvo la Raspberry Pi del HMI.  
- El switch se conecta también a la **red de la escuela** para acceso a internet.

Asignación de direcciones IP:

- `192.168.1.10` – **Jetson Nano** (servidor/orquestador).  
- `192.168.1.11` – **Raspberry Pi HMI + RFID** (“rasp dany”).  
  - Conectada directamente a la red de la escuela (no pasa por el switch interno).  
- `192.168.1.12` – **Raspberry Pi de visión artificial** (“rasp sebas”).  
- `192.168.1.13` – **PLC S7-1200** (control de puerta con motor a pasos).  
- `192.168.1.77` – **Robot UR3**.  
- `192.168.1.1` – **Gripper / controlador adicional** (si aplica).

Todos usan la misma máscara de red (por ejemplo `255.255.255.0`) para poder comunicarse entre sí.

---

### 2.2 Tabla de roles y protocolos

| IP            | Dispositivo                | Rol principal                                      | Protocolos usados                            |
|---------------|---------------------------|----------------------------------------------------|----------------------------------------------|
| 192.168.1.10  | Jetson Nano               | Orquestador, servidor principal                    | Python + HTTP (Flask), Snap7, sockets TCP    |
| 192.168.1.11  | Rasp HMI + RFID           | Interfaz gráfica local para el usuario             | HTTP (cliente), TCP/IP hacia Jetson          |
| 192.168.1.12  | Rasp visión               | Servidor de visión artificial (`/identify`)        | Flask/HTTP + cámara USB                      |
| 192.168.1.13  | PLC S7-1200               | Control de puerta con motor a pasos                | Snap7/TCP desde Jetson                       |
| 192.168.1.77  | UR3                       | Ejecución de rutinas de observación, pick & place  | Dashboard API (puerto 29999) + URScript      |
| 192.168.1.1   | Controlador gripper       | Control dedicado del accionamiento del gripper     | TCP/UDP según implementación                 |

---

### 2.3 Librerías y dependencias en la Jetson Nano

En la Jetson Nano se usan principalmente:

- **Python 3.x**
- **`requests`** — para llamar servicios HTTP (por ejemplo, visión artificial).  
- **`Flask`** — cuando la Jetson actúa como servidor (en pruebas o futuras versiones).  
- **`python-snap7`** — para comunicarse con el PLC Siemens S7-1200.  
- **`socket`** (módulo estándar de Python) — para hablar con la interfaz Dashboard del UR3.

Instalación típica (ejemplo):

```bash
pip install requests flask python-snap7
