---
title: Arquitectura general
layout: default
parent: Gabinete Robot
nav_order: 1
has_children: true
---

# Estructura del Gabinete — Dimensiones y Configuración

El gabinete se diseñó a partir de una estructura preexistente del laboratorio, que emplea el **perfiles de aluminio de 40×40 mm** para garantizar rigidez y modularidad.

---

## 1) Dimensiones Generales

Las dimensiones base de la estructura principal son:
* **Ancho (Eje X):** 1000 mm
* **Fondo/Profundidad (Eje Y):** 920 mm
* **Altura (Eje Z):** 2100 mm

![Dimenciones]({{ "/assets/img/full-dimenciones.png" | relative_url }})

---

## 2) Distribución de Componentes Principales

### A. Montaje del Robot UR3
* **Posición X:** 500 mm (Centro del ancho).
* **Posición Y:** Borde superior de la estructura.

![Dimenciones UR3]({{ "/assets/img/ur3_dimenciones.jpg" | relative_url }})

### B. Módulo de Clasificación de Materiales
En la parte posterior de la estructura (detrás del UR3), se incorporaron 3 contenedores para la clasificación.
* **Soporte de Botes:** Dos perfiles de 300 mm de profundidad y se cerró la geometría con un perfil de 920 mm (Eje X), creando una zona para los tres botes de reciclaje.
* **Refuerzo Estructural 1:** En esta zona se instalaron **dos perfiles de 300 mm en ángulo de $45^\circ$** para aumentar la rigidez de la estructura al recibir la carga de la parte superior.

![Dimenciones UR3]({{ "/assets/img/botes.jpg" | relative_url }})

### C. Módulo de Pantalla 
En la parte posterior y arriba de los botes, se instalo una pantalla de 50", para lo que fueron necesarios 2 soleras de soporte y añadir aun más refuersos a la estructura.
* **Solera TV:** Dos soleras de 1000 mm con barrenos centrados y distanciados por 440 mm. 
* **Refuerzo Estructural 2:** En la zona de los bots, se agregaron 2 patas que terminan en llantas para dar rigidez al sistema.

![Dimenciones UR3]({{ "/assets/img/soportes.jpg" | relative_url }})
---

## 3) Elementos de Interfaz y Acceso

### A. Zona de Depósito y Compuerta
* **Compuerta:** abertura de 170 mm X 330 mm.
* **Mecanismo de Compuerta:** Accionamiento de una puerta deslizable de apertura y cierre basado en un sistema de **banda y rueda V-slot 40x40** impulsado por un motor a pasos, en disposición horizontal.

![Dimenciones UR3]({{ "/assets/img/puerta.jpg" | relative_url }})

### B. Panel de Visualización (HMI y TV)
* **HMI (7 Pulgadas):** 
    1. Montada fuera de la estructura en el eje Y.
    2. Montaje usando piezas impresas en PLA y cortadas de acrilico para proporcionar una inclinación a -45° y sea comodo para los usuarios.

![Dimenciones UR3]({{ "/assets/img/UI.jpg" | relative_url }})

### C. Paneles Internos y Revestimiento
* **Separador Central:** Una placa interna de acrilico recubierta con vinil negro, ubicada al centro de la estructura.
* **Recubrimiento:**
    * **Acrílico de 3 mm:** Cara **frontal**.
    * **Láminas de PVC:** Parte **Fronal inferior**.

### D. Panel elctrico
* **Ubicación:** En la parte frontal inferior del gabinete
* **Diseño:** Se contempla una abertura para facilitar la visibilidad y el acceso.