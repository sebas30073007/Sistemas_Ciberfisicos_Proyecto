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

---

## Estado del proyecto
- **Equipo:** Haili Avila, Daniela Colin y Sebastián Méndez.
- **Objetivo:** automatizar la recolección y clasificación básica de residuos reciclables.
- **Tecnologías clave:** UR3, visión por computadora, sistemas embebidos, estructura funcional y una interfaz de usuario.

---

## Diagrama a bloques

![Diagrama general del proyecto]({{ "/assets/img/Diagrama_a_bloques.jpg" | relative_url }})
La arquitectura se compone de tres dominios que se comunican entre sí: el gabinete del robot (infraestructura física), la nube (servicios y procesamiento) y las interfaces de usuario (experiencia del público).

---

## Diagrama de topología

![Diagrama de topología y jerarquia]({{ "/assets/img/Diagrama-topologia.jpg" | relative_url }})
El diagrama de topología muestra cómo los servicios en la nube (Firebase, Render y GitHub Pages) se comunican con la infraestructura local del robot. La Jetson actúa como nodo central en la red local, coordinando a las Raspberry Pi y enlazándose con los dispositivos industriales: el sensor, el manipulador UR3 y el PLC Siemens. Cada elemento opera con una dirección IP definida dentro de la red 192.168.1.x, mientras que los servicios externos se acceden mediante sus respectivos dominios públicos e IPs resueltas por DNS.


---

### Tabla de descripción del sistema

| Categoría | Descripción |
|----------|-------------|
| **Gabinete del robot – Red y comunicaciones** | Un router provee al sistema de conexión a Internet. Aparte los diversos módulos del gabinete usan protocolos SPI, Serial, HDMI, Ethernet para interactuar entre ellos o con el procesador central. |
| **Gabinete del robot – Control general** | Una PC dedicada coordina las operaciones del robot, inputs del HMI y comunicación con la nube, así como accionar secuencias lógicas (procesos pre-establecidos de funcionamiento). |
| **Gabinete del robot – Interfaz de Usuario** | Identifica al usuario mediante tarjeta (ID único), muestra instrucciones e indicaciones. |
| **Gabinete del robot – Recepción de residuos** | Contiene los componentes industriales y robustos de sensado y verificación de aceptación de residuos "permitidos". |
| **Gabinete del robot – Robot** | Manipulador UR3 que recolecta y clasifica residuos con ayuda de un modelo de detección por visión artificial. |
| **Nube y servicios – APIs en Python** | Reciben imágenes y eventos, orquestan la clasificación y exponen datos a otras aplicaciones. |
| **Nube y servicios – Motor de IA** | Se ejecuta en la nube. |
| **Nube y servicios – Base de datos y almacenamiento** | Conserva usuarios, sesiones, vínculos a evidencias fotográficas y métricas de cada ciclo. |
| **Nube y servicios – Dashboards web/móvil** | Muestran KPIs, ranking y tablas de puntos para seguimiento operativo y gamificación. |
| **Interfaces de usuario – HMI local** | Guía al usuario durante el depósito, muestra instrucciones, confirma resultados y reproduce mensajes de audio. |
| **Interfaces de usuario – Sitio web / app** | Permite revisar el ranking global, el historial personal y las reglas de premiación cuando estén disponibles. |

---