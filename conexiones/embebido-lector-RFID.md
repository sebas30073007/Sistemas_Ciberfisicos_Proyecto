---
layout: default
title: Embebido-Lector RFID
parent: Conexiones
nav_order: 3
---

En este espacio detallaremos la construcción del sistema embebido que contiene el RFID y nos ayudará a registrar/identificar a los usuarios.


(assets/img/PCB_diagrama_squema.jpg)
(assets/img/PCB_placa_squema.jpg)
(assets/img/PCB_placa_squema_3D.jpg)


Descripción general de la PCB

Esta placa es el “cerebro embebido” de un módulo de interacción: lee tarjetas RFID, se comunica por Wi-Fi/Bluetooth y da retroalimentación sonora. El corazón es un ESP32-WROOM-32, que ofrece conectividad y potencia suficiente para manejar periféricos y lógica de aplicación. A su lado vive un módulo RC522 (lector RFID por SPI) que detecta y autentica tarjetas/llaveros; un buzzer integrado que permite confirmar acciones con pitidos; y un convertidor de señal UART TTL que facilita la programación y el diagnóstico por puerto serie. Con esto puedes identificar usuarios, registrar eventos y enviar los datos a una app o a la nube sin piezas adicionales.

Cómo está organizada

El ESP32 ocupa la zona superior izquierda y se ha reservado, a propósito, una KEEP-OUT ZONE sin cobre ni pistas bajo su antena. Ese “claro” garantiza que las señales de radio no se atenúen por el plano metálico, mejorando la cobertura Wi-Fi/BLE. Alrededor del ESP32 hay dos pulsadores: EN (reset) y BOOT, típicos en placas con este módulo para entrar al modo de carga y reiniciar; cerca también hay LEDs de estado con sus resistencias limitadoras, útiles para indicar encendido o actividad.

El RC522 se conecta por SPI al ESP32. En la placa verás las líneas SCK, MOSI, MISO, SDA/SS y RST rutadas en paralelo hasta un cabezal dedicado; esa agrupación reduce cruces y ayuda a mantener longitudes parecidas, lo que mejora la integridad de señal. El lector puede ir directamente sobre la tarjeta (si usas un módulo sin antena integrada) o como módulo externo conectado al cabezal, dejando la antena lo más libre posible de planos de cobre y tornillería para que el alcance sea estable.

El buzzer está colocado en la esquina inferior derecha. Se alimenta desde la línea de 3.3 V a través de una resistencia de control; sirve para confirmar lecturas o estados del sistema con beeps cortos. Junto a él hay pads para fijación y rutas despejadas que evitan acoplar ruido al bus SPI.

Para alimentación y consola, la placa incluye conectores de tres y cuatro pines. El de cuatro suele exponer TX, RX, VCC y GND (con el “convertidor TTL-serial” te conectas a un adaptador USB-TTL o a otro equipo). El de tres pines ofrece VDD, GND y RST del RC522 o alimentación auxiliar, según tu montaje. Los condensadores de desacoplo quedan próximos a la entrada de VDD y al propio ESP32 para filtrar picos de corriente en transmisiones Wi-Fi y lecturas RFID.

Flujo de energía y señales

La placa se alimenta a 3.3 V (ya sea desde un regulador previo o desde el sistema anfitrión). Esa línea se distribuye por un plano ancho y corto hacia el ESP32, el RC522 y el buzzer, con condensadores cerámicos cerca de cada consumidor para estabilizar. Las señales digitales de alta velocidad (SPI) viajan en la cara superior con trayectorias rectas y sin cambios de capa innecesarios; las líneas de UART para programación/diagnóstico son más tolerantes y se han llevado hacia el borde para un acceso cómodo. Toda la zona bajo la antena del ESP32 queda libre de cobre —lo verás sombreado en el layout— porque cualquier metal allí degrada el enlace de radio.

Construcción y montaje

La placa es de dos capas con plano de masa que rodea y devuelve corriente por el camino más corto, reduciendo ruido. Los cuatro agujeros de fijación permiten atornillarla a un gabinete; al estar cerca de las esquinas minimizan flexión y evitan que la vibración del buzzer se transmita de forma molesta. Las huellas de resistencias y capacitores están en 1206 (según tu librería), fáciles de soldar a mano.