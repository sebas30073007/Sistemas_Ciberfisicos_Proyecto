---
title: Computadora y red
layout: default
parent: Gabinete Robot
nav_order: 4
---

# Computadora y Red

La **computadora central** del robot actúa como el **procesador principal** del sistema.  
Su función es coordinar la comunicación entre los diferentes subsistemas del gabinete: la interfaz HMI, el PLC, el microcontrolador, la cámara y la conexión con la red local.  

En esta etapa del proyecto se realizaron **pruebas iniciales de comunicación** mediante un servidor desarrollado con **Flask (Python)**, que permitirá en versiones futuras manejar el flujo completo de datos entre el robot y la estación de procesamiento.

---

## Estructura general del sistema

El objetivo es que la PC opere como un **nodo maestro**, encargado de:
- Servir como **punto de enlace TCP/IP** entre la red local y los microprocesadores.
- **Recibir imágenes** desde la cámara o Raspberry Pi encargada de la visión.
- **Solicitar capturas** o datos específicos a los dispositivos secundarios.
- **Registrar eventos** y resultados de clasificación en archivos o bases de datos.
- **Coordinar las rutinas del robot UR3**, a través de comandos HTTP o sockets.

---

## Servidor de prueba (Flask)

Para validar la comunicación se implementó un pequeño servidor llamado `vision_hub_server.py`, que cumple funciones básicas:

- Recibir y guardar mensajes enviados por otros dispositivos.  
- Activar solicitudes de captura desde la PC hacia la Raspberry Pi.  
- Recibir imágenes procesadas y almacenarlas localmente.  
- Proveer rutas de diagnóstico (`/health`) y monitoreo del estado del sistema.

El servidor cuenta con rutas simples de tipo REST, como:
- `/guardar` — recibe texto o datos simples en JSON.  
- `/request_capture` — crea una solicitud de captura pendiente.  
- `/upload_image` — recibe la imagen capturada desde la cámara.  
- `/command` — permite consultar si hay alguna acción pendiente.  

Estas rutas son suficientes para simular la comunicación básica entre los módulos del sistema antes de integrar la lógica completa del robot.

---

## Comunicación y protocolos

A nivel de red, la PC funcionará como **router interno del gabinete**, gestionando la comunicación entre:
- El **PLC (Siemens S7-1200)** vía **Ethernet TCP/IP**.  
- Las **Raspberry Pi** mediante **HTTP**.  
- El **UR3** mediante **Ethernet**.  
