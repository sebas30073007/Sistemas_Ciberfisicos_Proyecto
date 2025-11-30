---
title: Conexiones industriales y de potencia
layout: default
parent: Conexiones eléctricas y red de comunicaciones
nav_order: 1
---

## 1. Conexiones industriales y de potencia

Esta parte describe lo que ocurre “del gabinete hacia afuera”: alimentación, seguridad y actuadores.

### 1.1 Relé Finder de enclavamiento y distribución de cargas

En la figura del **relé Finder** se muestran los contactos numerados (1–3-4, 5-6-7, 8-9-11) y la bobina (2–10).

- **Bobina (2–10):**  
  Se alimenta con 24 V DC (a través de la botonera) y regresa a 0 V.  
  Cuando la bobina se energiza, los tres contactos internos del relé cambian de estado.

- **Contacto 1–4 – Multicontacto UR3 + gripper**  
  - L (línea de 120 V AC) entra por el borne **1**.  
  - Sale por el borne **4** hacia el multicontacto donde se alimentan el **UR3** y el **gripper**.  
  - Si el relé cae, se desenergiza todo el multicontacto.

- **Contacto 6–5 – Driver del motor a pasos**  
  - +24 V entra al borne **6**.  
  - Sale por el borne **5** hacia la alimentación del **driver del motor a pasos**.  
  - Esto permite que, ante una parada de emergencia, el driver quede sin energía.

- **Contacto 11–8–9 – Señal de enclavamiento**  
  - Se utiliza como contacto auxiliar para crear el **autoretenido** con la botonera.  
  - El cierre 11–9 mantiene energizada la bobina aunque se suelte el pulsador de marcha.  
  - Opcionalmente, el estado puede llevarse como entrada al PLC para saber si el sistema está habilitado.

En resumen, este relé separa claramente la **lógica de mando (24 V DC)** de las **cargas de potencia (120 V AC y 24 V del driver)** y las pone bajo el mismo circuito de seguridad.

![Relé]({{ "/assets/img/energy_conex.jpg" | relative_url }})

---

### 1.2 PLC Siemens S7-1200: alimentación y salidas

En la imagen del **PLC S7-1200** se marcan:

- **Alimentación superior:**  
  - Borne de **+24 V**.  
  - Borne de **0 V**.  
  Estos alimentan internamente la CPU y sirven como referencia para entradas/salidas DC.

- **Puerto Ethernet frontal:**  
  - Se usa para la **comunicación TCP/IP** con la Jetson Nano y para la programación desde TIA Portal.

- **Salidas digitales hacia el driver del motor a pasos:**  
  - Dos salidas del banco **Q0.x** del PLC se cablean a:
    - Señal **PUL** (pulso) del driver.  
    - Señal **DIR** (dirección) del driver.  
  - La imagen indica también el retorno de **0 V** compartido con el driver, y la alimentación adicional de **+24 V** que requiere el mismo.

El PLC se encarga de generar los pulsos para el **motor a pasos de la puerta**, recibiendo órdenes desde la Jetson Nano.

![Relé]({{ "/assets/img/plc_conex.jpg" | relative_url }})

---

### 1.3 Botonera de arranque/parada y paro de emergencia

La botonera frontal tiene tres elementos principales:

- **Paro de emergencia (rojo de seta):** contacto **NC** (normalmente cerrado).  
- **Botón STOP (rojo):** contacto NC.  
- **Botón START (verde):** contacto NO (normalmente abierto).

En el esquema se ve:

1. **+24 V** entra por el contacto NC del **paro de emergencia**.  
2. Pasa por el contacto NC del botón **STOP**.  
3. Llega al contacto NO del botón **START**.  
4. Desde el START se envía la señal al borne **11** del relé Finder.  
5. El contacto 11–9 del propio relé se usa como **autoretenido**: cuando el relé se energiza, 11–9 cierra y se hace un puente en paralelo con el contacto START, manteniendo la bobina energizada.  
6. La bobina regresa a **0 V** por los bornes 2–10.

De esta forma:

- Si se pulsa el **paro de emergencia** o el botón **STOP**, se desenergiza el relé Finder y se corta energía al UR3, gripper y driver.  
- El botón **START** vuelve a armar el sistema cuando todas las condiciones de seguridad se cumplen.

![Relé]({{ "/assets/img/start_conex.jpg" | relative_url }})

---

### 1.4 Driver del motor a pasos y motor

En la imagen del **driver Microstep** se observan las siguientes conexiones:

- **Alimentación de potencia del driver:**  
  - Bornes **VCC / GND**: conectados a **+24 V** y **0 V** provenientes de la fuente y conmutados por el relé Finder.

- **Salidas hacia el motor a pasos:**  
  - Bornes **A+ / A−** y **B+ / B−**, conectados a las dos bobinas del motor.  
  - El código de colores del motor (rojo, azul, verde, negro) se asigna según la hoja de datos.

- **Entradas de señal desde el PLC:**  
  - **PUL+ / PUL−**: señal de pulsos para los pasos.  
  - **DIR+ / DIR−**: indican el sentido de giro.  
  - Opcionalmente **ENA+ / ENA−** si se usa la entrada de habilitación.

En el gabinete se definió:

- **PUL+ y DIR+** conectados a salidas digitales del PLC (24 V).  
- **PUL− y DIR−** conectados a **0 V** común.  

Los **DIP switches** del driver se ajustan para definir:

- Corriente máxima del motor.  
- Resolución de micro-paso (por ejemplo, 1/8, 1/16, etc.).

![Relé]({{ "/assets/img/driver_conex.jpg" | relative_url }})
