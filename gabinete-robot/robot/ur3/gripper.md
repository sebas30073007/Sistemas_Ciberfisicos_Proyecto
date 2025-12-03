---
title: Gripper
layout: default
parent: UR3
---
# OnRobot SG Soft Gripper

Para la manipulación de los residuos (latas, tetrapak y vidrio) en este proyecto, se implementó un **Soft Gripper (SG)** de la marca OnRobot. Este actuador flexible es ideal para la manipulación de objetos con geometrías variables o superficies frágiles.

![Gripper OnRobot SG]({{ "/assets/img/onrobot_gripper.jpg" | relative_url }})

## Conexión Física (Hardware)

El sistema utiliza la **OnRobot Compute Box** (conocida comúnmente como "EyeBox" en este setup) para gestionar la comunicación y control del actuador. La topología de conexión es la siguiente:

1.  **Gripper al Compute Box:** El gripper se conecta mediante un cable de 8 pines (conector **M8 de 8 polos**) al puerto de entrada en la Compute Box etiquetado como *Device*.
2.  **Comunicación (Ethernet):** Se utiliza un cable Ethernet para conectar la Compute Box directamente al switch dentro del gabinete de control del UR3, estableciendo la comunicación TCP/IP necesaria.
3.  **Alimentación:** La Compute Box se conecta a la corriente alterna mediante su fuente de poder externa.

> **Estado del sistema:** Para operar, es indispensable verificar que los LEDs indicadores en la Compute Box (tanto el de *Robot* como el de *Power*) se encuentren en color **verde** fijo.

## Configuración en PolyScope

Una vez realizadas las conexiones físicas, el dispositivo se da de alta en la interfaz del UR3:

1.  Ir a la pestaña **Instalación** $\rightarrow$ **Configuración de OnRobot**.
2.  Seleccionar el submenú **Información del dispositivo**.
3.  Elegir **SG Soft Gripper** de la lista.
4.  Presionar el botón para habilitar el control desde el robot.

## Programación y Comandos

Para integrar el gripper en los scripts de reciclaje del UR3 (como `rutRecoleccionLata` o `rutLata`), utilizamos comandos de script directos en lugar de los nodos gráficos estándar, lo que permite una ejecución más fluida dentro del código lógico.

El comando identificado y utilizado es `sg_grip`.

### Sintaxis del comando

```python
sg_grip(width, force, ???, grip_detect, ???)

En la práctica, utilizamos la siguiente configuración para las acciones de abrir y cerrar:

Cerrar (Agarre): sg_grip(30, False, 0, True, False)

El valor 30 indica una anchura cerrada (apriete).

Abrir (Soltar): sg_grip(75, False, 0, True, False)

El valor 75 indica la anchura de apertura para soltar el objeto, como se observa en el script de depositar.
