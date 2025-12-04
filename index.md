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
[![Video demostrativo](https://img.youtube.com/vi/4pZCZ6m2o4M/0.jpg)](https://youtu.be/4pZCZ6m2o4M)



---

## Estado del proyecto
- **Equipo:** Haili Avila, Daniela Colin y Sebastián Méndez.
- **Objetivo:** automatizar la recolección y clasificación básica de residuos reciclables.
- **Tecnologías clave:** UR3, visión por computadora, sistemas embebidos, estructura funcional y una interfaz de usuario.

---

## Diagrama a bloques

![Diagrama general del proyecto]({{ "/assets/img/general.png" | relative_url }})
La arquitectura se compone de tres dominios que se comunican entre sí: el gabinete del robot (infraestructura física), la nube (servicios y procesamiento) y las interfaces de usuario (experiencia del público).

---

## Diagrama de topología

![Diagrama de topología y jerarquia]({{ "/assets/img/Diagrama-topologia.jpg" | relative_url }})
El diagrama de topología muestra cómo los servicios en la nube (Firebase, Render y GitHub Pages) se comunican con la infraestructura local del robot. La Jetson actúa como nodo central en la red local, coordinando a las Raspberry Pi y enlazándose con los dispositivos industriales: el sensor, el manipulador UR3 y el PLC Siemens. Cada elemento opera con una dirección IP definida dentro de la red 192.168.1.x, mientras que los servicios externos se acceden mediante sus respectivos dominios públicos e IPs resueltas por DNS.


---

### Tabla de descripción del sistema

| Categoría | Función dentro del sistema |
|----------|-----------------------------|
| **Gabinete del robot – Red y comunicaciones** | El router da acceso a Internet y conecta todos los módulos internos. Dentro del gabinete se usan protocolos como SPI, Serial, HDMI y Ethernet para la comunicación entre sensores, actuadores y el procesador central. |
| **Gabinete del robot – Control general** | Una PC dedicada coordina el funcionamiento completo del robot: procesa entradas del HMI, ejecuta lógica de operación, controla secuencias y mantiene comunicación con la nube. |
| **Gabinete del robot – Interfaz de Usuario** | Identifica al usuario mediante una tarjeta RFID (ID único) y muestra instrucciones e indicaciones durante el proceso. |
| **Gabinete del robot – Recepción de residuos** | Incluye los sensores y mecanismos industriales que detectan, validan y verifican si un residuo es aceptable para el sistema. |
| **Gabinete del robot – Robot** | El brazo UR3 realiza la recolección y clasificación de residuos utilizando un modelo de visión artificial para reconocer objetos. |
| **Nube y servicios – APIs en Python** | Reciben imágenes y eventos desde el robot, coordinan la clasificación y exponen información para otros servicios. |
| **Nube y servicios – Base de datos y almacenamiento** | Guarda usuarios, sesiones, evidencia fotográfica y métricas operativas de cada ciclo del sistema. |
| **Interfaces de usuario – HMI local** | Acompaña al usuario durante el depósito del residuo: muestra instrucciones, confirma resultados y reproduce mensajes de audio. |
| **Interfaces de usuario – Sitio web / App** | Permite consultar ranking global, historial personal y reglas de premiación cuando estén disponibles. |


---