---
title: RFID reader
layout: default
parent: Interfaz Usuario
nav_order: 1
---

## ¿Qué hace esta placa?
Esta placa es el “cerebro embebido” : **lee tarjetas RFID**, **se comunica por USB/Serial** y **emite confirmaciones audibles**. El núcleo es un **ESP32-WROOM-32**; el lector **RC522** se conecta por **SPI**; un **buzzer** integrado da feedback; y un **USB-UART TTL** permite programar y depurar desde el puerto serie. Con esto se identifican usuarios, se registran eventos y se envían datos a app/nube sin módulos extra.

---

## Esquematico

![Diagrama esquemático de la PCB]({{ "/assets/img/PCB_diagrama_esquema.jpg" | relative_url }})
Diseño esquemático de la placa, donde se muestran las conexiones internas entre el ESP32, los botones de arranque, los LEDs, el buzzer, los conectores hacia el lector RC522 y la interfaz USB-UART. Algunas resistencias son de **0 Ω** y se usan únicamente como puentes para cruzar pistas en el PCB, sin modificar el comportamiento eléctrico del circuito.


---

## Distribución y ruteo en la PCB

![Distribución de componentes en la PCB]({{ "/assets/img/PCB_placa_esquema.jpg" | relative_url }})
Vista del ruteo de la PCB: se muestran las pistas que interconectan todos los componentes, trabajando prácticamente como una placa de **una sola capa** (todas las pistas van en la misma cara), salvo una única conexión que se llevó a la otra capa. En la parte superior se aprecia también el área de *keep-out* bajo la antena del ESP32.


---

## Vistas de la PCB

![PCB real]({{ "/assets/img/PCB-real.jpg" | relative_url }})
Vista de la PCB real ensamblada, con el módulo ESP32, botones, LED de estado y buzzer montados.


![Distribución de componentes en la PCB]({{ "/assets/img/PCB_placa_esquema.jpg" | relative_url }})
Distribución de componentes en la tarjeta, destacando las zonas de lógica, conectores y el área de keep-out bajo la antena del ESP32.

![Modelo 3D de la PCB]({{ "/assets/img/PCB_placa_esquema_3D.jpg" | relative_url }})
Modelo 3D de la PCB, útil para revisar interferencias mecánicas y la accesibilidad de conectores y botones.

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

| Señal RC522 | GPIO ESP32 | Nota          |
|-------------|------------|---------------|
| VDD         |            | 3.3 V         |
| RST         | GPIO21     | Reset RC522   |
| MISO        | GPIO19     | VSPI MISO     |
| MOSI        | GPIO23     | VSPI MOSI     |
| SCK         | GPIO18     | VSPI SCK      |
| SDA / SS    | GPIO5      | Chip select   |
| GND         |            | Plano de masa |

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

---

## Fabricación
La PCB fue mandada a manofacturar a los laboratorios de JLCPCB: [Descargar archivos Gerber]( {{ "assets/documentos/ESP32_Finaaaaal.zip" | relative_url }} ){: .btn .btn-primary }

![PCB ordenada]({{ "/assets/img/PCB_JLCPCB.jpg" | relative_url }})
