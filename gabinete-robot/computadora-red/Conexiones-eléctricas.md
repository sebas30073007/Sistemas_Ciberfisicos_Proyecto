---
title: Conexiones industriales y de potencia
layout: default
parent: Conexiones eléctricas y red de comunicaciones
nav_order: 1
---

## 1. Conexiones industriales y de potencia
![Diagrama general]({{ "/assets/img/Diagrama-electrico.jpg" | relative_url }})

Esta sección describe lo que ocurre “del gabinete hacia afuera”: alimentación, seguridad y actuadores.

---

### 1.1 Relé y distribución de cargas

![Relé]({{ "/assets/img/energy_conex.jpg" | relative_url }})

En la figura del se muestran los contactos numerados (1–3-4, 5-6-7, 8-9-11) y la bobina (2–10).

- **Bobina (2–10):**  
  Se alimenta con 24 V DC (a través de la botonera) y regresa a 0 V.  
    Cuando la bobina se energiza, los tres contactos internos del relé cambian de estado.

    - **Contacto 1–3 – Multicontacto con UR3 + gripper**  
      - L (línea de 120 V AC) entra por el borne **1**.  
        - Sale por el borne **3** hacia el multicontacto donde se alimentan el **UR3** y el **gripper**.  
          - Si el relé cae, se desenergiza todo el multicontacto.

          - **Contacto 6–7 – Driver del motor a pasos**  
            - +24 V entra al borne **6**.  
              - Sale por el borne **7** hacia la alimentación del **driver del motor a pasos**.  
                - Esto permite que, ante una parada de emergencia, el driver quede sin energía.

                - **Contacto 11–9 – Señal de enclavamiento**  
                  - Se utiliza como contacto auxiliar para crear el **enclavamiento** con la botonera.  
                    - El cierre 11–9 mantiene energizada la bobina aunque se suelte el pulsador de marcha.

                    En resumen, este relé separa claramente la **lógica de mando (24v DC)** de las **cargas de potencia (120v AC y 24v del driver)** y las pone bajo el mismo circuito de seguridad.

                    ---

                    ### 1.2 PLC Siemens S7-1215c: alimentación y salidas

                    ![Relé]({{ "/assets/img/plc_conex.jpg" | relative_url }})

                    En la imagen del **PLC S7-1215c** se marcan:

                    - **Alimentación superior:**  
                      - Borne de **+24 V**.  
                        - Borne de **0 V**.  
                          Estos alimentan internamente la CPU y sirven como referencia para entradas/salidas DC.

                          - **Puerto Ethernet frontal:**  
                            - Se usa para la **comunicación TCP/IP** con la Jetson Nano y para la programación desde TIA Portal.

                            - **Salidas digitales hacia el driver del motor a pasos:**  
                              - Dos salidas del banco **Q0.x** del PLC se cablean a:
                                  - Señal Q0.0 **PUL** (pulso) del driver.  
                                      - Señal Q0.1 **DIR** (dirección) del driver. 

                                      El PLC se encarga de generar los pulsos para el **motor a pasos de la puerta**, recibiendo órdenes desde la Jetson Nano.

                                      ---

                                      ### 1.3 Botonera de arranque/parada y paro de emergencia

                                      ![Relé]({{ "/assets/img/start_conex.jpg" | relative_url }})

                                      La botonera frontal tiene tres elementos principales:

                                      - **Paro de emergencia:** contacto **NC** (normalmente cerrado).  
                                      - **Botón STOP:** contacto NC.  
                                      - **Botón START:** contacto NO (normalmente abierto).

                                      En el esquema se ve:

                                      1. **+24 V** entra por el contacto NC del **paro de emergencia**.  
                                      2. Pasa por el contacto NC del botón **STOP**.  
                                      3. Llega al contacto NO del botón **START** (que esta en paralelo con un contactor NO del relé).  
                                      4. Desde el START se envía la señal al borne **2** del relé.  
                                      5. El contacto 11–9 del propio relé se usa como **autoretenido**: cuando el relé se energiza, 11–9 cierra y se hace un puente en paralelo con el contacto START, manteniendo la bobina energizada.  
                                      6. La bobina regresa a **0 V** por el borne 10.

                                      De esta forma:

                                      - Si se pulsa el **paro de emergencia** o el botón **STOP**, se desenergiza el relé Finder y se corta energía al UR3, gripper y driver.  
                                      - El botón **START** vuelve a armar el sistema cuando todas las condiciones de seguridad se cumplen.

                                      ---

                                      ### 1.4 Driver del motor a pasos y motor

                                      ![Relé]({{ "/assets/img/driver_conex.jpg" | relative_url }})

                                      En la imagen se observan las siguientes conexiones:

                                      - **Alimentación de potencia del driver:**  
                                        - Bornes **VCC / GND**: conectados a **+24 V** y **0 V** provenientes de la fuente y conmutados por el relé.

                                        - **Salidas hacia el motor a pasos:**  
                                          - Bornes **A+ / A−** y **B+ / B−**, conectados a las dos bobinas del stepper motor.  
                                            - El código de colores del motor (rojo, azul, verde, negro) se asigna según la hoja de datos.

                                            - **Entradas de señal desde el PLC:**  
                                              - **PUL−**: señal de pulsos para los pasos.  
                                                - **DIR−**: indican el sentido de giro.

                                                En el gabinete se definió:

                                                - **PUL+ y DIR+** conectados a 24 V.  
                                                - **PUL− y DIR−** conectados a salidas digitales del PLC. 

                                                Los **DIP switches** del driver se ajustan para definir:

                                                - Corriente máxima del motor (1.5A - 1.7A).  
                                                - Resolución de micro-paso (200 pulso/rev).

                                                
