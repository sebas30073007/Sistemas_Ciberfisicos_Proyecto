---
layout: default
title: Diagrama a bloques
parent: Conexiones
nav_order: 1
---

![Diagrama general del proyecto]({{ "/assets/img/Diagrama_de_proyecto.png" | relative_url }})

## Visión general
La arquitectura se compone de tres dominios que se comunican entre sí: el gabinete del robot (infraestructura física), la nube (servicios y procesamiento) y las interfaces de usuario (experiencia del operador y del público). Esta estructura permite separar responsabilidades sin perder trazabilidad entre eventos.

## Componentes principales
### Gabinete del robot
- **Robótica y sensado:** UR3 con cámara (montada en la muñeca o fija) y gripper para manipulación del residuo.
- **Sensores auxiliares:** barrera infrarroja, sensores de proximidad, peso e inductivo para detectar presencia de objetos y condiciones seguras.
- **Control y seguridad:** PLC para interlocks (puertas, paro de emergencia) y PC industrial que coordina la secuencia, muestra la HMI local y se comunica con la nube.
- **Red local:** todos los elementos se interconectan a través de un switch dedicado que aísla la red de control.

### Nube y servicios
- **APIs en Python:** reciben imágenes y eventos, orquestan la clasificación y exponen datos a otras aplicaciones.
- **Motor de IA:** puede ejecutarse en la nube o delegarse al edge; procesa las imágenes normalizadas y devuelve la clase del residuo.
- **Base de datos y almacenamiento:** conserva usuarios, sesiones, vínculos a evidencias fotográficas y métricas de cada ciclo.
- **Dashboards web/móvil:** muestran KPIs, ranking y tablas de puntos para seguimiento operativo y gamificación.

### Interfaces de usuario
- **HMI local:** guía al usuario durante el depósito, muestra instrucciones, confirma resultados y reproduce mensajes de audio.
- **Sitio web / app:** permite revisar el ranking global, el historial personal y las reglas de premiación cuando estén disponibles.

## Flujo operativo
1. El usuario se identifica (RFID/QR) o opera como invitado.
2. La cabina detecta el residuo, captura la imagen y la normaliza.
3. La IA clasifica el material y el UR3 deposita el objeto en el contenedor adecuado.
4. La PC registra un evento completo en la base de datos (usuario, material, confianza, fecha, máquina, evidencia, tiempo de ciclo).
5. Se actualiza el puntaje y ranking en la HMI y en los dashboards en tiempo real.

## Datos críticos
- Identificadores: usuario (si aplica), máquina y sesión.
- Trazabilidad: fecha/hora UTC, material clasificado, confianza del modelo y enlace a la imagen.
- Operación: duración del ciclo y puntos otorgados para análisis de desempeño y gamificación.

## Confiabilidad y seguridad
- **Seguridad funcional:** interlocks del PLC, enclavamiento de puerta y paro de emergencia evitan movimientos peligrosos.
- **Resiliencia:** la PC almacena en buffer eventos/imágenes si la conectividad falla y los reenvía al restablecer la red.
- **Ciberseguridad:** comunicaciones HTTPS y APIs protegidas con tokens.
- **Privacidad:** los eventos sin identificación se mantienen anónimos y solo alimentan métricas agregadas.

## Valor agregado
La combinación de robótica, visión y gamificación hace visible el proceso de reciclaje, entrega retroalimentación inmediata y fomenta la participación comunitaria. La modularidad de la arquitectura permite mejorar componentes individuales (gripper, modelo de IA, nuevos sensores) sin rediseñar el sistema completo.
