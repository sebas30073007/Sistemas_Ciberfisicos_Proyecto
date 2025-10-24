---
title: Cámara
layout: default
parent: Robot
---

# Entrenamiento del modelo de visión

Esta sección documenta el proceso de **entrenamiento de la red neuronal** utilizada para clasificar tres tipos de residuos: **vidrio, lata y Tetra Pak**, junto con una categoría adicional denominada **“BG”** (otros objetos o fondo).  
El modelo fue desarrollado mediante **[Teachable Machine](https://teachablemachine.withgoogle.com/)**, una herramienta accesible para la creación rápida de modelos de visión por computadora.

---

## 1. Captura de imágenes (Dataset)

Para entrenar la red se creó un conjunto de imágenes de ejemplo (dataset) que representara distintos escenarios reales de iluminación, ángulo y posición.

- **Vidrio:** 49 muestras tomadas con diferentes orientaciones de una botella transparente.  
- **Lata:** 83 muestras de latas de distintos colores y posiciones (de frente, lateral, vista superior).  
- **Tetra Pak:** 79 muestras con diferentes niveles de llenado y desgaste.  
- **Background:** 10 imágenes sin objetos de interés o con elementos irrelevantes, para ayudar al modelo a diferenciar el fondo.

Cada categoría se capturó con fondo oscuro y condiciones controladas para reducir errores de clasificación.  

---

## 2. Entrenamiento del modelo

Una vez cargadas las imágenes, se seleccionó la opción **“Entrenar modelo”** con la configuración predeterminada de Teachable Machine.  
El proceso fue rápido (unos segundos), generando una red neuronal ligera basada en **TensorFlow -> Keras**, adecuada para integrarse en el sistema embebido del robot.

El modelo aprendió a distinguir los patrones visuales característicos de cada clase (forma, textura, color dominante).  
El entrenamiento se validó en tiempo real mediante la cámara del sistema, observando el nivel de confianza para cada predicción.

---

## 3. Evaluación y resultados

Durante las pruebas, el modelo mostró resultados satisfactorios:

- **Vidrio:** alta precisión gracias a su forma y brillo característicos.  
- **Lata:** buena clasificación incluso con diferentes colores.  
- **Tetra Pak:** correcta en la mayoría de los casos.  
- **Background:** redujo falsos positivos, evitando clasificar objetos ajenos al sistema.

El sistema devuelve como salida la clase con mayor porcentaje de relación.

![Entrenamiento del modelo]({{ "/assets/img/Entrenamiento.png" | relative_url }})


---

## 4. Exportación e integración

Finalmente, el modelo fue exportado desde Teachable Machine en formato **TensorFlow Lite** para poder ejecutarse localmente en el entorno **Python / Raspberry Pi**. 

---

## Descarga del modelo

Puedes descargar el paquete del modelo (pesos y configuración) aquí:

[Descargar modelo entrenado]( {{ "/assets/documentos/vision_model.zip" | relative_url }} ){: .btn .btn-primary }

---
