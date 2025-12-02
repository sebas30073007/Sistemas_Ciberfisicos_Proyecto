---
title: RFID reader
layout: default
parent: Interfaz Usuario
nav_order: 1
---

## ¿Qué hace esta placa?
Esta placa es el “cerebro embebido” : **lee tarjetas RFID**, **se comunica por USB/Serial** y **emite confirmaciones audibles**. El núcleo es un **ESP32-WROOM-32**; el lector **RC522** se conecta por **SPI**; un **buzzer** integrado da feedback; y un **USB-UART TTL** permite programar y depurar desde el puerto serie. Con esto se identifican usuarios, se registran eventos y se envían datos a app/nube sin módulos extra.

---

## Vistas de la PCB

La tarjeta está basada en un **ESP32-WROOM-32** y actúa como placa base para pruebas de firmware con entradas digitales, salidas (LEDs y buzzer) y un conector de expansión para periféricos externos.  
El programador USB–Serial se mantiene como módulo aparte para mantener la tarjeta sencilla y reutilizable.

![PCB ensamblada con programador USB-Serial](img/pcb_ensamble.jpg)

En la fotografía se aprecia:

- El **módulo ESP32** en la parte superior izquierda.
- Tres **botones** (S1, S2, S3) en la zona central:
  - S1 – `EN` (reset del ESP32).
  - S2 – `BOOT` (modo de programación).
  - S3 – botón de usuario.
- El **LED de estado** cerca del borde inferior, útil para pruebas rápidas.
- El **buzzer** BZ1 en la esquina inferior derecha.
- El adaptador **USB-Serial** conectado al header inferior, que proporciona alimentación y líneas TX/RX.

---

## Esquemático eléctrico

El esquemático se divide en bloques funcionales: ESP32, lógica de reset/boot, indicadores y conectores de expansión.

![Esquemático principal de la tarjeta](img/pcb_schematic.png)

### Bloque ESP32

El bloque principal es el módulo **ESP32-WROOM-32 (U1)**:

- Pines de alimentación **3.3 V** y **GND** con capacitores de desacoplo cercanos (C1, C2, etc.).
- Pines de IO asignados a:
  - LEDs (por ejemplo `GPIO2`, `GPIO17`).
  - Buzzer.
  - Bus SPI/I²C expuesto en el conector de expansión J3.
- Las líneas UART (`TXD0`/`RXD0`) se llevan al conector de programación J1.

### Botones de EN, BOOT y usuario

En la parte superior del esquemático está la red de resistencias y botones:

- **S1 – EN**: resetea el ESP32.  
  - Resistencia pull-up mantiene `EN` en alto y el botón lo lleva a GND.
- **S2 – BOOT**: fuerza el modo de programación al mantenerlo presionado durante el reset.
- **S3 – SW1**: botón de propósito general conectado a un GPIO, con su correspondiente red de resistencias.

Esto permite flashear el ESP32 manualmente sin depender de auto-reset por hardware.

### Indicadores LED

![Bloque de LEDs e indicadores](img/pcb_leds.png)

El esquema incluye al menos dos LEDs (D1 y D2) con sus resistencias en serie:

- Uno se usa como **LED de alimentación/estado**.
- El otro puede quedar para depuración de firmware (parpadeos, errores, etc.).

Ambos están conectados a GPIOs configurables desde software.

### Conectores de expansión y buzzer

![Conectores y buzzer](img/pcb_connectors_buzzer.png)

- **J1 (UART)**: conector de 4 pines para el adaptador USB-Serial  
  (TX, RX, VCC y GND).  
- **J2**: conector de 3 pines (por ejemplo VDD, señal, GND) pensado para algún sensor simple o entrada digital.
- **J3 (header de 8 pines)**: expone:
  - VDD y GND.
  - Líneas **RST** y varios GPIOs.
  - Bus **SPI/I²C** (MISO, MOSI, SCK, SDA) para conectar displays, sensores o módulos externos.
- **BZ1 + R12**: salida para **buzzer**, con resistencia limitadora/driver. Ideal para feedback acústico (beeps de error, confirmación, etc.).

---

## Diseño de la PCB (layout)

El diseño se realizó en una PCB de **dos capas**, con plano de referencia mayormente en la capa inferior y ruteo de señales en la superior.

![Layout de la PCB con plano de cobre](img/pcb_layout.png)

Aspectos importantes del layout:

- Se respetó una **zona de keep-out** bajo la antena del ESP32 para no degradar la señal RF:
  - Sin cobre ni pistas.
  - Sin componentes metálicos en esa región.
- El ruteo principal de señales del ESP32 sale hacia el centro de la placa y luego se distribuye hacia:
  - Los botones de EN/BOOT.
  - El header de programación.
  - El conector de expansión J3.
- Se usan pistas relativamente anchas para alimentación y pistas estándar para señales digitales.
- Hay **vias de retorno a GND** distribuidas para reducir la inductancia de la malla de tierra.

---

## Vista 3D y ensamblaje

La vista 3D permite verificar la colocación física de los componentes y la ergonomía de los botones y conectores.

![Vista 3D de la PCB con keep-out de antena](img/pcb_3d.png)

En este render se observa:

- El **módulo ESP32** con la antena apuntando hacia la parte superior, con la etiqueta **KEEP-OUT ZONE** claramente marcada.
- Ubicación accesible de:
  - Botones S1, S2, S3.
  - Header inferior para el programador USB-Serial.
  - Buzzer en la esquina, evitando interferencias mecánicas con otros módulos.
- **Orificios de montaje** en las esquinas para fijar la tarjeta dentro de una caja o prototipo.

---

## Posibles mejoras para la siguiente revisión

- Añadir una **serigrafía más descriptiva** en los conectores (por ejemplo, etiquetar pines de J3: `VDD`, `GND`, `MISO`, `MOSI`, etc.).
- Incluir **pads de test** para señales críticas (TX/RX, 3.3 V, GND, alguna línea de debug).
- Considerar un pequeño **fusible resettable (PTC)** o protección adicional en la entrada de alimentación.
- Dejar un borde libre cerca del conector de programación para que el adaptador USB-Serial no choque con otros elementos mecánicos.

---
