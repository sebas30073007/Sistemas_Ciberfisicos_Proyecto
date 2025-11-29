---
title: Inicio
layout: home
nav_order: 1
redirect_from:
  - /conexiones/diagrama-a-bloques/
---

# Robot clasificador de residuos

Este proyecto documenta el desarrollo de un robot que identifica vidrio, latas y envases de Tetra Pak para separarlos automáticamente. Aquí encontrarás desarrollado la arquitectura, electrónica, lógica de clasificación y las interfaces de operación.
Cada sección incluye un índice con enlaces a subsecciones específicas.

## Estado del proyecto
- **Equipo:** Haili Avila, Daniela Colin y Sebastián Méndez.
- **Objetivo:** automatizar la recolección y clasificación básica de residuos reciclables.
- **Tecnologías clave:** UR3, visión por computadora, sistemas embebidos, estructura funcional y una interfaz de usuario.

## Diagrama a bloques

![Diagrama general del proyecto]({{ "/assets/img/Diagrama_a_bloques.jpg" | relative_url }})


### Visión general
La arquitectura se compone de tres dominios que se comunican entre sí: el gabinete del robot (infraestructura física), la nube (servicios y procesamiento) y las interfaces de usuario (experiencia del público).

### Componentes principales
#### Gabinete del robot
- **Red y comunicaciones:** Un router provee al sistema de conexión a Internet. Aparte los diversos modulos del gabinete usan protocolos SPI, Serial, HDMI, Ethernet para interactuar entre ellos o con el procesador central.
- **Control general:** Una PC dedicada coordina las operaciones del robot, inputs del HMI y comunicación con la nube, así como accionar secuencias lógicas (procesos pre-establecidos de funcionamiento).
- **Interfaz de Usuario:** Identidfica al usuario mediante tarjeta (ID único), muestra instrucciones e indicaciones.
- **Recepción de residuos:** contiene los componentes industriales y robustos de sensado y verificación de aceptación de residuos "permitidos".
- **Robot:** Manipulador UR3 que recolecta y clasifica residuos con ayuda de un modelo de detección por vision artificial.

#### Nube y servicios
- **APIs en Python:** reciben imágenes y eventos, orquestan la clasificación y exponen datos a otras aplicaciones.
- **Motor de IA:** se ejecuta en la nube.
- **Base de datos y almacenamiento:** conserva usuarios, sesiones, vínculos a evidencias fotográficas y métricas de cada ciclo.
- **Dashboards web/móvil:** muestran KPIs, ranking y tablas de puntos para seguimiento operativo y gamificación.

#### Interfaces de usuario
- **HMI local:** guía al usuario durante el depósito, muestra instrucciones, confirma resultados y reproduce mensajes de audio.
- **Sitio web / app:** permite revisar el ranking global, el historial personal y las reglas de premiación cuando estén disponibles.


## Diagrama a bloques del Algoritmo

![Diagrama general del algoritmo]({{ "/assets/img/Algoritmo.png" | relative_url }})

### Flujo operativo
1. Preparación: el PLC abre la puerta y los sensores verifican que no haya obstrucciones.
2. Colocación: la pantalla indica cómo acomodar el objeto; cuando queda alineado, se continúa.
3. Clasificación local: la cámara toma una imagen y la PC/Raspberry decide si es lata, vidrio o Tetra Pak.
4. Si no coincide, se marca como incompatible y se pide retirarlo.
5. Acción del robot: el UR3 ejecuta la rutina correspondiente y deposita el residuo en su contenedor.
6. Cierre y feedback: aparece una animación de confirmación (+1), el robot vuelve a Home, se cierra la puerta y el sistema queda listo para el siguiente usuario.


### Datos críticos
- Identificadores: usuario.
- Trazabilidad: fecha/hora, material clasificado y clasificación.
- Operación: duración del ciclo y puntos otorgados.

### Valor agregado
La combinación de robótica, visión y gamificación hace visible el proceso de reciclaje, entrega retroalimentación inmediata y fomenta la participación comunitaria. La modularidad de la arquitectura permite mejorar componentes individuales (gripper, modelo de IA, nuevos sensores) sin rediseñar el sistema completo.
