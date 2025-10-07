---
title: Interfaz HMI
layout: default
parent: Interfaz Usuario
nav_order: 2
---

## Vistas de la Interfaz

A continuación se presentan las pantallas principales del entorno gráfico desarrollado en **Tkinter** para la Raspberry Pi.  
Cada ventana está diseñada con imágenes de fondo y botones personalizados, asegurando una experiencia intuitiva para el usuario.

> 🔸 Sustituye los nombres de las imágenes según tus archivos reales en la carpeta `assets/img/`.

### Pantalla 1 – Bienvenida  
![Vista de pantalla de bienvenida]({{ "/assets/img/HMI_bienvenida.jpg" | relative_url }})

### Pantalla 2 – Escaneo de Tarjeta (Inicio de sesión)  
![Vista de pantalla de escaneo de tarjeta para iniciar sesión]({{ "/assets/img/HMI_escanear_inicio.jpg" | relative_url }})

### Pantalla 3 – Escaneo de Tarjeta (Crear cuenta)  
![Vista de pantalla de escaneo de tarjeta para crear cuenta]({{ "/assets/img/HMI_escanear_crear.jpg" | relative_url }})

### Pantalla 4 – Crear cuenta (Ingreso de nombre y foto)  
![Vista de pantalla para crear cuenta]({{ "/assets/img/HMI_crear_cuenta.jpg" | relative_url }})

### Pantalla 5 – Inicio de sesión exitoso  
![Vista de pantalla de sesión iniciada]({{ "/assets/img/HMI_inicio_sesion.jpg" | relative_url }})

### Pantalla 6 – Cargar objeto  
![Vista de pantalla de carga de objeto]({{ "/assets/img/HMI_cargar_objeto.jpg" | relative_url }})

---

## Descripción general del sistema HMI

Esta interfaz gráfica actúa como el **puente entre el usuario y el sistema embebido**.  
Su propósito principal es permitir que los usuarios se registren o inicien sesión mediante una **tarjeta RFID**, y posteriormente interactúen con las funciones disponibles (como carga de objetos o consulta de puntos).

El HMI fue desarrollado en **Python 3**, utilizando las siguientes bibliotecas:
- `tkinter` → creación de ventanas, botones y eventos.
- `PIL (ImageTk)` → manejo y escalado de imágenes.
- `requests` → envío de datos JSON al servidor (para la comunicación con backend).
- `mfrc522` → lectura del identificador RFID.

---

## Flujo general del programa

1. **Pantalla de Bienvenida:**  
   El usuario selecciona si desea **iniciar sesión** o **crear una cuenta nueva**.  

2. **Lectura de Tarjeta RFID:**  
   Al acercar una tarjeta al lector **RC522**, el sistema obtiene su **ID único**.  
   Una vez leído el ID, el flujo continúa automáticamente:
   - Si se seleccionó “Iniciar sesión” → pasa a la pantalla de login.
   - Si se seleccionó “Crear cuenta” → pasa a la pantalla para ingresar nombre.

3. **Registro de nuevo usuario:**  
   En la pantalla de registro, el usuario ingresa su nombre y se muestra un popup de **“Tomar Foto”** (simulado).  
   Al confirmar, el sistema guarda el nombre en un archivo `usuarios.txt` y envía los datos por **JSON** al servidor configurado (ej. `172.22.22.128`), con el siguiente formato:

   ```json
   {
     "rfid": "ID_de_la_tarjeta",
     "usuario": "Nombre_ingresado"
   }
