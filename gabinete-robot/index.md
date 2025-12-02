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
### Contenido de esta sección

| Sección | Descripción |
|--------|-------------|
| **Arquitectura general del gabinete** | Distribución física de los módulos: interfaz de usuario, recepción de residuos y célula robótica. |
| **Interfaz de usuario en el gabinete** | - Lector RFID (RC522), microcontrolador ESP32 y convertidor TTL-Serial.<br>- HMI táctil basada en Raspberry Pi y descripción de la experiencia del usuario al depositar residuos. |
| **Módulo de recepción de residuos** | - PLC Siemens LOGO! y señales de entrada/salida relevantes.<br>- Puerta automática con actuador lineal y su coordinación con el resto del sistema. |
| **Módulo robótico** | - Microprocesador del robot (Raspberry Pi).<br>- Cámara de profundidad utilizada para la clasificación.<br>- Brazo robótico UR3 y gripper de mano robótica suave. |
| **Red de comunicaciones y cómputo** | - Topología de la red local: PC central y switch Ethernet.<br>- Conexiones USB y serial que enlazan los diferentes microprocesadores y módulos de control. |

---


## Convenciones y alcance

- Se utilizan unidades métricas (mm) para dimensiones y referencias espaciales.
- Las conexiones eléctricas se describen con el nombre real de los puertos y, cuando aplica, con el código de color del cableado.
- Las fotografías, diagramas y esquemas eléctricos se enlazan desde las subpáginas correspondientes para mantener este índice ligero y enfocado en el contexto general.

Con esta guía podrás ubicar rápidamente dónde se documenta cada elemento del gabinete y cómo se relaciona con los demás subsistemas del robot.
