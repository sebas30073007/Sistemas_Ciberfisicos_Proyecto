---
layout: default
title: Embebido-Lector RFID
parent: Conexiones
nav_order: 3
---

## Vistas de la PCB

![Diagrama esquemático de la PCB]({{ "/assets/img/PCB_diagrama_esquema.jpg" | relative_url }})

![Distribución de componentes en la PCB]({{ "/assets/img/PCB_placa_esquema.jpg" | relative_url }})

![Modelo 3D de la PCB]({{ "/assets/img/PCB_placa_esquema_3D.jpg" | relative_url }})

## Descripción general
Esta placa es el “cerebro embebido” de un módulo de interacción: lee tarjetas RFID, se comunica por Wi-Fi/Bluetooth y ofrece retroalimentación sonora. El núcleo es un **ESP32-WROOM-32**, suficiente para manejar periféricos y lógica de aplicación. Lo acompañan un **módulo RC522** (lector RFID por SPI), un **buzzer** integrado para confirmaciones audibles y un **convertidor UART TTL** que simplifica la programación y diagnóstico desde un puerto serie. Con este conjunto es posible identificar usuarios, registrar eventos y enviar datos a una app o a la nube sin módulos adicionales.

## Organización del hardware
- **Zona del ESP32:** ubicada en la parte superior izquierda con una *keep-out zone* debajo de la antena para preservar la potencia de la señal Wi-Fi/BLE.
- **Control de arranque:** pulsadores **EN** (reset) y **BOOT** junto con LEDs de estado permiten reinicios y entrada al modo de carga.
- **Bus SPI para el RC522:** líneas **SCK**, **MOSI**, **MISO**, **SDA/SS** y **RST** rutadas en paralelo hacia un cabezal dedicado para mantener longitudes similares y buena integridad de señal.
- **Módulo RFID:** puede montarse directamente sobre la tarjeta o como módulo externo conectado al cabezal, procurando que la antena quede libre de metal.
- **Buzzer integrado:** situado en la esquina inferior derecha y alimentado desde 3.3 V mediante resistencia de control, aislado para evitar acoplar ruido al bus SPI.

## Conectividad y alimentación
- **Conectores de 4 pines:** exponen TX, RX, VCC y GND para programación o monitoreo mediante un adaptador USB-TTL.
- **Conectores de 3 pines:** proveen VDD, GND y señales del RC522 o alimentación auxiliar según la configuración.
- **Distribución de energía:** la placa trabaja a 3.3 V. Un plano ancho alimenta al ESP32, RC522 y buzzer, con condensadores cerámicos cercanos para estabilizar el consumo durante transmisiones inalámbricas y lecturas RFID.
- **Ruteo de señales:** el bus SPI se mantiene en la cara superior con trayectorias rectas; las líneas UART viajan hacia el borde para facilitar el acceso.

## Consideraciones de diseño y montaje
- Placa de dos capas con plano de masa envolvente para minimizar ruido.
- Cuatro orificios de fijación en las esquinas para asegurar al gabinete y reducir vibración.
- Huellas de resistencias y capacitores en tamaño 1206 para facilitar soldadura manual.
- Área bajo la antena del ESP32 sin cobre ni tornillería, evitando degradar el enlace inalámbrico.
