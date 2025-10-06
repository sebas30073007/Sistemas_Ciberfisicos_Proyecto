---
title: Diseño de la PCB
layout: default
parent: Interfaz Usuario
nav_order: 1
---


## Vistas de la PCB
![Diagrama esquemático de la PCB]({{ "/assets/img/PCB_diagrama_esquema.jpg" | relative_url }})
![Distribución de componentes en la PCB]({{ "/assets/img/PCB_placa_esquema.jpg" | relative_url }})
![Modelo 3D de la PCB]({{ "/assets/img/PCB_placa_esquema_3D.jpg" | relative_url }})

---

## ¿Qué hace esta placa?
Esta placa es el “cerebro embebido” del módulo: **lee tarjetas RFID**, **se comunica por USB/Serial** y **emite confirmaciones audibles**. El núcleo es un **ESP32-WROOM-32**; el lector **RC522** se conecta por **SPI**; un **buzzer** integrado da feedback; y un **USB-UART TTL** permite programar y depurar desde el puerto serie. Con esto se identifican usuarios, se registran eventos y se envían datos a app/nube sin módulos extra.

---

## Bloques de hardware
1) **ESP32 (zona superior-izquierda)**  
   - Mantener *keep-out* bajo la antena (sin cobre ni tornillería) para no degradar Wi-Fi/BLE.  
   - Pines de arranque: **EN** (reset) y **BOOT** (GPIO0) accesibles; LED(s) de estado para flashing.

2) **RC522 por SPI**  
   - Líneas: **SCK**, **MOSI**, **MISO**, **SS/SDA**, **RST** rutadas en paralelo y lo más cortas posible.  
   - Antena del RC522 despejada de metal (y de planos de cobre) para mejor lectura.

3) **USB-UART TTL**  
   - Conector de **4 pines**: **TX**, **RX**, **VCC**, **GND** para programación/monitor.  
   - Señales UART encaminadas al borde para acceso cómodo.

4) **Buzzer**  
   - Ubicado en esquina **inferior-derecha**; alimentado a **3.3 V** con limitación.  
   - Aislado del bus SPI para evitar acople de ruido.

---

## Conectividad y pinout de referencia

**Alimentación**
- **VDD = 3.3 V** para toda la placa (ESP32, RC522 y buzzer).

**UART0 – Programación**
- **Pin 1:** GND  
- **Pin 2:** VDD (3.3 V)  
- **Pin 3:** TX0 (ESP32 → PC) — GPIO1  
- **Pin 4:** RX0 (PC → ESP32) — GPIO3

**SPI – Lector RC522 (J3, 8 pines)**

| Señal RC522 | Net en PCB | GPIO ESP32 | Nota          |
|-------------|------------|------------|---------------|
| VDD         | VDD        |            | 3.3 V         |
| RST         | RST        | GPIO21     | Reset RC522   |
| MISO        | MISO       | GPIO19     | VSPI MISO     |
| MOSI        | MOSI       | GPIO23     | VSPI MOSI     |
| SCK         | SCK        | GPIO18     | VSPI SCK      |
| SDA / SS    | SDA        | GPIO5      | Chip select   |
| GND         | GND        |            | Plano de masa |

**Botones**
- **EN (EN)** y **BOOT (GPIO0)** accesibles para modo de carga.  
- **SW1 de usuario** en **GPIO16** (entrada con pull-up a VDD).

**Indicadores**
- **LED1** en **GPIO2**.  
- **LED2** en **GPIO17**.

**Actuador**
- **Buzzer** en net **BUZZ → GPIO22** (a través de R12, retorno a GND).


---
## Consideraciones de diseño y montaje
- Placa de una capa con plano de masa envolvente para minimizar ruido.
- Cuatro orificios de fijación en las esquinas para asegurar al gabinete y reducir vibración.
- Huellas de resistencias y capacitores en tamaño 1206 para facilitar soldadura manual.
- Área bajo la antena del ESP32 sin cobre ni tornillería, evitando degradar el enlace inalámbrico.