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

![Diagrama en escalera del PLC]({{ "/assets/img/Diagrama-PLC.jpg" | relative_url }})

El PLC Siemens ejecuta un pequeño programa en escalera encargado de **generar los pulsos de movimiento** para el motor a pasos que abre y cierra la puerta de recepción. La idea es convertir una orden sencilla (“abrir puerta”) en una secuencia de pulsos con dirección definida.

---

## 2. Actuador NEMA 17, puerta y driver

El movimiento real de la puerta se logra con:

- Un **motor a pasos NEMA 17**, montado en el gabinete.  
- Un **driver de micro-pasos DC 9–42 V**.  
- Un mecanismo de transmisión mecánica (por ejemplo, **husillo roscado, cremallera o sistema correa-polea**) que convierte el giro del eje del motor en **movimiento lineal de la puerta**.

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

El robot UR3 ejecuta un programa específico para la **recepción de residuos**, escrito en URScript y cargado desde el teach pendant. En la pantalla se aprecia una lista de instrucciones:

- Movimientos `movej()` y `movel()` hacia puntos predefinidos (P4, P5, P6, etc.) que corresponden a:
  - Posición de espera.  
  - Posición sobre la puerta.  
  - Posición de depósito del residuo.  

- Comandos al **gripper** (por ejemplo `sg_grip()`) para:
  - **Abrir la garra** y dejar caer el residuo en la tolva o bandeja de recepción.  
  - **Cerrar la garra** antes de retirarse o cuando toma un nuevo objeto.

La secuencia típica es:

1. El PLC posiciona la puerta en el estado requerido (abierta o cerrada) usando el NEMA 17.  
2. El UR3 ejecuta el programa de recepción: se mueve a la posición adecuada y actúa sobre el gripper.  
3. Una vez depositado el residuo, el robot regresa a una posición segura y la puerta puede volver a su estado inicial.

Toda la lógica de seguridad y el enclavamiento eléctrico (paros, relé, corte de potencia) se mantiene independiente y fue descrita en la sección de **Conexiones industriales y de potencia**; aquí únicamente se detalla la **parte mecánica y de programación asociada a la recepción de residuos**.

---
