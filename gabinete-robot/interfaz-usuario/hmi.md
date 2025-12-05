---
title: Interfaz HMI
layout: default
parent: Interfaz Usuario
nav_order: 2
---

## Vistas de la Interfaz

A continuación se presenta el flujo de pantallas  del entorno gráfico desarrollado en **Tkinter** para la Raspberry Pi. Cada ventana está diseñada con imágenes de fondo y botones personalizados, asegurando una experiencia intuitiva para el usuario.

![Flujo de pantalla]({{ "/assets/img/flujo.png" | relative_url }})

---

## Flujo general del programa

Al seleccionar el botón de **Inicio sesión** desemboca en el escaneo de la tarjeta como se muestra en la **Pantalla 2 - Escaneo de Tarjeta**. Se hace el escaneo para obtener el nombre y puntaje de este usuario verificando si coincide con alguna ID de tarjetas en la base de datos. En la **Pantalla 8 – Inicio de sesión** se muestra el puntaje que lleva hasta ahora el usuario y se muestra el botón de **Cargar objeto**. Posterior a un exitoso inicio de sesión si se dio clic en botón de **Cargar objeto** se despliega la **Pantalla 9 - Cargar Objeto** que simplemente se carga el objeto a reciclar y al haber inciiado sesión anteriormente se abonan los puntos de la cantidad de objetos cargados.

Después se encuentra el botón de **Crear cuenta** este igualmente requiere el escaneo de la tarjeta como se muestra en la **Pantalla 3 - Escaneo de Tarjeta** para empezar el registro de un nuevo usuario en la base de datos. La siguiente pantalla es **Pantalla 4 – Crear cuenta** que solicita el nombre del nuevo usuario, en la **Pantalla 5 – Crear cuenta** aparece un Pop Up que avisa al usuario de la captura de una foto, al obtener la foto del usuario se muestra la **Pantalla 6 – Crear cuenta** que avisa si el usuario fue registrado con éxito. Al completarse se dirige de nuevo a la Pantalla Inicial la **Pantalla 1 – Bienvenida** donde debe el usuario ahora ejecutar un inicio de sesión como fue descrito anteriormente.

Por ultimo el botón de **Reciclar si cuenta** siemplemente dirige al usuario a la **Pantalla 9 - Cargar Objeto**.

---



1. **Pantalla de Bienvenida:**  
   El usuario selecciona si desea **iniciar sesión**, **crear una cuenta nueva** o **reciclar sin cuenta**.  Esta ultima opcion es por si el usuario no dispone de una tarjeta RFID aunque al seleccionar esta opción el usuario no dispondrá de un record de puntos.

2. **Lectura de Tarjeta RFID:**  
   Al acercar una tarjeta al lector **RC522**, el sistema obtiene su **ID único**.  
   Una vez leído el ID, el flujo continúa automáticamente:
   - Si se seleccionó “Iniciar sesión” → pasa a la pantalla de login.
   - Si se seleccionó “Crear cuenta” → pasa a la pantalla para ingresar nombre.
   - Si se seleccionó “Reciclar sin cuenta” → pasa a la pantalla cargar un objeto para reciclar.

3. **Registro de nuevo usuario:**  
   En la pantalla de registro, el usuario ingresa su nombre y se muestra un popup de **“Tomar Foto”** (simulado).
   Al confirmar, el sistema guarda el nombre y el id en un archivo `usuarios.txt` y envía los datos por **JSON** al servidor configurado (ej. `172.22.22.128`), con el siguiente formato:

   ```json
   {
     "rfid": "ID_de_la_tarjeta",
     "usuario": "Nombre_ingresado"
   }

4. **Código completo de Interfaz**
   [📁 Ver código completo de la interfaz](https://github.com/sebas30073007/Sistemas_Ciberfisicos_Proyecto/blob/main/assets/documentos/codigo.py)
