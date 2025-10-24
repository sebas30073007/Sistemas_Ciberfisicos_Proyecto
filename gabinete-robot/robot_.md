---
title: Robot
layout: default
parent: Gabinete Robot
nav_order: 9
has_children: true
redirect_from:
  - /conexiones/arquitectura-electrica/
---

Esta sección concentra los elementos directamente involucrados en la manipulación de residuos: el brazo colaborativo UR3, los sensores de visión y los accesorios que le permiten operar dentro del gabinete.

## Alcance del sistema robótico

- **Brazo UR3.** Montaje mecánico, cableado de potencia y lógica de seguridad asociada a paros de emergencia.
- **Percepción.** Cámara RGB-D y accesorios de iluminación que alimentan al algoritmo de clasificación.
- **Herramental final.** Adaptadores, grippers y piezas impresas en 3D que permiten manipular los envases.

Cada componente está descrito en las subpáginas que se listan a continuación, incluyendo conexiones, parámetros de calibración y recomendaciones de mantenimiento.

## Guía de lectura

1. Comienza por el **[brazo UR3](./robot/ur3.html)** para conocer su integración mecánica, el ruteo de cables y las rutinas de homeado.
2. Continúa con la **[cámara](./robot/camara.html)** para entender la configuración óptica, el montaje y el enlace con el stack de visión.
3. Consulta los anexos dentro de cada página para revisar listas de repuestos, versiones de firmware y pasos de diagnóstico.

Este índice busca ofrecer un mapa claro de todos los elementos que orbitan al robot, facilitando la transición desde el diseño conceptual hasta la operación diaria.
