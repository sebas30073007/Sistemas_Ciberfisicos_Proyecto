---
title: Gabinete Robot
layout: default
nav_order: 2
has_children: true
permalink: /gabinete-robot/
redirect_from:
  - /conexiones/
  - /estructura/
---

# Gabinete

El gabinete del robot integra la infraestructura física, el cableado y los subsistemas electrónicos que permiten que el robot de reciclaje opere de forma autónoma y segura.

---


![Estructura]({{ "/assets/img/Gabinete_robot.jpg" | relative_url }})

## ¿Qué encontrarás en esta sección?

1. **Arquitectura general del gabinete**
   - Distribución física de los módulos: interfaz de usuario, recepción de residuos y célula robótica.

2. **Interfaz de usuario en el gabinete**
   - Lector de tarjetas RFID (RC522), microcontrolador ESP32 y convertidor TTL–Serial.
   - HMI táctil basada en Raspberry Pi y descripción de la experiencia de la persona que deposita residuos.

3. **Módulo de recepción de residuos**
   - PLC Siemens LOGO! y señales de entrada/salida relevantes.
   - Puerta automática con actuador lineal y su coordinación con el resto del sistema.

4. **Módulo robótico**
   - Microprocesador del robot (Raspberry Pi).
   - Cámara de profundidad utilizada para la clasificación.
   - Brazo robótico UR3 y gripper de mano robótica suave.

5. **Red de comunicaciones y cómputo**
   - Topología de la red local: PC central y switch Ethernet.
   - Conexiones USB y serial que enlazan los diferentes microprocesadores y módulos de control.


## Convenciones y alcance

- Se utilizan unidades métricas (mm) para dimensiones y referencias espaciales.
- Las conexiones eléctricas se describen con el nombre real de los puertos y, cuando aplica, con el código de color del cableado.
- Las fotografías, diagramas y esquemas eléctricos se enlazan desde las subpáginas correspondientes para mantener este índice ligero y enfocado en el contexto general.

Con esta guía podrás ubicar rápidamente dónde se documenta cada elemento del gabinete y cómo se relaciona con los demás subsistemas del robot.
