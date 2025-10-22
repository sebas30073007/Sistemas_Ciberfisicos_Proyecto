---
title: Inicio
layout: home
nav_order: 1
redirect_from:
  - /conexiones/diagrama-a-bloques/
---

# Robot clasificador de residuos

El proyecto documenta el desarrollo de un robot que identifica vidrio, latas y envases Tetra Pak para separarlos automáticamente. Aquí encontrarás desde la arquitectura electrónica hasta la lógica de clasificación y las interfaces de operación.

## Cómo navegar la documentación

- [Gabinete Robot]({{ "/gabinete-robot/" | relative_url }}): Infraestructura física, cableado e interfaces embebidas.
- [Nube]({{ "/nube/" | relative_url }}):
- [Interacción Usuario]({{ "/interaccion-usuario/" | relative_url }}): Aplicaciones, flujos y retroalimentación para los usuarios.

Cada sección incluye un índice con enlaces a subsecciones específicas. La información sirve como punto de partida para que ajustes los detalles técnicos con datos del proyecto.

## Estado del proyecto
- **Equipo:** Haili Avila, Daniela Colin y Sebastián Méndez.
- **Objetivo:** automatizar la recolección y clasificación básica de residuos reciclables.
- **Tecnologías clave:** UR3, visión por computadora, sistemas embebidos, estructura funcional y una interfaz.

## Diagrama a bloques

![Diagrama general del proyecto]({{ "/assets/img/Proyecto.png" | relative_url }})

### Visión general
La arquitectura se compone de tres dominios que se comunican entre sí: el gabinete del robot (infraestructura física), la nube (servicios y procesamiento) y las interfaces de usuario (experiencia del operador y del público). Esta estructura permite separar responsabilidades sin perder trazabilidad entre eventos.

### Componentes principales
#### Gabinete del robot
- **Robótica y sensado:** UR3 con cámara (montada en la muñeca) y gripper para manipulación del residuo.
- **Sensores auxiliares:** barrera infrarroja, sensores de proximidad, peso e inductivo para detectar presencia de objetos y condiciones seguras.
- **Control y seguridad:** PLC para interlocks (puertas, paro de emergencia) y PC que coordina la secuencia y se comunica con la nube.
- **Red local:** todos los elementos se interconectan a través de un switch dedicado que aísla la red de control.

#### Nube y servicios
- **APIs en Python:** reciben imágenes y eventos, orquestan la clasificación y exponen datos a otras aplicaciones.
- **Motor de IA:** se ejecuta en la nube.
- **Base de datos y almacenamiento:** conserva usuarios, sesiones, vínculos a evidencias fotográficas y métricas de cada ciclo.
- **Dashboards web/móvil:** muestran KPIs, ranking y tablas de puntos para seguimiento operativo y gamificación.

#### Interfaces de usuario
- **HMI local:** guía al usuario durante el depósito, muestra instrucciones, confirma resultados y reproduce mensajes de audio.
- **Sitio web / app:** permite revisar el ranking global, el historial personal y las reglas de premiación cuando estén disponibles.

## Diagrama a bloques

![Diagrama general del algoritmo]({{ "/assets/img/Algoritmo.png" | relative_url }})

### Flujo operativo
1. El usuario se identifica (RFID) o opera como invitado.
2. La cabina detecta el residuo, captura la imagen y clasifica el material.
3. El UR3 deposita el objeto en el contenedor adecuado.
4. La PC registra un evento completo en la base de datos (usuario, material, fecha).
5. Se actualiza el puntaje y ranking en la HMI y en los dashboards en tiempo real.

### Datos críticos
- Identificadores: usuario (si aplica), máquina.
- Trazabilidad: fecha/hora, material clasificado.
- Operación: duración del ciclo y puntos otorgados para análisis de desempeño.

### Valor agregado
La combinación de robótica, visión y gamificación hace visible el proceso de reciclaje, entrega retroalimentación inmediata y fomenta la participación comunitaria. La modularidad de la arquitectura permite mejorar componentes individuales (gripper, nuevos sensores) sin rediseñar el sistema completo.

