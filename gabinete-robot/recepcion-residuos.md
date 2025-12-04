---
title: Recepción de residuos
layout: default
parent: Gabinete Robot
nav_order: 3
has_children: true
---

En esta sección se describe **cómo se recibe el residuo en el gabinete**, centrándonos en:

- La lógica del **PLC** que genera los pulsos para el motor a pasos.
- El **mecanismo de la puerta** accionado por un **NEMA 17** y su driver.
- Las **conexiones eléctricas de mando y potencia** asociadas a este conjunto (sin entrar en temas de comunicación).

---

## 1. Lógica del PLC para el motor de la puerta

![Diagrama en escalera del PLC]({{ "/assets/img/diagrama_stepper.jpg" | relative_url }})

El PLC Siemens ejecuta un pequeño programa en escalera encargado de **generar los pulsos de movimiento** para el motor a pasos que abre y cierra la puerta de recepción. La idea es convertir una orden sencilla (“abrir puerta”) en una secuencia de pulsos con dirección definida.

---

## 2. Actuador NEMA 17, puerta y driver

El movimiento real de la puerta se logra con:

- Un **motor a pasos NEMA 17**, montado en el gabinete.  
- Un **driver de micro-pasos DC 9–42 V**.  
- Un mecanismo de transmisión mecánica (**correa-polea**) que convierte el giro del eje del motor en **movimiento lineal de la puerta**.

### 2.1 Señales que llegan al driver

Desde el PLC llegan cuatro señales de mando al driver:

- **Q_PULSO_STEPPER → entrada PUL−** del driver.  
- **Q_DIR_STEPPER → entrada DIR−**.  
- **PUL+ y DIR+** se encuentran cableadas de forma permanente a **+24 VDC**.  

La alimentación de potencia del driver (VCC y GND) proviene de la fuente de **24 VDC**, conmutada por el relé de seguridad descrito en la sección de “Conexiones industriales y de potencia”. Así, ante un paro de emergencia, el driver queda sin energía y el motor se detiene.

### 2.2 Movimiento de la puerta

Cuando la salida **Q_PULSO_STEPPER** emite el tren de pulsos:

- El driver genera **pequeños pasos angulares** en el NEMA 17.  
- Cada paso se traduce, a través del mecanismo mecánico, en un **avance o retroceso de la puerta**.  
- La combinación de **número de pasos** y **sentido (Q_DIR_STEPPER)** determina si la puerta se abre o se cierra, así como la velocidad con la que se realiza el movimiento.

Los parámetros de micro-paso y corriente del driver se ajustan en sus DIP-switches para equilibrar **suavidad de movimiento, par disponible y ruido mecánico**.

---

## 3. Programa del UR3 durante la recepción

![Teach Pendant del UR3 con secuencia de recepción]({{ "/assets/img/teachPendant.jpg" | relative_url }})

El robot UR3 ejecuta un programa específico para la **recepción de residuos**, escrito en URScript y cargado desde el teach pendant. Con movimientos `movej()` hacia puntos predefinidos (P4, P5, P6, etc.) tenemos:
  - Posición de HOME.  
  - Posición sobre la puerta. 

La secuencia típica es:

1. El UR3 se manda a una posicion de HOME.
2. El PLC abre la puerta usando el NEMA 17.  
3. El UR3 ejecuta el programa de posición-observación, situandose sobre la puerta.
4. Se ejecuta el modelo de clasificación.

Toda la lógica de seguridad y el enclavamiento eléctrico (paros, relé, corte de potencia) se mantiene independiente y fue descrita en la sección de **Conexiones industriales y de potencia**; aquí únicamente se detalla la **parte mecánica y de programación asociada a la recepción de residuos**.

---
