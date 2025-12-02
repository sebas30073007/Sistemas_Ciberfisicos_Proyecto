---
title: Interacción Usuario
layout: default
nav_order: 4
has_children: true
permalink: /interaccion-usuario/
---

# Algoritmo de funcionamiento

![Diagrama general del algoritmo]({{ "/assets/img/Algoritmo.png" | relative_url }})

## Flujo operativo
1. Preparación: el PLC abre la puerta y los sensores verifican que no haya obstrucciones.
2. Colocación: la pantalla indica cómo acomodar el objeto; cuando queda alineado, se continúa.
3. Clasificación local: la cámara toma una imagen y la PC/Raspberry decide si es lata, vidrio o Tetra Pak.
4. Si no coincide, se marca como incompatible y se pide retirarlo.
5. Acción del robot: el UR3 ejecuta la rutina correspondiente y deposita el residuo en su contenedor.
6. Cierre y feedback: aparece una animación de confirmación (+1), el robot vuelve a Home, se cierra la puerta y el sistema queda listo para el siguiente usuario.


## Datos críticos
- Identificadores: usuario.
- Trazabilidad: fecha/hora, material clasificado y clasificación.
- Operación: duración del ciclo y puntos otorgados.
