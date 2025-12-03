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

### 1.1 Variables principales

- **M0.3 – Habilitación automática**  
  Bit interno que indica que el sistema está listo para mover la puerta (seguridad OK, relé energizado, etc.).

- **CMD_ABRIR (M0.4)**  
  Orden de apertura de la puerta. Cuando está a 1, el motor gira en el sentido de apertura.

- **Q_PULSO_STEPPER**  
  Salida digital del PLC conectada a la entrada de **PULSO** del driver del motor a pasos.

- **Q_DIR_STEPPER**  
  Salida digital conectada a la entrada de **DIRECCIÓN** del driver.

- **PULSO_ON / PULSO_OFF**  
  Marcas internas generadas por temporizadores TON que permiten fijar la duración de los estados alto y bajo del pulso.

### 1.2 Red de generación del tren de pulsos

En la primera red se combina:

- **M0.3 (habilitación)**  
- **CMD_ABRIR**  
- **PULSO_OFF**  
- **PULSO_ON** (como contacto normalmente cerrado)  
- Un **contacto de realimentación** de la propia salida **Q_PULSO_STEPPER** en paralelo

De forma resumida:

> Mientras el sistema esté habilitado y se reciba la orden de abrir, la salida **Q_PULSO_STEPPER** se mantiene oscilando, generando un tren de pulsos para el driver.

El contacto en paralelo de Q_PULSO_STEPPER actúa como **auto-mantenimiento**, garantizando que la red no se detenga en cada flanco.

### 1.3 Temporizadores para dar forma al pulso

Las siguientes dos redes contienen dos temporizadores TON:

- **TON IEC_Timer_0_DB**  
  - Entrada **IN**: Q_PULSO_STEPPER.  
  - Tiempo **PT = 1 ms**.  
  - Salida **Q**: activa la marca **PULSO_ON**.

- **TON IEC_Timer_0_DB_1**  
  - Entrada **IN**: contacto inverso de Q_PULSO_STEPPER.  
  - Tiempo **PT = 1 ms**.  
  - Salida **Q**: activa la marca **PULSO_OFF**.

Con esta estructura se consigue que:

- El flanco de activación de Q_PULSO_STEPPER produzca un tiempo mínimo en alto (**PULSO_ON**).  
- El flanco contrario genere un tiempo mínimo en bajo (**PULSO_OFF**).

El resultado es un **pulso cuadrado bien definido**, con tiempos ajustables mediante los parámetros PT, que cumple las especificaciones mínimas de tiempo de pulso del driver del motor a pasos.

### 1.4 Selección de sentido de giro

En la última red:

- El bit **CMD_ABRIR (M0.4)** se usa para activar la salida **Q_DIR_STEPPER**.

Cuando CMD_ABRIR está activo:

- **Q_DIR_STEPPER = 1** → el driver interpreta “giro en sentido de apertura”.

Para el sentido de cierre, se utilizará el valor contrario de esta señal o una lógica complementaria en otro tramo del programa, según la estrategia de control definida.

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
