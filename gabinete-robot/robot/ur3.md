---
title: UR3
layout: default
parent: Modulo Robotico
has_children: true
---

![Teach Pendant del UR3 con secuencia de recepción]({{ "/assets/img/teachPendant.jpg" | relative_url }})

El UR3 no ejecuta un único programa monolítico, sino un **conjunto de scripts especializados** que se llaman según el tipo de residuo detectado. En el teach pendant se encuentran precargadas, entre otras, las siguientes rutinas:

- `rutObservacion` – mueve al robot a una postura de observación para ver el objeto sobre la bandeja.
- `rutRecoleccionLata`, `rutRecoleccionTetra`, `rutRecoleccionVidrio` – trayectorias para tomar el objeto identificado como lata, tetrapak o vidrio.
- `rutLata`, `rutTetra`, `rutVid` – trayectorias de depósito para colocar cada tipo de residuo en su contenedor correspondiente.

La lógica general es:

1. El UR3 ejecuta `rutObservacion` y se coloca en la posición desde la cual el sistema de visión puede observar el objeto.
2. Un script externo en Python realiza una petición HTTP a la **Raspberry Pi**, que corre el modelo de visión y calcula la **moda de varias predicciones**.
3. Con base en la etiqueta recibida (`"lata"`, `"tetra"`, `"vidrio"` o `"bg"`), el sistema selecciona qué script de recolección y depósito ejecutar en el UR3.

El código que realiza la consulta al servidor de visión tiene la siguiente forma:

{% raw %}
~~~python
import requests

VISION_URL = "http://192.168.1.12:5000/identify"

resp = requests.get(VISION_URL, timeout=10)
resp.raise_for_status()

data = resp.json()
print("Respuesta de visión:", data)
print("Objeto detectado:", data.get("object"))
~~~
{% endraw %}

El servidor devuelve un JSON del estilo:

{% raw %}
~~~json
{ "object": "lata" }
~~~
{% endraw %}

donde `"object"` puede ser `"lata"`, `"tetra"`, `"vidrio"` o `"bg"` (background, sin objeto válido).  
Finalmente, según este resultado, se dispara en el UR3 la combinación adecuada de:

- rutina de **recolección** (`rutRecoleccionLata`, `rutRecoleccionTetra`, `rutRecoleccionVidrio`), y  
- rutina de **depósito** (`rutLata`, `rutTetra`, `rutVid`),

dejando toda la **cinemática y trayectorias** encapsuladas en los scripts del UR3, mientras la selección de qué rutina usar se decide externamente a partir del modelo de visión.

