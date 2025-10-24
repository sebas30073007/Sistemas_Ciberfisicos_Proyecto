---
title: Estructura del Gabinete
layout: default
parent: Gabinete Robot
nav_order: 3
redirect_from:
  - /estructura/chasis-y-locomocion/
---

# Estructura del Gabinete — Dimensiones y Configuración

El gabinete se diseñó a partir de una estructura preexistente del laboratorio, que emplea el **Sistema 8 de perfiles de aluminio de 40×40 mm** para garantizar rigidez y modularidad. Su diseño es diferente a la iteración CAD inicial debido a ajustes en materiales y funcionalidad.

---

## 1) Dimensiones Generales del Bastidor

Las dimensiones base del bastidor principal son:
* **Ancho (Eje X):** 1000 mm
* **Fondo/Profundidad (Eje Y):** 620 mm
* **Altura (Eje Z), sin ruedas:** $\approx$ 700 mm (Medida a confirmar y ajustar)

### Estructura Superior Desmontable
Se ha añadido una estructura superior desmontable para facilitar el transporte a través de zonas pequeñas. Esta se conforma por **cuatro perfiles verticales de 1200 mm** en las esquinas, unidos por perfiles horizontales de **540 mm (Eje Y)** y **920 mm (Eje X)** en la parte superior.

---

## 2) Distribución de Componentes Principales

### A. Montaje del Robot UR3
El brazo robótico **UR3** se ubica en el centro del eje X y alineado al borde superior del eje Y (Y=0 cm en el modelo si se toma la parte frontal como positiva).
* **Posición X:** 500 mm (Centro del ancho).
* **Posición Y:** Borde superior de la estructura.
* **Placa de Montaje:** Base metálica de $120 \times 120 \text{ mm}$.
* **Soporte:** Se apoya sobre dos perfiles de mayor grosor que el estándar 40x40.

### B. Módulo de Clasificación de Materiales
En la parte posterior de la estructura (eje Y negativo, detrás del UR3), se incorporó un módulo para la clasificación.
* **Soporte de Botes:** Se agregaron dos perfiles de 300 mm de profundidad en las esquinas (Eje Y negativo) y se cerró la geometría con un perfil de 920 mm (Eje X), creando una zona para los tres botes de reciclaje (**TetraPak, Vidrio y Latas**).
* **Refuerzo Estructural:** En esta zona se instalaron **dos perfiles de 300 mm en ángulo de $45^\circ$** para aumentar la rigidez de la estructura al recibir la carga de la parte superior.

---

## 3) Elementos de Interfaz y Acceso

### A. Zona de Depósito y Compuerta
* **Ubicación:** Eje X, desde 40 mm hasta 300 mm (para librar el perfil).
* **Mecanismo de Compuerta:** Accionamiento de una puerta deslizable de apertura y cierre basado en un sistema de **banda y rueda V-slot 40x40** impulsado por un motor, probablemente en disposición horizontal sobre el eje X.

### B. Panel de Visualización (HMI y TV)
* **HMI (7 Pulgadas):** Se montará un panel táctil de 7 pulgadas. Las opciones de montaje son:
    1. Proyección fuera de la estructura en el eje Y.
    2. Montaje usando dos perfiles adicionales (400 mm y 300 mm de longitud) alineados con la profundidad (Eje Y) y adyacentes al perfil vertical de 1200 mm, en el borde opuesto al módulo de clasificación.
* **Pantalla Informativa:** Se instalará una **pantalla de 50 pulgadas en orientación vertical** en el **lateral derecho** (Eje X, 1000 mm).

### C. Paneles Internos y Revestimiento
* **Separador Central:** Una placa interna (posiblemente de madera) recubierta con vinil negro, ubicada al centro de la estructura.
* **Recubrimiento:**
    * **Acrílico de 3 mm:** Caras **frontal, lateral izquierda** y la parte **trasera superior** (solo la zona de los perfiles de 1200 mm).
    * **Láminas de Acero (aprox. 1 mm):** Parte **trasera inferior, lateral derecha** completa y la **parte superior** de la estructura.

### D. Acceso de Mantenimiento (Volumen para Electrónica)
* **Ubicación:** En la parte posterior del gabinete (Eje Y negativo), para acceder a los componentes eléctricos (fuentes, controladores, protecciones).
* **Diseño de la Puerta:** Se contempla una gran abertura para facilitar la visibilidad y el acceso. Se mantendrá un margen de **50 mm** desde la base para definir el corte de la puerta de mantenimiento.